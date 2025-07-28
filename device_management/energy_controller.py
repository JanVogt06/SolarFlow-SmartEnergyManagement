"""
Energie-Steuerung für den Smart Energy Manager.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from .device import Device, DeviceState
from .device_manager import DeviceManager


class EnergyController:
    """Steuert Geräte basierend auf verfügbarer Energie"""

    def __init__(self, device_manager: DeviceManager) -> None:
        """
        Initialisiert den EnergyController.

        Args:
            device_manager: Verwaltung der Geräte
        """
        self.device_manager = device_manager
        self.logger = logging.getLogger(__name__)

        # Hysterese-Zeitspanne (verhindert zu häufiges Schalten)
        self.hysteresis_time: timedelta = timedelta(minutes=5)

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

        # Sortiere Geräte nach Priorität
        devices = self.device_manager.get_devices_by_priority()

        # Berechne aktuellen Verbrauch der gesteuerten Geräte
        current_consumption = self.device_manager.get_total_consumption()

        # Die verfügbare Leistung für neue Geräte ist der aktuelle Überschuss
        # plus die Leistung, die wir durch Abschalten von Geräten freigeben könnten
        total_available = surplus_power + current_consumption

        self.logger.debug(f"Überschuss: {surplus_power}W, Gesteuerter Verbrauch: {current_consumption}W, "
                          f"Total verfügbar: {total_available}W")

        # Dann: Prüfe welche Geräte ausgeschaltet werden müssen
        # Verwende den TATSÄCHLICHEN Überschuss für die Ausschalt-Entscheidung
        for device in devices:
            if device.state == DeviceState.ON:
                # Gerät läuft - prüfe ob ausschalten basierend auf REALEM Überschuss
                if surplus_power < device.switch_off_threshold:
                    # Prüfe Mindestlaufzeit
                    if self._check_min_runtime(device, current_time):
                        action = self._switch_off(device, current_time,
                                                f"Überschuss ({surplus_power}W) < Schwellwert ({device.switch_off_threshold}W)")
                        if action:
                            changes[device.name] = action
                            # Aktualisiere verfügbare Leistung nach Abschaltung
                            surplus_power += device.power_consumption
                            total_available = surplus_power + self.device_manager.get_total_consumption()

        # Danach: Prüfe welche Geräte eingeschaltet werden können
        # Verwende die TOTAL verfügbare Leistung für die Einschalt-Entscheidung
        available_for_new = total_available
        for device in devices:
            action = self._process_device_for_switching_on(device, available_for_new, current_time)

            if action:
                changes[device.name] = action
                # Aktualisiere verfügbare Leistung nach Einschaltung
                if "eingeschaltet" in action and device.state == DeviceState.ON:
                    available_for_new -= device.power_consumption

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
                return self._switch_off(device, current_time, "Außerhalb erlaubter Zeit")
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
                # FIX 3: Prüfe Hysterese für EINSCHALTEN (basierend auf letztem Ausschalten)
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
        device.state = DeviceState.ON
        device.last_state_change = current_time

        self.logger.info(f"Gerät '{device.name}' eingeschaltet "
                         f"(Leistung: {device.power_consumption}W)")

        return "eingeschaltet"

    def _switch_off(self, device: Device, current_time: datetime, reason: str = "") -> str:
        """
        Schaltet ein Gerät aus.

        Args:
            device: Auszuschaltendes Gerät
            current_time: Aktuelle Zeit
            reason: Grund für das Ausschalten

        Returns:
            Aktionsbeschreibung
        """
        # Berechne und addiere Laufzeit zur Tagesstatistik
        if device.last_state_change:
            runtime = int((current_time - device.last_state_change).total_seconds() / 60)
            device.runtime_today += runtime
            self.logger.debug(f"Gerät '{device.name}' lief {runtime} Minuten, "
                            f"Gesamt heute: {device.runtime_today} Minuten")

        device.state = DeviceState.OFF
        device.last_state_change = current_time
        # FIX 3: Speichere Ausschaltzeit für Hysterese
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