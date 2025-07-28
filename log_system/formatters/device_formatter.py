"""
Formatter für Geräte-Daten.
"""

from typing import Any, Dict, List
from datetime import datetime
from .base_formatter import BaseFormatter


class DeviceEventFormatter(BaseFormatter):
    """Formatter für Geräte-Events"""

    def format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formatiert Device-Event für Output.

        Args:
            data: Dictionary mit Event-Daten

        Returns:
            Dictionary mit formatierten Daten
        """
        device = data['device']
        return {
            'timestamp': self.format_timestamp(datetime.now()),
            'device_name': device.name,
            'action': data['action'],
            'from_state': data['old_state'].value if hasattr(data['old_state'], 'value') else str(data['old_state']),
            'to_state': device.state.value if hasattr(device.state, 'value') else str(device.state),
            'reason': data['reason'],
            'surplus_power': self.format_number(data['surplus_power']),
            'device_power': self.format_number(device.power_consumption),
            'on_threshold': self.format_number(device.switch_on_threshold),
            'off_threshold': self.format_number(device.switch_off_threshold),
            'runtime_today': self.format_number(device.runtime_today),
            'priority': str(device.priority.value if hasattr(device.priority, 'value') else device.priority)
        }

    def get_headers(self) -> List[str]:
        """
        Gibt die CSV-Header zurück.

        Returns:
            Liste mit Header-Spalten
        """
        if self.use_german_headers:
            return [
                "Zeitstempel",
                "Gerät",
                "Aktion",
                "Von Status",
                "Zu Status",
                "Grund",
                "Überschuss (W)",
                "Geräteverbrauch (W)",
                "Schwellwert Ein (W)",
                "Schwellwert Aus (W)",
                "Laufzeit heute (min)",
                "Priorität"
            ]
        else:
            return [
                "Timestamp",
                "Device",
                "Action",
                "From State",
                "To State",
                "Reason",
                "Surplus (W)",
                "Device Power (W)",
                "On Threshold (W)",
                "Off Threshold (W)",
                "Runtime Today (min)",
                "Priority"
            ]


class DeviceStatusFormatter(BaseFormatter):
    """Formatter für Geräte-Status"""

    def format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formatiert Device-Status für Output.

        Args:
            data: Dictionary mit Status-Daten

        Returns:
            Dictionary mit formatierten Daten
        """
        devices = data['devices']
        surplus_power = data['surplus_power']

        # Basis-Daten
        result = {
            'timestamp': self.format_timestamp(datetime.now())
        }

        # Daten für jedes Gerät
        total_on = 0
        total_consumption = 0.0

        for device in devices:
            is_on = device.state.value == 'on' if hasattr(device.state, 'value') else False
            device_key = device.name.lower().replace(' ', '_')

            result[f'{device_key}_state'] = self.format_boolean(is_on)
            result[f'{device_key}_runtime'] = self.format_number(device.runtime_today)

            if is_on:
                total_on += 1
                total_consumption += device.power_consumption

        # Zusammenfassung
        used_surplus = min(total_consumption, max(0, surplus_power))

        result.update({
            'total_on': str(total_on),
            'total_consumption': self.format_number(total_consumption),
            'surplus_power': self.format_number(surplus_power),
            'used_surplus': self.format_number(used_surplus)
        })

        return result

    def get_headers(self) -> List[str]:
        """
        Gibt die CSV-Header zurück.

        Returns:
            Liste mit Header-Spalten
        """
        # Dynamische Header basierend auf Geräten
        # Muss zur Laufzeit mit tatsächlichen Geräten gefüllt werden
        return []  # Wird vom Writer dynamisch erstellt