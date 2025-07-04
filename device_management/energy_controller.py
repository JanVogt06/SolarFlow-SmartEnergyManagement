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

    def __init__(self, device_manager: DeviceManager):
        """
        Initialisiert den EnergyController.

        Args:
            device_manager: Verwaltung der Geräte
        """
        self.device_manager = device_manager
        self.logger = logging.getLogger(__name__)

        # Hysterese-Zeitspanne (verhindert zu häufiges Schalten)
        self.hysteresis_time = timedelta(minutes=5)

    def update(self, surplus_power: float, current_time: Optional[datetime] = None) -> Dict[str, str]:
        """
        Aktualisiert Gerätezustände basierend auf verfügbarem Überschuss.

        Args:
            surplus_power: Verfügbarer Überschuss in Watt
            current_time: Aktuelle Zeit (optional, für Tests)

        Returns:
            Dict mit Statusänderungen {Gerätename: Aktion}
        """
        if current_time is None:
            current_time = datetime.now()

        changes = {}

        # Sortiere Geräte nach Priorität
        devices = self.device_manager.get_devices_by_priority()

        # Berechne aktuellen Verbrauch
        current_consumption = self.device_manager.get_total_consumption()
        available_power = surplus_power + current_consumption

        self.logger.debug(f"Überschuss: {surplus_power}W, Verbrauch: {current_consumption}W, "
                          f"Verfügbar: {available_power}W")

        # Verarbeite Geräte nach Priorität
        for device in devices:
            action = self._process_device(device, available_power, current_time)

            if action:
                changes[device.name] = action

                # Aktualisiere verfügbare Leistung
                if action == "eingeschaltet" and device.state == DeviceState.ON:
                    available_power -= device.power_consumption
                elif action == "ausgeschaltet" and device.state == DeviceState.OFF:
                    available_power += device.power_consumption

        return changes

    def _process_device(self, device: Device, available_power: float, current_time: datetime) -> Optional[str]:
        """
        Verarbeitet ein einzelnes Gerät.

        Args:
            device: Zu verarbeitendes Gerät
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

        # Entscheide basierend auf aktuellem Zustand
        if device.state == DeviceState.OFF or device.state == DeviceState.BLOCKED:
            # Gerät ist aus - prüfe ob einschalten
            if available_power >= device.switch_on_threshold:
                # Prüfe Hysterese
                if self._check_hysteresis(device, current_time):
                    return self._switch_on(device, current_time)

        elif device.state == DeviceState.ON:
            # Gerät läuft - prüfe ob ausschalten
            if available_power < device.switch_off_threshold:
                # Prüfe Mindestlaufzeit
                if self._check_min_runtime(device, current_time):
                    return self._switch_off(device, current_time, "Nicht genug Überschuss")

        return None

    def _switch_on(self, device: Device, current_time: datetime) -> str:
        """Schaltet ein Gerät ein"""
        device.state = DeviceState.ON
        device.last_state_change = current_time

        self.logger.info(f"Gerät '{device.name}' eingeschaltet "
                         f"(Leistung: {device.power_consumption}W)")

        return "eingeschaltet"

    def _switch_off(self, device: Device, current_time: datetime, reason: str = "") -> str:
        """Schaltet ein Gerät aus"""
        # Berechne Laufzeit
        if device.last_state_change:
            runtime = int((current_time - device.last_state_change).total_seconds() / 60)
            device.runtime_today += runtime

        device.state = DeviceState.OFF
        device.last_state_change = current_time

        self.logger.info(f"Gerät '{device.name}' ausgeschaltet"
                         f"{f' - {reason}' if reason else ''}")

        return "ausgeschaltet"

    def _check_hysteresis(self, device: Device, current_time: datetime) -> bool:
        """Prüft ob Hysterese-Zeit abgelaufen ist"""
        if device.last_state_change is None:
            return True

        time_since_change = current_time - device.last_state_change
        return time_since_change >= self.hysteresis_time

    def _check_min_runtime(self, device: Device, current_time: datetime) -> bool:
        """Prüft ob Mindestlaufzeit erreicht ist"""
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