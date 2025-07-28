"""
Formatter für Tagesstatistiken.
"""

from typing import Any, Dict, List
from .base_formatter import BaseFormatter


class StatsFormatter(BaseFormatter):
    """Formatter für Tagesstatistik-Daten"""

    def format(self, data: Any) -> Dict[str, Any]:
        """
        Formatiert DailyStats für Output.

        Args:
            data: DailyStats-Objekt

        Returns:
            Dictionary mit formatierten Daten
        """
        return {
            'date': data.date.strftime('%Y-%m-%d'),
            'runtime_hours': self.format_number(data.runtime_hours, decimals=1),
            'pv_energy': self.format_number(data.pv_energy, decimals=2),
            'consumption_energy': self.format_number(data.consumption_energy, decimals=2),
            'self_consumption_energy': self.format_number(data.self_consumption_energy, decimals=2),
            'feed_in_energy': self.format_number(data.feed_in_energy, decimals=2),
            'grid_energy': self.format_number(data.grid_energy, decimals=2),
            'grid_energy_day': self.format_number(data.grid_energy_day, decimals=2),
            'grid_energy_night': self.format_number(data.grid_energy_night, decimals=2),
            'battery_charge_energy': self.format_number(data.battery_charge_energy, decimals=2),
            'battery_discharge_energy': self.format_number(data.battery_discharge_energy, decimals=2),
            'pv_power_max': self.format_number(data.pv_power_max),
            'consumption_power_max': self.format_number(data.consumption_power_max),
            'feed_in_power_max': self.format_number(data.feed_in_power_max),
            'grid_power_max': self.format_number(data.grid_power_max),
            'surplus_power_max': self.format_number(data.surplus_power_max),
            'battery_soc_min': self.format_number(data.battery_soc_min, decimals=1)
            if data.battery_soc_min is not None else "-",
            'battery_soc_max': self.format_number(data.battery_soc_max, decimals=1)
            if data.battery_soc_max is not None else "-",
            'autarky_avg': self.format_number(data.autarky_avg, decimals=1),
            'self_sufficiency_rate': self.format_number(data.self_sufficiency_rate, decimals=1),
            'cost_grid_consumption': self.format_number(data.cost_grid_consumption, decimals=2),
            'revenue_feed_in': self.format_number(data.revenue_feed_in, decimals=2),
            'cost_saved': self.format_number(data.cost_saved, decimals=2),
            'total_benefit': self.format_number(data.total_benefit, decimals=2),
            'cost_without_solar': self.format_number(data.cost_without_solar, decimals=2)
        }

    def get_headers(self) -> List[str]:
        """
        Gibt die CSV-Header zurück.

        Returns:
            Liste mit Header-Spalten
        """
        if self.use_german_headers:
            return [
                "Datum",
                "Laufzeit (h)",
                "PV-Produktion (kWh)",
                "Verbrauch (kWh)",
                "Eigenverbrauch (kWh)",
                "Einspeisung (kWh)",
                "Netzbezug (kWh)",
                "Netzbezug Tag (kWh)",
                "Netzbezug Nacht (kWh)",
                "Batterie geladen (kWh)",
                "Batterie entladen (kWh)",
                "Max PV-Leistung (W)",
                "Max Verbrauch (W)",
                "Max Einspeisung (W)",
                "Max Netzbezug (W)",
                "Max Überschuss (W)",
                "Min Batterie SOC (%)",
                "Max Batterie SOC (%)",
                "Ø Autarkie (%)",
                "Energie-Autarkie (%)",
                "Stromkosten (EUR)",
                "Einspeisevergütung (EUR)",
                "Eingesparte Kosten (EUR)",
                "Gesamtnutzen (EUR)",
                "Kosten ohne Solar (EUR)"
            ]
        else:
            return [
                "Date",
                "Runtime (h)",
                "PV Production (kWh)",
                "Consumption (kWh)",
                "Self Consumption (kWh)",
                "Feed-in (kWh)",
                "Grid Consumption (kWh)",
                "Grid Day (kWh)",
                "Grid Night (kWh)",
                "Battery Charged (kWh)",
                "Battery Discharged (kWh)",
                "Max PV Power (W)",
                "Max Consumption (W)",
                "Max Feed-in (W)",
                "Max Grid Power (W)",
                "Max Surplus (W)",
                "Min Battery SOC (%)",
                "Max Battery SOC (%)",
                "Avg Autarky (%)",
                "Energy Autarky (%)",
                "Electricity Cost (EUR)",
                "Feed-in Revenue (EUR)",
                "Saved Cost (EUR)",
                "Total Benefit (EUR)",
                "Cost without Solar (EUR)"
            ]