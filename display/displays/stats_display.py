"""Statistik-Display für Tagesauswertungen."""

from typing import Any, Dict, List, Tuple
from ..core import BaseDisplay, Colors
from ..components import Header, Table, Separator, ProgressBar


class StatsDisplay(BaseDisplay):
    """Zeigt Tagesstatistiken formatiert an"""

    def __init__(self, config: Any):
        """
        Initialisiert StatsDisplay.

        Args:
            config: Konfigurationsobjekt
        """
        super().__init__(config)
        self.header = Header()
        self.table = Table(self.color_manager)
        self.separator = Separator()
        self.progress = ProgressBar(color_manager=self.color_manager)

    def display(self, stats: Any) -> None:
        """
        Zeigt die Tagesstatistiken an.

        Args:
            stats: DailyStats-Objekt
        """
        self._display_header(stats)
        self._display_energy_section(stats)
        self._display_cost_section(stats)
        self._display_power_section(stats)
        self._display_metrics_section(stats)
        self.separator.line()

    def _display_header(self, stats: Any) -> None:
        """Zeigt den Header."""
        date_str = stats.date.strftime('%d.%m.%Y')
        self.header.display("TAGESSTATISTIK", date_str)

    def _display_energy_section(self, stats: Any) -> None:
        """Zeigt Energie-Sektion."""
        self.header.display_section("Energie heute")

        # Basis-Energiewerte
        energy_data = {
            "PV-Produktion:": (stats.pv_energy, "kWh"),
            "Verbrauch:": (stats.consumption_energy, "kWh"),
            "Eigenverbrauch:": (stats.self_consumption_energy, "kWh"),
            "Einspeisung:": (stats.feed_in_energy, "kWh"),
            "Netzbezug:": (stats.grid_energy, "kWh")
        }

        for label, (value, unit) in energy_data.items():
            self.print_value_line(label, value, unit, decimals=2)

        # Detaillierter Netzbezug
        if stats.grid_energy_day > 0 or stats.grid_energy_night > 0:
            self.separator.empty_line()
            print(f"  → Tagtarif: {stats.grid_energy_day:>8.2f} kWh")
            print(f"  → Nachttarif: {stats.grid_energy_night:>8.2f} kWh")

        # Batterie wenn vorhanden
        if stats.battery_charge_energy > 0 or stats.battery_discharge_energy > 0:
            self.separator.empty_line()
            self.print_value_line("Batterie geladen:", stats.battery_charge_energy, "kWh", decimals=2)
            self.print_value_line("Batterie entladen:", stats.battery_discharge_energy, "kWh", decimals=2)

    def _display_cost_section(self, stats: Any) -> None:
        """Zeigt Kosten-Sektion."""
        self.header.display_section("Kostenberechnung")

        currency = self.config.costs.currency_symbol

        # Kosten mit Farben
        cost_items = [
            ("Stromkosten (Netzbezug):", stats.cost_grid_consumption, Colors.RED),
            ("Einspeisevergütung:", stats.revenue_feed_in, Colors.GREEN),
            ("Eingesparte Kosten:", stats.cost_saved, Colors.GREEN)
        ]

        for label, value, color in cost_items:
            self.print_value_line(label, value, currency, color=color, decimals=2)

        self.separator.subsection()

        # Gesamtnutzen
        benefit_color = Colors.GREEN if stats.total_benefit > 0 else Colors.RED
        self.print_value_line("GESAMTNUTZEN:", stats.total_benefit, currency,
                              color=benefit_color, decimals=2)

        # Vergleichswert
        self.separator.empty_line()
        self.print_value_line("Kosten ohne Solar:", stats.cost_without_solar, currency, decimals=2)

        # ROI als Progress Bar
        if stats.cost_without_solar > 0:
            roi = (stats.total_benefit / stats.cost_without_solar) * 100
            self.progress.display(roi, 100, "Einsparungsquote", True,
                                  self.color_manager.get_threshold_color(roi, 'autarky'))

    def _display_power_section(self, stats: Any) -> None:
        """Zeigt Leistungs-Sektion."""
        self.header.display_section("Maximale Leistung")

        # PV-Leistung mit Farbe
        pv_color = self.color_manager.get_threshold_color(stats.pv_power_max, 'pv_power')
        self.print_value_line("PV-Leistung:", stats.pv_power_max, "W", color=pv_color)

        # Andere Leistungswerte
        self.print_value_line("Verbrauch:", stats.consumption_power_max, "W")

        if stats.surplus_power_max > 0:
            surplus_color = self.color_manager.get_threshold_color(stats.surplus_power_max, 'surplus')
            self.print_value_line("Überschuss:", stats.surplus_power_max, "W", color=surplus_color)

        # Batterie Min/Max
        if stats.battery_soc_min is not None and stats.battery_soc_max is not None:
            self.separator.empty_line()
            self._display_battery_stats(stats)

    def _display_battery_stats(self, stats: Any) -> None:
        """Zeigt Batterie-Statistiken."""
        print("Batterie-Ladestand:")

        # Min/Max als kleine Progress Bars
        if stats.battery_soc_min is not None:
            self.progress.display(stats.battery_soc_min, 100, "  Min", True,
                                  self.color_manager.get_threshold_color(stats.battery_soc_min, 'battery_soc'))

        if stats.battery_soc_max is not None:
            self.progress.display(stats.battery_soc_max, 100, "  Max", True,
                                  self.color_manager.get_threshold_color(stats.battery_soc_max, 'battery_soc'))

    def _display_metrics_section(self, stats: Any) -> None:
        """Zeigt Kennzahlen."""
        self.header.display_section("Kennzahlen")

        # Autarkiegrad
        autarky_color = self.color_manager.get_threshold_color(stats.autarky_avg, 'autarky')
        self.print_value_line("Ø Autarkiegrad:", stats.autarky_avg, "%",
                              color=autarky_color, decimals=1)

        # Energie-Autarkie
        energy_color = self.color_manager.get_threshold_color(stats.self_sufficiency_rate, 'autarky')
        self.print_value_line("Energie-Autarkie:", stats.self_sufficiency_rate, "%",
                              color=energy_color, decimals=1)

        # Laufzeit
        self.separator.empty_line()
        runtime_str = self.formatter.format_time(stats.runtime_hours)
        print(f"Laufzeit: {runtime_str}")

    def display_summary_table(self, stats_list: List[Any]) -> None:
        """
        Zeigt mehrere Tage als Vergleichstabelle.

        Args:
            stats_list: Liste von DailyStats
        """
        if not stats_list:
            return

        self.header.display("WOCHENÜBERSICHT")

        # Tabellen-Header
        headers = ["Datum", "PV (kWh)", "Verbrauch", "Autarkie %", "Nutzen (€)"]
        rows = []

        for stats in stats_list[-7:]:  # Letzte 7 Tage
            row = [
                stats.date.strftime('%d.%m'),
                f"{stats.pv_energy:.1f}",
                f"{stats.consumption_energy:.1f}",
                f"{stats.self_sufficiency_rate:.0f}",
                f"{stats.total_benefit:.2f}"
            ]
            rows.append(row)

        self.table.display(headers, rows, alignments=['l', 'r', 'r', 'r', 'r'])

        # Gesamtsummen
        self.separator.subsection()
        total_pv = sum(s.pv_energy for s in stats_list[-7:])
        total_benefit = sum(s.total_benefit for s in stats_list[-7:])

        print(f"Gesamt PV-Produktion: {total_pv:.1f} kWh")
        print(f"Gesamtnutzen: {total_benefit:.2f} {self.config.costs.currency_symbol}")