"""
Anzeigeformatierung für den Fronius Solar Monitor.
"""

from typing import Optional
from .models import SolarData
from .config import Config
from .daily_stats import DailyStats


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

    def format_value(self, label: str, value: float, unit: str, width: int = 25, decimals: int = 0) -> str:
        """
        Formatiert einen Wert für die Anzeige.

        Args:
            label: Beschriftung
            value: Anzuzeigender Wert
            unit: Einheit
            width: Breite des Label-Feldes
            decimals: Anzahl Nachkommastellen

        Returns:
            Formatierter String
        """
        if decimals == 0:
            return f"{label:<{width}} {value:>10.0f} {unit}"
        else:
            return f"{label:<{width}} {value:>10.{decimals}f} {unit}"

    def format_value_with_color(self, label: str, value: float, unit: str, color: str = "", width: int = 25, decimals: int = 0) -> str:
        """
        Formatiert einen Wert für die Anzeige mit Farbe.

        Args:
            label: Beschriftung
            value: Anzuzeigender Wert
            unit: Einheit
            color: ANSI Farbcode
            width: Breite des Label-Feldes
            decimals: Anzahl Nachkommastellen

        Returns:
            Formatierter String mit Farbe
        """
        reset = self.COLOR_RESET if self.enable_colors and color else ""
        if decimals == 0:
            return f"{label:<{width}} {color}{value:>10.0f} {unit}{reset}"
        else:
            return f"{label:<{width}} {color}{value:>10.{decimals}f} {unit}{reset}"

    def get_threshold_color(self, value: float, threshold_key: str) -> str:
        """
        Generische Methode zur Farbbestimmung basierend auf Schwellwerten.

        Args:
            value: Zu prüfender Wert
            threshold_key: Schlüssel für die Schwellwerte in config.THRESHOLDS

        Returns:
            ANSI-Farbcode oder leerer String
        """
        if not self.enable_colors:
            return ""

        thresholds = self.config.THRESHOLDS.get(threshold_key, {})
        high = thresholds.get('high', float('inf'))
        medium = thresholds.get('medium', 0)

        if value >= high:
            return self.COLOR_GREEN
        elif value >= medium:
            return self.COLOR_YELLOW
        else:
            return self.COLOR_RED

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

        # PV-Erzeugung mit Farbe
        pv_color = self.get_threshold_color(data.pv_power, 'pv_power')
        print(self.format_value_with_color("PV-Erzeugung:", data.pv_power, "W", pv_color))

        # Hausverbrauch (ohne Farbe)
        print(self.format_value("Hausverbrauch:", data.load_power, "W"))

        # Gesamtproduktion
        if data.has_battery:
            total_prod_color = self.get_threshold_color(data.total_production, 'pv_power')
            print(self.format_value_with_color("Gesamtproduktion:", data.total_production, "W", total_prod_color))

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

        # Batterie-Ladestand mit Farbe
        if data.battery_soc is not None:
            color = self.get_threshold_color(data.battery_soc, 'battery_soc')
            print(self.format_value_with_color("Batterie-Ladestand:", data.battery_soc, "%", color))

    def _display_calculated_values(self, data: SolarData) -> None:
        """
        Zeigt berechnete Werte mit Farbe an.

        Args:
            data: Solardaten
        """
        # Eigenverbrauch und Autarkie mit Farbe
        autarky_color = self.get_threshold_color(data.autarky_rate, 'autarky')
        print(self.format_value_with_color("Eigenverbrauch:", data.self_consumption, "W", autarky_color))
        print(self.format_value_with_color("Autarkiegrad:", data.autarky_rate, "%", autarky_color))

        if data.surplus_power >= self.config.SURPLUS_DISPLAY_THRESHOLD:
            # Spezielle Farblogik für Überschuss (Blau für wenig)
            if not self.enable_colors:
                surplus_color = ""
            elif data.surplus_power >= self.config.THRESHOLDS['surplus']['high']:
                surplus_color = self.COLOR_GREEN
            elif data.surplus_power >= self.config.THRESHOLDS['surplus']['medium']:
                surplus_color = self.COLOR_YELLOW
            else:
                surplus_color = self.COLOR_BLUE  # Blau für wenig Überschuss

            print(self.format_value_with_color("Verfügbarer Überschuss:", data.surplus_power, "W", surplus_color))

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

    def display_daily_stats(self, stats: DailyStats) -> None:
        """
        Zeigt die Tagesstatistiken an.

        Args:
            stats: Anzuzeigende Tagesstatistiken
        """
        print("\n" + "=" * 60)
        print(f"{'TAGESSTATISTIK':<20} {stats.date.strftime('%d.%m.%Y')}")
        print("=" * 60)

        # Energiewerte
        print("\nEnergie heute:")
        print(self.format_value("PV-Produktion:", stats.pv_energy, "kWh", width=25, decimals=2))
        print(self.format_value("Verbrauch:", stats.consumption_energy, "kWh", width=25, decimals=2))
        print(self.format_value("Eigenverbrauch:", stats.self_consumption_energy, "kWh", width=25, decimals=2))
        print(self.format_value("Einspeisung:", stats.feed_in_energy, "kWh", width=25, decimals=2))
        print(self.format_value("Netzbezug:", stats.grid_energy, "kWh", width=25, decimals=2))

        # Batterie wenn vorhanden
        if stats.battery_charge_energy > 0 or stats.battery_discharge_energy > 0:
            print(self.format_value("Batterie geladen:", stats.battery_charge_energy, "kWh", width=25, decimals=2))
            print(self.format_value("Batterie entladen:", stats.battery_discharge_energy, "kWh", width=25, decimals=2))

        # Maximale Leistungswerte
        print("\nMaximale Leistung:")
        pv_max_color = self.get_threshold_color(stats.pv_power_max, 'pv_power')
        print(self.format_value_with_color("PV-Leistung:", stats.pv_power_max, "W", pv_max_color))
        print(self.format_value("Verbrauch:", stats.consumption_power_max, "W"))

        if stats.surplus_power_max > 0:
            surplus_color = self.get_threshold_color(stats.surplus_power_max, 'surplus')
            print(self.format_value_with_color("Überschuss:", stats.surplus_power_max, "W", surplus_color))

        # Batterie Min/Max
        if stats.battery_soc_min is not None and stats.battery_soc_max is not None:
            print(f"\nBatterie-Ladestand:")
            min_color = self.get_threshold_color(stats.battery_soc_min, 'battery_soc')
            max_color = self.get_threshold_color(stats.battery_soc_max, 'battery_soc')
            print(f"  Min: {min_color}{stats.battery_soc_min:>5.1f}%{self.COLOR_RESET if self.enable_colors else ''} | "
                  f"Max: {max_color}{stats.battery_soc_max:>5.1f}%{self.COLOR_RESET if self.enable_colors else ''}")

        # Durchschnitte und Berechnungen
        print("\nKennzahlen:")
        autarky_color = self.get_threshold_color(stats.autarky_avg, 'autarky')
        print(self.format_value_with_color("Ø Autarkiegrad:", stats.autarky_avg, "%", autarky_color, decimals=1))

        # Autarkie basierend auf Energiewerten
        energy_autarky_color = self.get_threshold_color(stats.self_sufficiency_rate, 'autarky')
        print(self.format_value_with_color("Energie-Autarkie:", stats.self_sufficiency_rate, "%", energy_autarky_color, decimals=1))

        print(f"\nLaufzeit: {stats.runtime_hours:.1f} Stunden")
        print("=" * 60)