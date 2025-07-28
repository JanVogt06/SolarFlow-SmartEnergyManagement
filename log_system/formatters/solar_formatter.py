"""
Formatter für Solar-Daten.
"""

from typing import Any, Dict, List
from .base_formatter import BaseFormatter


class SolarFormatter(BaseFormatter):
    """Formatter für Solar-Log-Daten"""

    def format(self, data: Any) -> Dict[str, Any]:
        """
        Formatiert SolarData für Output.

        Args:
            data: SolarData-Objekt

        Returns:
            Dictionary mit formatierten Daten
        """
        return {
            'timestamp': self.format_timestamp(data.timestamp),
            'pv_power': self.format_number(data.pv_power),
            'grid_power': self.format_number(data.grid_power, with_sign=True),
            'battery_power': self.format_number(data.battery_power, with_sign=True)
            if data.battery_power != 0 else "0",
            'load_power': self.format_number(data.load_power),
            'battery_soc': self.format_number(data.battery_soc, decimals=1)
            if data.battery_soc is not None else "-",
            'total_production': self.format_number(data.total_production),
            'feed_in_power': self.format_number(data.feed_in_power),
            'grid_consumption': self.format_number(data.grid_consumption),
            'self_consumption': self.format_number(data.self_consumption),
            'autarky_rate': self.format_number(data.autarky_rate, decimals=1),
            'surplus_power': self.format_number(data.surplus_power)
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
                "PV-Erzeugung (W)",
                "Netz (W)",  # + = Bezug, - = Einspeisung
                "Batterie (W)",  # + = Entladung, - = Ladung
                "Hausverbrauch (W)",
                "Batterie-Stand (%)",
                "Gesamtproduktion (W)",
                "Einspeisung (W)",
                "Netzbezug (W)",
                "Eigenverbrauch (W)",
                "Autarkie (%)",
                "Überschuss (W)"
            ]
        else:
            return [
                "Timestamp",
                "PV Power (W)",
                "Grid Power (W)",  # + = consumption, - = feed-in
                "Battery Power (W)",  # + = discharge, - = charge
                "Load Power (W)",
                "Battery SOC (%)",
                "Total Production (W)",
                "Feed-in Power (W)",
                "Grid Consumption (W)",
                "Self Consumption (W)",
                "Autarky Rate (%)",
                "Surplus Power (W)"
            ]