"""
Anzeigeformatierung für den Fronius Solar Monitor - KORRIGIERT.
"""

from typing import Optional
from .models import SolarData
from .config import Config
from .daily_stats import DailyStats
from device_management import DeviceState


class DisplayFormatter:
    """Klasse für die Formatierung der Anzeige"""

    # ANSI Farb-Codes
    COLOR_GREEN = '\033[92m'
    COLOR_YELLOW = '\033[93m'
    COLOR_RED = '\033[91m'
    COLOR_BLUE = '\033[94m'
    COLOR_RESET = '\033[0m'

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

    def display_data_with_devices(self, data: SolarData, device_manager) -> None:
        """
        Zeigt die Daten mit Gerätestatus formatiert an.

        Args:
            data: Anzuzeigende Solardaten
            device_manager: DeviceManager mit Geräteinformationen
        """
        # Zeige normale Solar-Daten
        self.display_data(data)

        # Füge Geräte-Sektion hinzu
        print("\n" + "-" * 60)
        print("GERÄTESTEUERUNG:")
        print("-" * 60)

        # Berechne Gesamtverbrauch der gesteuerten Geräte
        controlled_consumption = device_manager.get_total_consumption()

        print(f"Gesteuerter Verbrauch:    {controlled_consumption:>10.0f} W")
        print(f"Aktueller Überschuss:     {data.surplus_power:>10.0f} W")

        # Optional: Zeige theoretischen Überschuss (wenn alle Geräte aus wären)
        theoretical_surplus = data.surplus_power + controlled_consumption
        if controlled_consumption > 0:
            print(f"Theoretischer Überschuss: {theoretical_surplus:>10.0f} W (wenn alle Geräte aus)")
        print()

        # Zeige Gerätestatus
        devices = device_manager.get_devices_by_priority()
        if not devices:
            print("Keine Geräte konfiguriert")
        else:
            print(f"{'Gerät':<20} {'Priorität':>9} {'Leistung':>10} {'Status':<12} {'Laufzeit heute':>14}")
            print("-" * 75)

            for device in devices:
                # Status-Farbe
                if device.state.value == "on":
                    status_color = self.COLOR_GREEN
                    status_text = "EIN"
                elif device.state.value == "blocked":
                    status_color = self.COLOR_YELLOW
                    status_text = "BLOCKIERT"
                else:
                    status_color = self.COLOR_RED
                    status_text = "AUS"

                total_runtime = device.get_current_runtime(data.timestamp)

                # Formatiere Laufzeit
                hours = total_runtime // 60
                minutes = total_runtime % 60
                runtime_str = f"{hours}h {minutes}m"

                # Zeige Zeile
                status_colored = f"{status_color}{status_text:<10}{self.COLOR_RESET if self.enable_colors else ''}"
                print(f"{device.name:<20} {device.priority:>9} {device.power_consumption:>9.0f}W "
                      f"{status_colored} {runtime_str:>14}")

                # Zeige zusätzliche Info bei Blockierung
                if device.state.value == "blocked":
                    if not device.can_run_today():
                        remaining = device.get_remaining_runtime()
                        print(f"  → Maximale Tageslaufzeit erreicht")
                    elif not device.is_time_allowed(data.timestamp):
                        print(f"  → Außerhalb der erlaubten Zeiten")

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
        Zeigt die Tagesstatistiken mit Kostenberechnung an.

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
        if stats.grid_energy_day > 0 or stats.grid_energy_night > 0:
            print(f"  → Tagtarif: {stats.grid_energy_day:>8.2f} kWh")
            print(f"  → Nachttarif: {stats.grid_energy_night:>8.2f} kWh")

        # Batterie wenn vorhanden
        if stats.battery_charge_energy > 0 or stats.battery_discharge_energy > 0:
            print(self.format_value("Batterie geladen:", stats.battery_charge_energy, "kWh", width=25, decimals=2))
            print(self.format_value("Batterie entladen:", stats.battery_discharge_energy, "kWh", width=25, decimals=2))

        # === NEUE KOSTENSEKTION ===
        print("\nKostenberechnung:")
        currency = self.config.CURRENCY_SYMBOL

        # Kosten formatieren mit Farbe
        cost_color = self.COLOR_RED if self.enable_colors else ""
        savings_color = self.COLOR_GREEN if self.enable_colors else ""

        print(
            f"{'Stromkosten (Netzbezug):':<25} {cost_color}{stats.cost_grid_consumption:>10.2f} {currency}{self.COLOR_RESET if self.enable_colors else ''}")
        print(
            f"{'Einspeisevergütung:':<25} {savings_color}{stats.revenue_feed_in:>10.2f} {currency}{self.COLOR_RESET if self.enable_colors else ''}")
        print(
            f"{'Eingesparte Kosten:':<25} {savings_color}{stats.cost_saved:>10.2f} {currency}{self.COLOR_RESET if self.enable_colors else ''}")
        print("-" * 60)

        benefit_color = self.COLOR_GREEN if stats.total_benefit > 0 else self.COLOR_RED
        print(
            f"{'GESAMTNUTZEN:':<25} {benefit_color if self.enable_colors else ''}{stats.total_benefit:>10.2f} {currency}{self.COLOR_RESET if self.enable_colors else ''}")

        # Vergleichswert
        print(f"\n{'Kosten ohne Solar:':<25} {stats.cost_without_solar:>10.2f} {currency}")

        # ROI
        if stats.cost_without_solar > 0:
            roi = (stats.total_benefit / stats.cost_without_solar) * 100
            roi_color = self.get_threshold_color(roi, 'autarky')  # Nutze Autarkie-Schwellwerte
            print(
                f"{'Einsparungsquote:':<25} {roi_color}{roi:>10.1f} %{self.COLOR_RESET if self.enable_colors else ''}")

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
        print(self.format_value_with_color("Energie-Autarkie:", stats.self_sufficiency_rate, "%", energy_autarky_color,
                                           decimals=1))

        print(f"\nLaufzeit: {stats.runtime_hours:.1f} Stunden")
        print("=" * 60)