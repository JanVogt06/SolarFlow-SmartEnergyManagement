"""
Energie-Steuerung für den Smart Energy Manager.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

from .device import Device, DeviceState
from .device_manager import DeviceManager
from .interfaces import ISmartDeviceInterface


class EnergyController:
    """Steuert Geräte basierend auf verfügbarer Energie"""

    def __init__(self, device_manager: DeviceManager,
                 device_interface: Optional[ISmartDeviceInterface] = None) -> None:
        """
        Initialisiert den EnergyController.

        Args:
            device_manager: Verwaltung der Geräte
            device_interface: Interface für Hardware-Steuerung (optional)
        """
        self.device_manager = device_manager
        self.device_interface = device_interface
        self.logger = logging.getLogger(__name__)

        # Hysterese-Zeitspanne (verhindert zu häufiges Schalten)
        self.hysteresis_time: timedelta = timedelta(minutes=5)

        # Tracking für kürzlich geschaltete Geräte (verhindert falsche Sync-Erkennung)
        # Format: {device_name: datetime_of_last_switch}
        self._recent_switches: Dict[str, datetime] = {}
        self._switch_settle_time: timedelta = timedelta(seconds=15)

    def update(self, surplus_power: float, current_time: Optional[datetime] = None) -> Dict[str, str]:
        """
        Aktualisiert Gerätezustände basierend auf verfügbarem Überschuss.

        Args:
            surplus_power: Verfügbarer Überschuss in Watt (kann negativ sein!)
            current_time: Aktuelle Zeit (optional, für Tests)

        Returns:
            Dict mit Statusänderungen {Gerätename: Aktion}
        """
        if current_time is None:
            current_time = datetime.now()

        changes: Dict[str, str] = {}

        # Synchronisiere Gerätestatus mit Hardware (falls manuell geschaltet wurde)
        self._sync_device_states(current_time)

        # Sortiere Geräte nach Priorität (niedrigere Zahl = höhere Priorität)
        devices = self.device_manager.get_devices_by_priority()

        # Berechne aktuellen Verbrauch der gesteuerten Geräte
        current_consumption = self.device_manager.get_total_consumption()

        # Die verfügbare Leistung für neue Geräte ist der aktuelle Überschuss
        # plus die Leistung, die wir durch Abschalten von Geräten freigeben könnten
        total_available = surplus_power + current_consumption

        self.logger.debug(f"Überschuss: {surplus_power}W, Gesteuerter Verbrauch: {current_consumption}W, "
                          f"Total verfügbar: {total_available}W")

        # Schritt 1: Prüfe welche Geräte ausgeschaltet werden müssen (zu wenig Überschuss)
        for device in devices:
            if device.state == DeviceState.ON:
                # Gerät läuft - prüfe ob ausschalten
                # WICHTIG: Der effektive Überschuss für dieses Gerät ist der aktuelle Überschuss (= Einspeisung)
                # PLUS der eigene Verbrauch des Geräts, da dieses bereits in der reduzierten Einspeisung enthalten ist.
                # Beispiel: 3242W Einspeisung vor Einschalten, Gerät 2000W → Einspeisung sinkt auf ~1242W
                # Für die Ausschalt-Entscheidung muss aber der ursprüngliche Überschuss (3242W) betrachtet werden.
                effective_surplus = surplus_power + device.power_consumption

                if effective_surplus < device.switch_off_threshold:
                    # Prüfe Mindestlaufzeit
                    if self._check_min_runtime(device, current_time):
                        action = self._switch_off(device, current_time,
                                                f"Überschuss ({effective_surplus:.1f}W) < Schwellwert ({device.switch_off_threshold}W)")
                        if action:
                            changes[device.name] = action
                            # Aktualisiere verfügbare Leistung nach Abschaltung
                            surplus_power += device.power_consumption
                            total_available = surplus_power + self.device_manager.get_total_consumption()

        # Schritt 2: Prüfe ob höher priorisierte Geräte eingeschaltet werden können
        # indem niedriger priorisierte ausgeschaltet werden
        changes.update(self._handle_priority_preemption(devices, total_available, current_time))

        # Aktualisiere total_available nach möglichen Änderungen
        current_consumption = self.device_manager.get_total_consumption()
        total_available = surplus_power + current_consumption

        # Schritt 3: Prüfe welche Geräte eingeschaltet werden können
        available_for_new = total_available
        for device in devices:
            action = self._process_device_for_switching_on(device, available_for_new, current_time)

            if action:
                changes[device.name] = action
                # Aktualisiere verfügbare Leistung nach Einschaltung
                if "eingeschaltet" in action and device.state == DeviceState.ON:
                    available_for_new -= device.power_consumption

        return changes

    def _sync_device_states(self, current_time: datetime) -> None:
        """
        Synchronisiert den internen Gerätestatus mit dem tatsächlichen Hardware-Status.

        Dies ist wichtig, falls Geräte manuell (z.B. über die Hue-App) geschaltet wurden.
        """
        if not self.device_interface or not self.device_interface.connected:
            return

        for device in self.device_manager.devices:
            # Nur Geräte synchronisieren, die im Hardware-Interface verfügbar sind
            if not self.device_interface.is_device_available(device.name):
                continue

            # Überspringe Geräte, die kürzlich von uns geschaltet wurden
            # (Hardware braucht Zeit zum Reagieren)
            if device.name in self._recent_switches:
                time_since_switch = current_time - self._recent_switches[device.name]
                if time_since_switch < self._switch_settle_time:
                    self.logger.debug(f"Überspringe Sync für '{device.name}' - "
                                     f"kürzlich geschaltet ({time_since_switch.total_seconds():.0f}s)")
                    continue
                else:
                    # Wartezeit abgelaufen - aus Tracking entfernen
                    del self._recent_switches[device.name]

            # Aktuellen Hardware-Status abfragen
            hw_state = self.device_interface.get_state(device.name)
            if hw_state is None:
                # Konnte Status nicht abfragen - überspringen
                continue

            # Vergleiche mit internem Status
            internal_is_on = device.state == DeviceState.ON
            hw_is_on = hw_state

            if hw_is_on and not internal_is_on:
                # Gerät wurde manuell eingeschaltet
                self.logger.info(f"Gerät '{device.name}' wurde extern eingeschaltet - synchronisiere Status")
                device.state = DeviceState.ON
                device.last_state_change = current_time

            elif not hw_is_on and internal_is_on:
                # Gerät wurde manuell ausgeschaltet
                self.logger.info(f"Gerät '{device.name}' wurde extern ausgeschaltet - synchronisiere Status")

                # Berechne Laufzeit vor Statusänderung
                if device.last_state_change:
                    runtime = int((current_time - device.last_state_change).total_seconds() / 60)
                    device.runtime_today += runtime
                    self.logger.debug(f"Gerät '{device.name}' lief {runtime} Minuten (extern ausgeschaltet)")

                device.state = DeviceState.OFF
                device.last_state_change = current_time
                device.last_switch_off = current_time

    def _handle_priority_preemption(self, devices: List[Device], total_available: float,
                                    current_time: datetime) -> Dict[str, str]:
        """
        Prüft ob höher priorisierte Geräte eingeschaltet werden können,
        indem niedriger priorisierte ausgeschaltet werden.

        Args:
            devices: Liste der Geräte sortiert nach Priorität
            total_available: Total verfügbare Leistung
            current_time: Aktuelle Zeit

        Returns:
            Dict mit Statusänderungen
        """
        changes: Dict[str, str] = {}

        for device in devices:
            # Nur ausgeschaltete Geräte betrachten, die eingeschaltet werden könnten
            if device.state not in (DeviceState.OFF, DeviceState.BLOCKED):
                continue

            # Prüfe ob Gerät grundsätzlich laufen darf (Zeit, Tageslaufzeit)
            if not device.is_time_allowed(current_time) or not device.can_run_today():
                continue

            # Prüfe Hysterese
            if not self._check_switch_on_hysteresis(device, current_time):
                continue

            # Genug Leistung vorhanden? Dann brauchen wir keine Verdrängung
            if total_available >= device.switch_on_threshold:
                continue

            # Nicht genug Leistung - prüfe ob wir durch Abschalten von
            # niedriger priorisierten Geräten genug Leistung freimachen können
            potential_power = total_available
            devices_to_preempt: List[Device] = []

            # Gehe durch alle laufenden Geräte mit niedrigerer Priorität (höhere Zahl)
            for other_device in reversed(devices):  # Von niedrigster Priorität her
                if other_device.name == device.name:
                    continue
                if other_device.state != DeviceState.ON:
                    continue
                if other_device.priority <= device.priority:
                    # Gleiche oder höhere Priorität - nicht verdrängen
                    continue

                # Prüfe Mindestlaufzeit des zu verdrängenden Geräts
                if not self._check_min_runtime(other_device, current_time):
                    continue

                # Dieses Gerät könnte verdrängt werden
                potential_power += other_device.power_consumption
                devices_to_preempt.append(other_device)

                # Genug Leistung gesammelt?
                if potential_power >= device.switch_on_threshold:
                    break

            # Können wir genug Leistung freimachen?
            if potential_power >= device.switch_on_threshold and devices_to_preempt:
                # Schalte die niedriger priorisierten Geräte aus
                for preempt_device in devices_to_preempt:
                    action = self._switch_off(
                        preempt_device, current_time,
                        f"Verdrängt durch höher priorisiertes Gerät '{device.name}'"
                    )
                    if action:
                        changes[preempt_device.name] = action
                        total_available += preempt_device.power_consumption

                # Schalte das höher priorisierte Gerät ein
                action = self._switch_on(device, current_time)
                if action:
                    changes[device.name] = action
                    total_available -= device.power_consumption

        return changes

    def _process_device_for_switching_on(self, device: Device, available_power: float,
                                        current_time: datetime) -> Optional[str]:
        """
        Prüft ob ein Gerät eingeschaltet werden kann.

        Args:
            device: Zu prüfendes Gerät
            available_power: Verfügbare Leistung in Watt
            current_time: Aktuelle Zeit

        Returns:
            Aktion oder None
        """
        # Prüfe Zeitbeschränkungen
        if not device.is_time_allowed(current_time):
            if device.state == DeviceState.ON:
                action = self._switch_off(device, current_time, "Außerhalb erlaubter Zeit")
                if action:
                    return action
            device.state = DeviceState.BLOCKED
            return None

        # Prüfe Tageslaufzeit
        if not device.can_run_today():
            if device.state == DeviceState.ON:
                return self._switch_off(device, current_time, "Maximale Tageslaufzeit erreicht")
            device.state = DeviceState.BLOCKED
            return None

        # Gerät kann grundsätzlich laufen - prüfe ob einschalten
        if device.state == DeviceState.OFF or device.state == DeviceState.BLOCKED:
            # Gerät ist aus - prüfe ob einschalten
            if available_power >= device.switch_on_threshold:
                # Prüfe Hysterese für EINSCHALTEN (basierend auf letztem Ausschalten)
                if self._check_switch_on_hysteresis(device, current_time):
                    return self._switch_on(device, current_time)

        return None

    def _switch_on(self, device: Device, current_time: datetime) -> str:
        """
        Schaltet ein Gerät ein.

        Args:
            device: Einzuschaltendes Gerät
            current_time: Aktuelle Zeit

        Returns:
            Aktionsbeschreibung
        """
        # Hardware schalten wenn Interface vorhanden
        if self.device_interface and self.device_interface.connected:
            try:
                success = self.device_interface.switch_on(device.name)
                if success:
                    self.logger.debug(f"Hardware '{device.name}' erfolgreich eingeschaltet")
                    # Merke Schaltzeit für Sync-Verzögerung
                    self._recent_switches[device.name] = current_time
                else:
                    self.logger.warning(f"Hardware '{device.name}' konnte nicht eingeschaltet werden")
            except Exception as e:
                self.logger.error(f"Fehler beim Hardware-Einschalten: {e}")

        device.state = DeviceState.ON
        device.last_state_change = current_time

        self.logger.info(f"Gerät '{device.name}' eingeschaltet "
                         f"(Leistung: {device.power_consumption}W)")

        return "eingeschaltet"

    def _switch_off(self, device: Device, current_time: datetime, reason: str = "") -> Optional[str]:
        """
        Schaltet ein Gerät aus.

        Args:
            device: Auszuschaltendes Gerät
            current_time: Aktuelle Zeit
            reason: Grund für das Ausschalten

        Returns:
            Aktionsbeschreibung
        """
        # Hardware schalten wenn Interface vorhanden
        if self.device_interface and self.device_interface.connected:
            try:
                success = self.device_interface.switch_off(device.name)
                if success:
                    self.logger.debug(f"Hardware '{device.name}' erfolgreich ausgeschaltet")
                    # Merke Schaltzeit für Sync-Verzögerung
                    self._recent_switches[device.name] = current_time
                else:
                    self.logger.warning(f"Hardware '{device.name}' konnte nicht ausgeschaltet werden")
            except Exception as e:
                self.logger.error(f"Fehler beim Hardware-Ausschalten: {e}")

        # Berechne und addiere Laufzeit zur Tagesstatistik
        if device.last_state_change:
            runtime = int((current_time - device.last_state_change).total_seconds() / 60)
            device.runtime_today += runtime
            self.logger.debug(f"Gerät '{device.name}' lief {runtime} Minuten, "
                              f"Gesamt heute: {device.runtime_today} Minuten")

        device.state = DeviceState.OFF
        device.last_state_change = current_time
        device.last_switch_off = current_time

        self.logger.info(f"Gerät '{device.name}' ausgeschaltet"
                         f"{f' - {reason}' if reason else ''}")

        return f"ausgeschaltet - {reason}" if reason else "ausgeschaltet"

    def _check_switch_on_hysteresis(self, device: Device, current_time: datetime) -> bool:
        """
        Prüft ob Hysterese-Zeit seit dem letzten Ausschalten abgelaufen ist.

        Dies verhindert zu schnelles Wiedereinschalten nach dem Ausschalten.

        Args:
            device: Zu prüfendes Gerät
            current_time: Aktuelle Zeit

        Returns:
            True wenn Einschalten erlaubt
        """
        if device.last_switch_off is None:
            # Gerät wurde noch nie ausgeschaltet oder ist beim Start aus
            return True

        time_since_off = current_time - device.last_switch_off
        can_switch_on = time_since_off >= self.hysteresis_time

        if not can_switch_on:
            remaining = self.hysteresis_time - time_since_off
            self.logger.debug(f"Gerät '{device.name}' kann noch nicht eingeschaltet werden. "
                            f"Hysterese: {remaining.total_seconds():.0f}s verbleibend")

        return can_switch_on

    def _check_min_runtime(self, device: Device, current_time: datetime) -> bool:
        """
        Prüft ob Mindestlaufzeit erreicht ist.

        Args:
            device: Zu prüfendes Gerät
            current_time: Aktuelle Zeit

        Returns:
            True wenn Mindestlaufzeit erreicht oder keine definiert
        """
        if device.min_runtime == 0 or device.last_state_change is None:
            return True

        runtime = (current_time - device.last_state_change).total_seconds() / 60
        return runtime >= device.min_runtime

    def reset_daily_stats(self) -> None:
        """Setzt die Tagesstatistiken aller Geräte zurück"""
        for device in self.device_manager.devices:
            device.runtime_today = 0
            if device.state == DeviceState.BLOCKED:
                device.state = DeviceState.OFF

        self.logger.info("Tagesstatistiken der Geräte zurückgesetzt")