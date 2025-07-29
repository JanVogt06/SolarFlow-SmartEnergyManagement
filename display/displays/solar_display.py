"""Solar-Daten Display."""

from typing import Any, Optional
from ..core import BaseDisplay, Colors
from ..components import Header, Table, ProgressBar, Separator


class SolarDisplay(BaseDisplay):
    """Zeigt Solar-Daten formatiert an"""

    def __init__(self, config: Any):
        """
        Initialisiert SolarDisplay.

        Args:
            config: Konfigurationsobjekt
        """
        super().__init__(config)
        self.header = Header()
        self.table = Table(self.color_manager)
        self.progress = ProgressBar(color_manager=self.color_manager)
        self.separator = Separator()

    def display(self, data: Any, **kwargs: Any) -> None:
        """
        Zeigt die Solar-Daten an.

        Args:
            data: SolarData-Objekt
        """
        self._display_header(data)
        self._display_power_section(data)
        self._display_grid_section(data)

        if data.has_battery:
            self._display_battery_section(data)

        self.separator.subsection()
        self._display_calculated_section(data)
        self.separator.line()

    def _display_header(self, data: Any) -> None:
        """Zeigt den Header mit Zeitstempel."""
        timestamp = data.timestamp.strftime('%Y-%m-%d %H:%M:%S') if data.timestamp else "N/A"
        self.header.display("SOLAR MONITOR", timestamp)

    def _display_power_section(self, data: Any) -> None:
        """Zeigt die Leistungswerte."""
        # PV-Erzeugung mit Farbe
        pv_color = self.color_manager.get_threshold_color(data.pv_power, 'pv_power')
        self.table.display_colored_row("PV-Erzeugung:", data.pv_power, "W", pv_color)

        # Hausverbrauch
        self.table.display_colored_row("Hausverbrauch:", data.load_power, "W")

        # Gesamtproduktion wenn Batterie vorhanden
        if data.has_battery:
            total_color = self.color_manager.get_threshold_color(data.total_production, 'pv_power')
            self.table.display_colored_row("Gesamtproduktion:", data.total_production, "W", total_color)

    def _display_grid_section(self, data: Any) -> None:
        """Zeigt die Netzwerte."""
        if data.is_feeding_in:
            self.table.display_colored_row("Einspeisung:", data.feed_in_power, "W", Colors.GREEN)
        elif data.grid_consumption > 0:
            self.table.display_colored_row("Netzbezug:", data.grid_consumption, "W", Colors.RED)
        else:
            self.table.display_colored_row("Netz:", 0, "W")

    def _display_battery_section(self, data: Any) -> None:
        """Zeigt Batterie-Informationen."""
        self.separator.empty_line()

        # Batterie-Status
        if abs(data.battery_power) < self.config.battery.idle_threshold:
            status = "Standby"
            power = abs(data.battery_power)
            color = Colors.BLUE
        elif data.battery_charging:
            status = "Ladung"
            power = data.battery_charge_power
            color = Colors.YELLOW
        else:
            status = "Entladung"
            power = data.battery_discharge_power
            color = Colors.GREEN

        self.table.display_colored_row(f"Batterie ({status}):", power, "W", color)

        # Batterie-SOC mit Progress Bar
        if data.battery_soc is not None:
            self.progress.display_battery(data.battery_soc)

    def _display_calculated_section(self, data: Any) -> None:
        """Zeigt berechnete Werte."""
        # Eigenverbrauch und Autarkie
        autarky_color = self.color_manager.get_threshold_color(data.autarky_rate, 'autarky')

        self.table.display_colored_row("Eigenverbrauch:", data.self_consumption, "W", autarky_color)
        self.table.display_colored_row("Autarkiegrad:", data.autarky_rate, "%", autarky_color)

        # Überschuss wenn relevant
        if data.surplus_power >= self.config.display.surplus_display_threshold:
            surplus_color = self._get_surplus_color(data.surplus_power)
            self.table.display_colored_row("Verfügbarer Überschuss:", data.surplus_power, "W", surplus_color)

    def _get_surplus_color(self, surplus: float) -> str:
        """Bestimmt die Farbe für Überschussanzeige."""
        thresholds = self.config.thresholds.surplus

        if surplus >= thresholds['high']:
            return Colors.GREEN
        elif surplus >= thresholds['medium']:
            return Colors.YELLOW
        else:
            return Colors.BLUE

    def display_with_progress_bars(self, data: Any) -> None:
        """
        Alternative Anzeige mit Progress Bars.

        Args:
            data: SolarData-Objekt
        """
        self._display_header(data)

        # Zeige Leistungen als Progress Bars
        max_power = max(data.pv_power, data.load_power, 5000)  # 5kW minimum

        self.progress.display_power(data.pv_power, max_power, "PV-Erzeugung")
        self.progress.display_power(data.load_power, max_power, "Verbrauch")

        if data.has_battery:
            self.separator.empty_line()
            self.progress.display_battery(data.battery_soc or 0)

        self.separator.subsection()

        # Kennzahlen
        autarky_color = self.color_manager.get_threshold_color(data.autarky_rate, 'autarky')
        print(f"Autarkie: {self.color_manager.colorize(f'{data.autarky_rate:.1f}%', autarky_color)}")

        if data.surplus_power > 0:
            surplus_color = self._get_surplus_color(data.surplus_power)
            print(f"Überschuss: {self.color_manager.colorize(f'{data.surplus_power:.0f}W', surplus_color)}")

        self.separator.line()