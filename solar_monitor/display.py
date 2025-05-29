"""
Anzeigeformatierung für den Fronius Solar Monitor.
"""

from typing import Optional
from .models import SolarData
from .config import Config


class DisplayFormatter:
    """Klasse für die Formatierung der Anzeige"""

    # ANSI Farb-Codes
    COLOR_GREEN = '\033[92m'
    COLOR_YELLOW = '\033[93m'
    COLOR_RED = '\033[91m'
    COLOR_BLUE = '\033[94m'
    COLOR_RESET = '\033[0m'
    COLOR_BOLD = '\033[1m'

    def __init__(self, config: Config):
        """
        Initialisiert den DisplayFormatter.

        Args:
            config: Konfigurationsobjekt
        """
        self.config = config
        self.enable_colors = config.ENABLE_COLORS

    def format_value(self, label: str, value: float, unit: str, width: int = 25) -> str:
        """
        Formatiert einen Wert für die Anzeige.

        Args:
            label: Beschriftung
            value: Anzuzeigender Wert
            unit: Einheit
            width: Breite des Label-Feldes

        Returns:
            Formatierter String
        """
        return f"{label:<{width}} {value:>10.0f} {unit}"

    def get_autarky_color(self, autarky_rate: float) -> str:
        """
        Gibt die Farbe basierend auf dem Autarkiegrad zurück.

        Args:
            autarky_rate: Autarkiegrad in Prozent

        Returns:
            ANSI-Farbcode oder leerer String
        """
        if not self.enable_colors:
            return ""

        if autarky_rate >= self.config.AUTARKY_HIGH_THRESHOLD:
            return self.COLOR_GREEN
        elif autarky_rate >= self.config.AUTARKY_MEDIUM_THRESHOLD:
            return self.COLOR_YELLOW
        else:
            return self.COLOR_RED

    def get_battery_soc_color(self, battery_soc: float) -> str:
        """
        Gibt die Farbe basierend auf dem Batterie-Ladestand zurück.

        Args:
            battery_soc: Batterie-Ladestand in Prozent

        Returns:
            ANSI-Farbcode oder leerer String
        """
        if not self.enable_colors:
            return ""

        if battery_soc >= self.config.BATTERY_SOC_HIGH_THRESHOLD:
            return self.COLOR_GREEN
        elif battery_soc >= self.config.BATTERY_SOC_MEDIUM_THRESHOLD:
            return self.COLOR_YELLOW
        else:
            return self.COLOR_RED

    def get_pv_power_color(self, pv_power: float) -> str:
        """
        Gibt die Farbe basierend auf der PV-Leistung zurück.

        Args:
            pv_power: PV-Leistung in Watt

        Returns:
            ANSI-Farbcode oder leerer String
        """
        if not self.enable_colors:
            return ""

        if pv_power >= self.config.PV_POWER_HIGH_THRESHOLD:
            return self.COLOR_GREEN
        elif pv_power >= self.config.PV_POWER_MEDIUM_THRESHOLD:
            return self.COLOR_YELLOW
        else:
            return self.COLOR_RED

    def get_surplus_color(self, surplus_power: float) -> str:
        """
        Gibt die Farbe basierend auf dem Überschuss zurück.

        Args:
            surplus_power: Überschuss-Leistung in Watt

        Returns:
            ANSI-Farbcode oder leerer String
        """
        if not self.enable_colors:
            return ""

        if surplus_power >= self.config.SURPLUS_HIGH_THRESHOLD:
            return self.COLOR_GREEN
        elif surplus_power >= self.config.SURPLUS_MEDIUM_THRESHOLD:
            return self.COLOR_YELLOW
        else:
            return self.COLOR_BLUE  # Blau für wenig Überschuss

    def display_data(self, data: SolarData) -> None:
        """
        Zeigt die Daten formatiert an.

        Args:
            data: Anzuzeigende Solardaten
        """
        # Header
        print("\n" + "=" * 60)
        print(f"{'Zeitstempel:':<20} {data.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        # Leistungsdaten
        print(self.format_value("PV-Erzeugung:", data.pv_power, "W"))
        print(self.format_value("Hausverbrauch:", data.load_power, "W"))

        # Netz
        if data.is_feeding_in:
            print(self.format_value("Einspeisung:", data.feed_in_power, "W"))
        elif data.grid_consumption > 0:
            print(self.format_value("Netzbezug:", data.grid_consumption, "W"))
        else:
            print(self.format_value("Netz:", 0, "W"))

        # Batterie
        if data.has_battery:
            self._display_battery_info(data)

        # Separator
        print("-" * 60)

        # Berechnete Werte mit Farbe
        self._display_calculated_values(data)

        print("=" * 60)

    def _display_battery_info(self, data: SolarData) -> None:
        """
        Zeigt Batterie-Informationen an.

        Args:
            data: Solardaten
        """
        # Batterie-Status
        if abs(data.battery_power) < self.config.BATTERY_IDLE_THRESHOLD:
            print(self.format_value("Batterie (Standby):", abs(data.battery_power), "W"))
        elif data.battery_charging:
            print(self.format_value("Batterie-Ladung:", data.battery_charge_power, "W"))
        else:
            print(self.format_value("Batterie-Entladung:", data.battery_discharge_power, "W"))

        # Batterie-Ladestand
        if data.battery_soc is not None:
            color = self.get_battery_soc_color(data.battery_soc)
            reset = self.COLOR_RESET if self.enable_colors else ""
            print(f"{'Batterie-Ladestand:':<25} {color}{data.battery_soc:>10.0f} %{reset}")

    def _display_calculated_values(self, data: SolarData) -> None:
        """
        Zeigt berechnete Werte mit Farbe an.

        Args:
            data: Solardaten
        """
        color = self.get_autarky_color(data.autarky_rate)
        reset = self.COLOR_RESET if self.enable_colors else ""

        print(f"{'Eigenverbrauch:':<25} {color}{data.self_consumption:>10.0f} W{reset}")
        print(f"{'Autarkiegrad:':<25} {color}{data.autarky_rate:>10.1f} %{reset}")

        # Zusätzliche Informationen
        if data.surplus_power > self.config.SURPLUS_DISPLAY_THRESHOLD:
            print(f"{'Verfügbarer Überschuss:':<25} {data.surplus_power:>10.0f} W")

    def display_simple(self, data: SolarData) -> None:
        """
        Zeigt eine vereinfachte Ansicht (für kleine Displays).

        Args:
            data: Anzuzeigende Solardaten
        """
        print(f"\n{data.timestamp.strftime('%H:%M:%S')} | "
              f"PV: {data.pv_power:>5.0f}W | "
              f"Last: {data.load_power:>4.0f}W | "
              f"Netz: {data.grid_power:>+5.0f}W | "
              f"Autarkie: {data.autarky_rate:>3.0f}%")

    def clear_screen(self) -> None:
        """Löscht den Bildschirm (plattformunabhängig)"""
        import os
        os.system('clear' if os.name == 'posix' else 'cls')