"""
Anzeigeformatierung für den Fronius Solar Monitor.
"""

from typing import Optional, Tuple, List, Any
from .models import SolarData
from .config import Config
from .daily_stats import DailyStats
from device_management import DeviceState, Device, DeviceManager


class DisplayFormatter:
    """Klasse für die Formatierung der Anzeige"""

    # ANSI Farb-Codes
    COLOR_GREEN = '\033[92m'
    COLOR_YELLOW = '\033[93m'
    COLOR_RED = '\033[91m'
    COLOR_BLUE = '\033[94m'
    COLOR_RESET = '\033[0m'

    # Display-Konstanten
    SEPARATOR_WIDTH = 60
    SEPARATOR_CHAR = "="
    SUB_SEPARATOR_CHAR = "-"
    LABEL_WIDTH = 25
    VALUE_WIDTH = 10

    def __init__(self, config: Config) -> None:
        """
        Initialisiert den DisplayFormatter.

        Args:
            config: Konfigurationsobjekt
        """
        self.config = config
        self.enable_colors: bool = config.display.enable_colors

    # ========== Basis-Formatierungsmethoden ==========

    def _get_color(self, color_constant: str) -> str:
        """
        Gibt Farbcode zurück wenn Farben aktiviert sind.

        Args:
            color_constant: ANSI Farbcode-Konstante

        Returns:
            Farbcode oder leerer String
        """
        return color_constant if self.enable_colors else ""

    def _colorize(self, text: str, color: str) -> str:
        """
        Färbt Text wenn Farben aktiviert sind.

        Args:
            text: Zu färbender Text
            color: Farbcode

        Returns:
            Gefärbter Text oder Original
        """
        if not color or not self.enable_colors:
            return text
        return f"{color}{text}{self.COLOR_RESET}"

    def _print_separator(self, char: Optional[str] = None, width: Optional[int] = None) -> None:
        """
        Druckt eine Trennlinie.

        Args:
            char: Zeichen für die Trennlinie
            width: Breite der Trennlinie
        """
        char = char or self.SEPARATOR_CHAR
        width = width or self.SEPARATOR_WIDTH
        print(char * width)

    def _print_header(self, title: str, subtitle: Optional[str] = None) -> None:
        """
        Druckt einen formatierten Header.

        Args:
            title: Haupttitel
            subtitle: Optionaler Untertitel
        """
        self._print_separator()
        if subtitle:
            print(f"{title:<20} {subtitle}")
        else:
            print(title)
        self._print_separator()

    def format_value(self, label: str, value: float, unit: str,
                    width: Optional[int] = None, decimals: int = 0) -> str:
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
        width = width or self.LABEL_WIDTH
        if decimals == 0:
            return f"{label:<{width}} {value:>{self.VALUE_WIDTH}.0f} {unit}"
        else:
            return f"{label:<{width}} {value:>{self.VALUE_WIDTH}.{decimals}f} {unit}"

    def format_value_with_color(self, label: str, value: float, unit: str,
                               color: str = "", width: Optional[int] = None,
                               decimals: int = 0) -> str:
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
        width = width or self.LABEL_WIDTH
        formatted_value = f"{value:>{self.VALUE_WIDTH}.{decimals}f}" if decimals else f"{value:>{self.VALUE_WIDTH}.0f}"
        colored_value = self._colorize(f"{formatted_value} {unit}", color)
        return f"{label:<{width}} {colored_value}"

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

    # ========== Hauptanzeige-Methoden ==========

    def display_data(self, data: SolarData) -> None:
        """
        Zeigt die Daten formatiert an.

        Args:
            data: Anzuzeigende Solardaten
        """
        self._display_data_header(data)
        self._display_power_values(data)
        self._display_grid_values(data)

        if data.has_battery:
            self._display_battery_info(data)

        self._print_separator(self.SUB_SEPARATOR_CHAR)
        self._display_calculated_values(data)
        self._print_separator()

    def display_data_with_devices(self, data: SolarData, device_manager: DeviceManager) -> None:
        """
        Zeigt die Daten mit Gerätestatus formatiert an.

        Args:
            data: Anzuzeigende Solardaten
            device_manager: DeviceManager mit Geräteinformationen
        """
        # Zeige normale Solar-Daten
        self.display_data(data)

        # Füge Geräte-Sektion hinzu
        self._display_device_section(data, device_manager)

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
        Zeigt die Tagesstatistiken mit Kostenberechnung an.

        Args:
            stats: Anzuzeigende Tagesstatistiken
        """
        self._display_stats_header(stats)
        self._display_energy_section(stats)
        self._display_cost_section(stats)
        self._display_power_section(stats)
        self._display_metrics_section(stats)
        self._print_separator()

    # ========== Private Hilfsmethoden für display_data ==========

    def _display_data_header(self, data: SolarData) -> None:
        """Zeigt den Header mit Zeitstempel."""
        timestamp = data.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        self._print_header(f"{'Zeitstempel:':<20}", timestamp)

    def _display_power_values(self, data: SolarData) -> None:
        """Zeigt die Leistungswerte an."""
        pv_color = self._get_color(self.get_threshold_color(data.pv_power, 'pv_power'))
        print(self.format_value_with_color("PV-Erzeugung:", data.pv_power, "W", pv_color))
        print(self.format_value("Hausverbrauch:", data.load_power, "W"))

        if data.has_battery:
            total_prod_color = self._get_color(self.get_threshold_color(data.total_production, 'pv_power'))
            print(self.format_value_with_color("Gesamtproduktion:", data.total_production, "W", total_prod_color))

    def _display_grid_values(self, data: SolarData) -> None:
        """Zeigt die Netzwerte an."""
        if data.is_feeding_in:
            print(self.format_value("Einspeisung:", data.feed_in_power, "W"))
        elif data.grid_consumption > 0:
            print(self.format_value("Netzbezug:", data.grid_consumption, "W"))
        else:
            print(self.format_value("Netz:", 0, "W"))

    def _display_battery_info(self, data: SolarData) -> None:
        """Zeigt Batterie-Informationen an."""
        # Batterie-Status
        if abs(data.battery_power) < self.config.battery.idle_threshold:
            print(self.format_value("Batterie (Standby):", abs(data.battery_power), "W"))
        elif data.battery_charging:
            print(self.format_value("Batterie-Ladung:", data.battery_charge_power, "W"))
        else:
            print(self.format_value("Batterie-Entladung:", data.battery_discharge_power, "W"))

        # Batterie-Ladestand mit Farbe
        if data.battery_soc is not None:
            color = self._get_color(self.get_threshold_color(data.battery_soc, 'battery_soc'))
            print(self.format_value_with_color("Batterie-Ladestand:", data.battery_soc, "%", color))

    def _display_calculated_values(self, data: SolarData) -> None:
        """Zeigt berechnete Werte mit Farbe an."""
        # Eigenverbrauch und Autarkie mit Farbe
        autarky_color = self._get_color(self.get_threshold_color(data.autarky_rate, 'autarky'))
        print(self.format_value_with_color("Eigenverbrauch:", data.self_consumption, "W", autarky_color))
        print(self.format_value_with_color("Autarkiegrad:", data.autarky_rate, "%", autarky_color))

        if data.surplus_power >= self.config.display.surplus_display_threshold:
            surplus_color = self._get_surplus_color(data.surplus_power)
            print(self.format_value_with_color("Verfügbarer Überschuss:", data.surplus_power, "W", surplus_color))

    def _get_surplus_color(self, surplus_power: float) -> str:
        """Bestimmt die Farbe für Überschussanzeige."""
        if not self.enable_colors:
            return ""

        if surplus_power >= self.config.THRESHOLDS['surplus']['high']:
            return self.COLOR_GREEN
        elif surplus_power >= self.config.THRESHOLDS['surplus']['medium']:
            return self.COLOR_YELLOW
        else:
            return self.COLOR_BLUE  # Blau für wenig Überschuss

    # ========== Private Hilfsmethoden für display_data_with_devices ==========

    def _display_device_section(self, data: SolarData, device_manager) -> None:
        """Zeigt die Gerätesteuerungs-Sektion."""
        print("\n" + self.SUB_SEPARATOR_CHAR * self.SEPARATOR_WIDTH)
        print("GERÄTESTEUERUNG:")
        self._print_separator(self.SUB_SEPARATOR_CHAR)

        self._display_device_summary(data, device_manager)
        self._display_device_list(data, device_manager)
        self._print_separator()

    def _display_device_summary(self, data: SolarData, device_manager) -> None:
        """Zeigt die Zusammenfassung der Gerätesteuerung."""
        controlled_consumption = device_manager.get_total_consumption()

        print(f"Gesteuerter Verbrauch:    {controlled_consumption:>10.0f} W")
        print(f"Aktueller Überschuss:     {data.surplus_power:>10.0f} W")

        # Optional: Zeige theoretischen Überschuss
        if controlled_consumption > 0:
            theoretical_surplus = data.surplus_power + controlled_consumption
            print(f"Theoretischer Überschuss: {theoretical_surplus:>10.0f} W (wenn alle Geräte aus)")
        print()

    def _display_device_list(self, data: SolarData, device_manager) -> None:
        """Zeigt die Liste der Geräte."""
        devices = device_manager.get_devices_by_priority()

        if not devices:
            print("Keine Geräte konfiguriert")
            return

        # Header
        print(f"{'Gerät':<20} {'Priorität':>9} {'Leistung':>10} {'Status':<12} {'Laufzeit heute':>14}")
        print("-" * 75)

        # Geräte
        for device in devices:
            self._display_device_row(device, data)

    def _display_device_row(self, device, data: SolarData) -> None:
        """Zeigt eine einzelne Gerätezeile."""
        # Status ermitteln
        status_text, status_color = self._get_device_status_display(device)

        # Laufzeit formatieren
        total_runtime = device.get_current_runtime(data.timestamp)
        runtime_str = self._format_runtime(total_runtime)

        # Zeile ausgeben
        status_colored = self._colorize(f"{status_text:<10}", status_color)
        print(f"{device.name:<20} {device.priority:>9} {device.power_consumption:>9.0f}W "
              f"{status_colored} {runtime_str:>14}")

        # Zusätzliche Info bei Blockierung
        if device.state.value == "blocked":
            self._display_device_block_reason(device, data)

    def _get_device_status_display(self, device: Device) -> Tuple[str, str]:
        """
        Gibt Status-Text und Farbe für ein Gerät zurück.

        Args:
            device: Gerät dessen Status angezeigt werden soll

        Returns:
            Tuple aus (Status-Text, Farbcode)
        """
        if device.state.value == "on":
            return "EIN", self._get_color(self.COLOR_GREEN)
        elif device.state.value == "blocked":
            return "BLOCKIERT", self._get_color(self.COLOR_YELLOW)
        else:
            return "AUS", self._get_color(self.COLOR_RED)

    def _format_runtime(self, total_minutes: int) -> str:
        """
        Formatiert Laufzeit in Stunden und Minuten.

        Args:
            total_minutes: Gesamtlaufzeit in Minuten

        Returns:
            Formatierter String (z.B. "2h 30m")
        """
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours}h {minutes}m"

    def _display_device_block_reason(self, device, data: SolarData) -> None:
        """Zeigt den Grund für eine Geräteblockierung."""
        if not device.can_run_today():
            print(f"  → Maximale Tageslaufzeit erreicht")
        elif not device.is_time_allowed(data.timestamp):
            print(f"  → Außerhalb der erlaubten Zeiten")

    # ========== Private Hilfsmethoden für display_daily_stats ==========

    def _display_stats_header(self, stats: DailyStats) -> None:
        """Zeigt den Header der Tagesstatistik."""
        date_str = stats.date.strftime('%d.%m.%Y')
        self._print_header("TAGESSTATISTIK", date_str)

    def _display_energy_section(self, stats: DailyStats) -> None:
        """Zeigt die Energie-Sektion der Tagesstatistik."""
        print("\nEnergie heute:")

        # Basis-Energiewerte
        energy_values = [
            ("PV-Produktion:", stats.pv_energy),
            ("Verbrauch:", stats.consumption_energy),
            ("Eigenverbrauch:", stats.self_consumption_energy),
            ("Einspeisung:", stats.feed_in_energy),
            ("Netzbezug:", stats.grid_energy)
        ]

        for label, value in energy_values:
            print(self.format_value(label, value, "kWh", decimals=2))

        # Detaillierter Netzbezug
        if stats.grid_energy_day > 0 or stats.grid_energy_night > 0:
            print(f"  → Tagtarif: {stats.grid_energy_day:>8.2f} kWh")
            print(f"  → Nachttarif: {stats.grid_energy_night:>8.2f} kWh")

        # Batterie wenn vorhanden
        if stats.battery_charge_energy > 0 or stats.battery_discharge_energy > 0:
            print(self.format_value("Batterie geladen:", stats.battery_charge_energy, "kWh", decimals=2))
            print(self.format_value("Batterie entladen:", stats.battery_discharge_energy, "kWh", decimals=2))

    def _display_cost_section(self, stats: DailyStats) -> None:
        """Zeigt die Kosten-Sektion der Tagesstatistik."""
        print("\nKostenberechnung:")
        currency = self.config.costs.currency_symbol

        # Kosten mit Farben
        cost_items = [
            ("Stromkosten (Netzbezug):", stats.cost_grid_consumption, self.COLOR_RED),
            ("Einspeisevergütung:", stats.revenue_feed_in, self.COLOR_GREEN),
            ("Eingesparte Kosten:", stats.cost_saved, self.COLOR_GREEN)
        ]

        for label, value, color in cost_items:
            colored_value = self._colorize(f"{value:>10.2f} {currency}", self._get_color(color))
            print(f"{label:<25} {colored_value}")

        self._print_separator(self.SUB_SEPARATOR_CHAR)

        # Gesamtnutzen
        benefit_color = self._get_color(self.COLOR_GREEN if stats.total_benefit > 0 else self.COLOR_RED)
        benefit_text = self._colorize(f"{stats.total_benefit:>10.2f} {currency}", benefit_color)
        print(f"{'GESAMTNUTZEN:':<25} {benefit_text}")

        # Vergleichswert
        print(f"\n{'Kosten ohne Solar:':<25} {stats.cost_without_solar:>10.2f} {currency}")

        # ROI
        if stats.cost_without_solar > 0:
            roi = (stats.total_benefit / stats.cost_without_solar) * 100
            roi_color = self._get_color(self.get_threshold_color(roi, 'autarky'))
            roi_text = self._colorize(f"{roi:>10.1f} %", roi_color)
            print(f"{'Einsparungsquote:':<25} {roi_text}")

    def _display_power_section(self, stats: DailyStats) -> None:
        """Zeigt die Leistungs-Sektion der Tagesstatistik."""
        print("\nMaximale Leistung:")

        # PV-Leistung mit Farbe
        pv_max_color = self._get_color(self.get_threshold_color(stats.pv_power_max, 'pv_power'))
        print(self.format_value_with_color("PV-Leistung:", stats.pv_power_max, "W", pv_max_color))

        # Andere Leistungswerte
        print(self.format_value("Verbrauch:", stats.consumption_power_max, "W"))

        if stats.surplus_power_max > 0:
            surplus_color = self._get_color(self.get_threshold_color(stats.surplus_power_max, 'surplus'))
            print(self.format_value_with_color("Überschuss:", stats.surplus_power_max, "W", surplus_color))

        # Batterie Min/Max
        if stats.battery_soc_min is not None and stats.battery_soc_max is not None:
            self._display_battery_stats(stats)

    def _display_battery_stats(self, stats: DailyStats) -> None:
        """Zeigt Batterie-Statistiken."""
        print(f"\nBatterie-Ladestand:")

        min_color = self._get_color(self.get_threshold_color(stats.battery_soc_min, 'battery_soc'))
        max_color = self._get_color(self.get_threshold_color(stats.battery_soc_max, 'battery_soc'))

        min_text = self._colorize(f"{stats.battery_soc_min:>5.1f}%", min_color)
        max_text = self._colorize(f"{stats.battery_soc_max:>5.1f}%", max_color)

        print(f"  Min: {min_text} | Max: {max_text}")

    def _display_metrics_section(self, stats: DailyStats) -> None:
        """Zeigt die Kennzahlen-Sektion der Tagesstatistik."""
        print("\nKennzahlen:")

        # Durchschnittlicher Autarkiegrad
        autarky_color = self._get_color(self.get_threshold_color(stats.autarky_avg, 'autarky'))
        print(self.format_value_with_color("Ø Autarkiegrad:", stats.autarky_avg, "%", autarky_color, decimals=1))

        # Energie-Autarkie
        energy_autarky_color = self._get_color(self.get_threshold_color(stats.self_sufficiency_rate, 'autarky'))
        print(self.format_value_with_color("Energie-Autarkie:", stats.self_sufficiency_rate, "%",
                                         energy_autarky_color, decimals=1))

        # Laufzeit
        print(f"\nLaufzeit: {stats.runtime_hours:.1f} Stunden")