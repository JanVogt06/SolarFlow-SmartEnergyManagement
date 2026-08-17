"""
Energie-Steuerung für den Smart Energy Manager.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple

from .device import Device, DeviceState
from .device_manager import DeviceManager
from .interfaces import ISmartDeviceInterface


class EnergyController:
    """Steuert Geräte basierend auf verfügbarer Energie"""

    def __init__(self, device_manager: DeviceManager,
                 device_interface: Optional[ISmartDeviceInterface] = None,
                 min_battery_soc_on: float = 95.0,
                 min_battery_soc_off: float = 20.0) -> None:
        """
        Initialisiert den EnergyController.

        Args:
            device_manager: Verwaltung der Geräte
            device_interface: Interface für Hardware-Steuerung (optional)
            min_battery_soc_on: Mindest-Batteriestand zum Einschalten (Default: 95%)
            min_battery_soc_off: Batteriestand unter dem ausgeschaltet wird (Default: 20%)
        """
        self.device_manager = device_manager
        self.device_interface = device_interface
        self.logger = logging.getLogger(__name__)

        # Batterie-Schwellwerte
        self.min_battery_soc_on = min_battery_soc_on
        self.min_battery_soc_off = min_battery_soc_off

        # Hysterese-Zeitspanne (verhindert zu häufiges Schalten)
        self.hysteresis_time: timedelta = timedelta(minutes=5)

        # Dauer, für die manuelles Schalten die Automatik pausiert
        self.manual_override_time: timedelta = timedelta(minutes=30)

        # Tracking für kürzlich geschaltete Geräte (verhindert falsche Sync-Erkennung
        # während der Bridge-Latenz). Format: {device_name: (zeit, ziel_status)}
        # ziel_status: True = ON, False = OFF
        self._recent_switches: Dict[str, Tuple[datetime, bool]] = {}
        self._switch_settle_time: timedelta = timedelta(seconds=15)

        # Tracking für Sync-Warnungen (nur einmal pro Gerät warnen)
        self._sync_warned_devices: set = set()

    def update(self, surplus_power: float, current_time: Optional[datetime] = None,
               battery_power: float = 0.0, battery_soc: float = 100.0) -> Dict[str, str]:
        """
        Aktualisiert Gerätezustände basierend auf verfügbarem Überschuss.

        Args:
            surplus_power: Aktuelle Einspeisung ins Netz in Watt (0 oder positiv)
            current_time: Aktuelle Zeit (optional, für Tests)
            battery_power: Batterieleistung in Watt (positiv = entlädt, negativ = lädt)
            battery_soc: Batterie-Ladestand in Prozent (0-100)

        Returns:
            Dict mit Statusänderungen {Gerätename: Aktion}
        """
        if current_time is None:
            current_time = datetime.now()

        changes: Dict[str, str] = {}
        self._release_expired_overrides(current_time)

        # Manuell übersteuerte und nicht erreichbare Geräte steuert die Automatik nicht
        devices = [d for d in self.device_manager.get_devices_by_priority()
                   if not d.is_manual(current_time) and d.state != DeviceState.UNREACHABLE]

        # Die verfügbare Leistung für neue Geräte ist der aktuelle Überschuss
        # plus die Leistung, die wir durch Abschalten von Geräten freigeben könnten
        current_consumption = self._controllable_consumption(devices)
        total_available = surplus_power + current_consumption

        self.logger.info(f"Energie-Update: Überschuss={surplus_power:.0f}W, "
                         f"Gesteuerter Verbrauch={current_consumption:.0f}W, "
                         f"Total verfügbar={total_available:.0f}W, "
                         f"Batterie={battery_soc:.1f}% ({battery_power:+.0f}W)")

        # Schritt 1: Prüfe welche Geräte ausgeschaltet werden müssen
        # Niedrigste Priorität zuerst (umgekehrte Reihenfolge), damit höher
        # priorisierte Geräte mit gleichem Verbrauch länger laufen
        for device in reversed(devices):
            if device.state == DeviceState.ON:
                # Prüfe kritischen Batteriestand
                if battery_soc < self.min_battery_soc_off:
                    if self._check_min_runtime(device, current_time):
                        action = self._switch_off(device, current_time,
                                                  f"Batteriestand kritisch ({battery_soc:.1f}% < {self.min_battery_soc_off}%)")
                        if action:
                            changes[device.name] = action
                            surplus_power += device.power_consumption
                            total_available = surplus_power + self._controllable_consumption(devices)
                    continue

                # Berechne den ECHTEN effektiven Überschuss
                # Wenn die Batterie entlädt (positiv), kommt die Energie nicht aus PV-Überschuss!
                if battery_power > 0:  # Batterie entlädt
                    # Der echte Überschuss wäre: Einspeisung + Geräteleistung - Batterie-Entladung
                    # Beispiel: 6W Einspeisung, 2000W Gerät, 3311W Batterie-Entladung
                    # → echter Überschuss = 6 + 2000 - 3311 = -1305W (kein Überschuss!)
                    effective_surplus = surplus_power + device.power_consumption - battery_power
                else:
                    # Batterie lädt oder Standby - normale Berechnung
                    # Der Überschuss ist Einspeisung + Geräteleistung
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
                            total_available = surplus_power + self._controllable_consumption(devices)

        # Schritt 2: Prüfe ob höher priorisierte Geräte eingeschaltet werden können
        # indem niedriger priorisierte ausgeschaltet werden
        changes.update(self._handle_priority_preemption(devices, total_available, current_time, battery_soc))

        # Aktualisiere total_available nach möglichen Änderungen
        total_available = surplus_power + self._controllable_consumption(devices)

        # Schritt 3: Prüfe welche Geräte eingeschaltet werden können
        available_for_new = total_available
        for device in devices:
            action = self._process_device_for_switching_on(device, available_for_new, current_time, battery_soc)

            if action:
                changes[device.name] = action
                # Aktualisiere verfügbare Leistung nach Einschaltung
                if "eingeschaltet" in action and device.state == DeviceState.ON:
                    available_for_new -= device.power_consumption

        return changes

    def set_device_interface(self, device_interface: Optional[ISmartDeviceInterface]) -> None:
        """
        Tauscht das Hardware-Interface, z.B. nach geänderter Hue-Konfiguration.

        Args:
            device_interface: Neues Interface
        """
        self.device_interface = device_interface
        self._recent_switches.clear()
        self._sync_warned_devices.clear()

    @staticmethod
    def _controllable_consumption(devices: List[Device]) -> float:
        """
        Summiert den Verbrauch der Geräte, die die Automatik abschalten könnte.

        Args:
            devices: Von der Automatik steuerbare Geräte

        Returns:
            Verbrauch in Watt
        """
        return sum(d.power_consumption for d in devices if d.state == DeviceState.ON)

    def start_manual_override(self, device: Device,
                              current_time: Optional[datetime] = None) -> None:
        """
        Nimmt ein Gerät für die konfigurierte Dauer aus der Automatik.

        Args:
            device: Manuell geschaltetes Gerät
            current_time: Aktuelle Zeit (optional)
        """
        minutes = self.manual_override_time.total_seconds() / 60
        if minutes <= 0:
            return

        device.manual_until = (current_time or datetime.now()) + self.manual_override_time
        self.logger.info(f"'{device.name}' bleibt {minutes:.0f} Minuten manuell gesteuert")

    def switch_manually(self, device: Device, on: bool,
                        current_time: Optional[datetime] = None) -> bool:
        """
        Schaltet ein Gerät manuell und pausiert dafür die Automatik.

        Args:
            device: Zu schaltendes Gerät
            on: Zielzustand
            current_time: Aktuelle Zeit (optional)

        Returns:
            True wenn die Hardware den Befehl angenommen hat
        """
        current_time = current_time or datetime.now()
        action = (self._switch_on(device, current_time) if on
                  else self._switch_off(device, current_time, "manuell geschaltet"))

        if action is None:
            return False

        self.start_manual_override(device, current_time)
        return True

    def release_manual_override(self, device: Device) -> None:
        """
        Gibt ein manuell übersteuertes Gerät sofort wieder an die Automatik zurück.

        Args:
            device: Betroffenes Gerät
        """
        if device.manual_until is None:
            return

        device.manual_until = None
        self.logger.info(f"'{device.name}' wird wieder automatisch gesteuert")

    def _release_expired_overrides(self, current_time: datetime) -> None:
        """Beendet abgelaufene manuelle Übersteuerungen."""
        for device in self.device_manager.snapshot_devices():
            if device.manual_until and current_time >= device.manual_until:
                device.manual_until = None
                self.logger.info(f"Manuelle Übersteuerung für '{device.name}' abgelaufen")

    def sync_states(self, current_time: Optional[datetime] = None) -> None:
        """
        Synchronisiert den internen Gerätestatus mit dem tatsächlichen Hardware-Status.

        Erkennt sowohl extern (z.B. über die Hue-App) geschaltete Geräte als auch
        Geräte, die gar nicht mehr antworten - etwa weil sie nicht eingesteckt sind.

        Args:
            current_time: Aktuelle Zeit (optional, für Tests)
        """
        if not self._has_hardware_interface():
            return

        if current_time is None:
            current_time = datetime.now()

        # Einmal frisch von der Hardware lesen, die Einzelabfragen unten treffen den Cache
        self.device_interface.refresh(force=True)

        # Snapshot statt direktem Zugriff: schützt vor parallelen API-Mutationen
        for device in self.device_manager.snapshot_devices():
            status = self.device_interface.get_status(device.name)
            if status is None:
                self._warn_device_missing(device)
                continue

            self._sync_warned_devices.discard(device.name)
            hw_on, reachable = status

            if not reachable:
                self._mark_unreachable(device, current_time)
                continue

            if self._is_switch_settling(device, hw_on, current_time):
                continue

            self._adopt_hardware_state(device, hw_on, current_time)

    def _has_hardware_interface(self) -> bool:
        """Prüft ob ein verbundenes Hardware-Interface vorhanden ist."""
        return (self.device_interface is not None
                and self.device_interface.connected
                and self.device_interface.interface_type != "null")

    def _warn_device_missing(self, device: Device) -> None:
        """Warnt einmalig, wenn ein Gerät im Hardware-Interface fehlt."""
        if device.name in self._sync_warned_devices:
            return

        self.logger.warning(
            f"Gerät '{device.name}' nicht im Hardware-Interface gefunden - Sync übersprungen. "
            f"Prüfe ob der Name exakt mit dem Hue-Gerätenamen übereinstimmt."
        )
        self._sync_warned_devices.add(device.name)

    def _mark_unreachable(self, device: Device, current_time: datetime) -> None:
        """Setzt ein nicht antwortendes Gerät auf UNREACHABLE."""
        if device.state == DeviceState.UNREACHABLE:
            return

        self.logger.warning(
            f"Gerät '{device.name}' antwortet nicht - vermutlich nicht eingesteckt"
        )
        if device.state == DeviceState.ON:
            self._accumulate_runtime(device, current_time)

        device.state = DeviceState.UNREACHABLE
        device.last_state_change = current_time
        self._recent_switches.pop(device.name, None)

    def _is_switch_settling(self, device: Device, hw_on: bool, current_time: datetime) -> bool:
        """Prüft ob die Bridge einen selbst abgesetzten Schaltbefehl noch nicht zeigt."""
        pending = self._recent_switches.get(device.name)
        if pending is None:
            return False

        switch_time, expected_state = pending
        if hw_on == expected_state:
            del self._recent_switches[device.name]
            return False

        if current_time - switch_time < self._switch_settle_time:
            self.logger.debug(f"Überspringe Sync für '{device.name}' - Bridge-Latenz")
            return True

        del self._recent_switches[device.name]
        return False

    def _adopt_hardware_state(self, device: Device, hw_on: bool, current_time: datetime) -> None:
        """Übernimmt den Hardware-Status in den internen Gerätezustand."""
        was_unreachable = device.state == DeviceState.UNREACHABLE
        if was_unreachable:
            self.logger.info(f"Gerät '{device.name}' ist wieder erreichbar")
        elif hw_on == (device.state == DeviceState.ON):
            return

        if hw_on:
            if not was_unreachable:
                self.logger.info(f"Gerät '{device.name}' wurde extern eingeschaltet")
                self.start_manual_override(device, current_time)
            device.state = DeviceState.ON
        else:
            if not was_unreachable:
                self.logger.info(f"Gerät '{device.name}' wurde extern ausgeschaltet")
                self.start_manual_override(device, current_time)
                self._accumulate_runtime(device, current_time)
                device.last_switch_off = current_time
            device.state = DeviceState.OFF

        device.last_state_change = current_time

    @staticmethod
    def _accumulate_runtime(device: Device, current_time: datetime) -> None:
        """Rechnet die laufende Session auf die Tageslaufzeit an."""
        if not device.last_state_change:
            return

        runtime = int((current_time - device.last_state_change).total_seconds() / 60)
        device.runtime_today += runtime

    def _handle_priority_preemption(self, devices: List[Device], total_available: float,
                                    current_time: datetime, battery_soc: float) -> Dict[str, str]:
        """
        Prüft ob höher priorisierte Geräte eingeschaltet werden können,
        indem niedriger priorisierte ausgeschaltet werden.

        Args:
            devices: Liste der Geräte sortiert nach Priorität
            total_available: Total verfügbare Leistung
            current_time: Aktuelle Zeit
            battery_soc: Batterie-Ladestand in Prozent

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

            # Prüfe Batterie-Mindeststand zum Einschalten
            if battery_soc < self.min_battery_soc_on:
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
                                        current_time: datetime,
                                        battery_soc: float = 100.0) -> Optional[str]:
        """
        Prüft ob ein Gerät eingeschaltet werden kann.

        Args:
            device: Zu prüfendes Gerät
            available_power: Verfügbare Leistung in Watt
            current_time: Aktuelle Zeit
            battery_soc: Batterie-Ladestand in Prozent

        Returns:
            Aktion oder None
        """
        if device.state == DeviceState.UNREACHABLE:
            return None

        # Prüfe Zeitbeschränkungen
        if not device.is_time_allowed(current_time):
            if device.state == DeviceState.ON:
                action = self._switch_off(device, current_time, "Außerhalb erlaubter Zeit")
                if action:
                    return action
                # Hardware-Schaltung fehlgeschlagen: Gerät könnte real noch ON sein,
                # daher nicht auf BLOCKED setzen — beim nächsten Sync wird korrigiert.
                return None
            device.state = DeviceState.BLOCKED
            return None

        # Prüfe Tageslaufzeit
        if not device.can_run_today():
            if device.state == DeviceState.ON:
                action = self._switch_off(device, current_time, "Maximale Tageslaufzeit erreicht")
                if action:
                    return action
                return None
            device.state = DeviceState.BLOCKED
            return None

        # Gerät kann grundsätzlich laufen - BLOCKED zurücksetzen
        if device.state == DeviceState.BLOCKED:
            device.state = DeviceState.OFF

        if device.state == DeviceState.OFF:
            # Prüfe Batterie-Mindeststand zum Einschalten
            if battery_soc < self.min_battery_soc_on:
                self.logger.info(f"Gerät '{device.name}' wartet auf Batterie "
                                 f"({battery_soc:.1f}% < {self.min_battery_soc_on}%)")
                return None

            # Gerät ist aus - prüfe ob einschalten
            if available_power >= device.switch_on_threshold:
                # Prüfe Hysterese für EINSCHALTEN (basierend auf letztem Ausschalten)
                if self._check_switch_on_hysteresis(device, current_time):
                    return self._switch_on(device, current_time)
            else:
                self.logger.debug(
                    f"Gerät '{device.name}' bleibt aus: "
                    f"Verfügbar={available_power:.0f}W < Schwellwert={device.switch_on_threshold:.0f}W"
                )

        return None

    def _apply_hardware_switch(self, device: Device, on: bool, current_time: datetime) -> bool:
        """
        Schaltet die Hardware und meldet, ob der virtuelle Status nachgezogen werden darf.

        Args:
            device: Zu schaltendes Gerät
            on: Zielzustand
            current_time: Aktuelle Zeit

        Returns:
            True wenn der Zustandswechsel übernommen werden darf
        """
        if self.device_interface is None or self.device_interface.interface_type == "null":
            return True

        target = "EIN" if on else "AUS"

        if not self.device_interface.connected:
            self.logger.warning(
                f"Hardware-Interface nicht verbunden - '{device.name}' bleibt unverändert"
            )
            return False

        try:
            success = (self.device_interface.switch_on(device.name) if on
                       else self.device_interface.switch_off(device.name))
        except Exception as e:
            self.logger.error(
                f"Hardware-Fehler beim Schalten von '{device.name}' auf {target}: {e}"
            )
            return False

        if not success:
            self.logger.warning(
                f"'{device.name}' konnte nicht auf {target} geschaltet werden - "
                f"Status bleibt unverändert"
            )
            return False

        self._recent_switches[device.name] = (current_time, on)
        return True

    def _switch_on(self, device: Device, current_time: datetime) -> Optional[str]:
        """
        Schaltet ein Gerät ein.

        Args:
            device: Einzuschaltendes Gerät
            current_time: Aktuelle Zeit

        Returns:
            Aktionsbeschreibung oder None wenn Hardware-Schaltung fehlschlug
        """
        if not self._apply_hardware_switch(device, True, current_time):
            return None

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
            Aktionsbeschreibung oder None wenn Hardware-Schaltung fehlschlug
        """
        if not self._apply_hardware_switch(device, False, current_time):
            return None

        self._accumulate_runtime(device, current_time)
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
        for device in self.device_manager.snapshot_devices():
            device.runtime_today = 0
            if device.state == DeviceState.BLOCKED:
                device.state = DeviceState.OFF

        self.logger.info("Tagesstatistiken der Geräte zurückgesetzt")