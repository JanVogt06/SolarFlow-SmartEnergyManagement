"""
Tagesstatistik-Logging für den Fronius Solar Monitor.
"""

import csv
import logging
from datetime import datetime
from pathlib import Path

from solar_monitor.daily_stats import DailyStats
from solar_monitor.config import Config


class DailyStatsLogger:
    """Klasse zum Logging der Tagesstatistiken"""

    def __init__(self, config: Config):
        """
        Initialisiert den DailyStatsLogger mit Konfiguration.

        Args:
            config: Konfigurationsobjekt
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Erstelle Verzeichnisstruktur
        self.base_dir = Path(config.DATA_LOG_DIR)
        self.stats_dir = self.base_dir / config.DAILY_STATS_DIR
        self.stats_dir.mkdir(parents=True, exist_ok=True)

        # Dateiname basiert auf aktuellem Monat
        timestamp = datetime.now().strftime("%Y%m")
        base_name = config.DAILY_STATS_BASE_NAME.replace('.csv', '')
        self.filename = self.stats_dir / f"{base_name}_{timestamp}.csv"

        self.logger.info(f"Tagesstatistik-Log: {self.filename}")

        # Prüfe ob Datei existiert
        self.file_exists = self.filename.exists()

        # Header schreiben wenn neue Datei
        if not self.file_exists:
            self._write_header()

    def _write_header(self) -> None:
        """Schreibt die CSV-Header"""

        if self.config.CSV_USE_GERMAN_HEADERS:
            headers = [
                "Datum",
                "Laufzeit (h)",
                "PV-Produktion (kWh)",
                "Verbrauch (kWh)",
                "Eigenverbrauch (kWh)",
                "Einspeisung (kWh)",
                "Netzbezug (kWh)",
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
                "Energie-Autarkie (%)"
            ]
        else:
            headers = [
                "Date",
                "Runtime (h)",
                "PV Production (kWh)",
                "Consumption (kWh)",
                "Self Consumption (kWh)",
                "Feed-in (kWh)",
                "Grid Consumption (kWh)",
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
                "Energy Autarky (%)"
            ]

        try:
            with open(self.filename, 'w', newline='', encoding=self.config.CSV_ENCODING) as f:
                writer = csv.writer(f, delimiter=self.config.CSV_DELIMITER)
                writer.writerow(headers)

                # Session-Info
                writer.writerow([])
                session_info = f"# Monatsdatei erstellt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                writer.writerow([session_info])
                writer.writerow([])

            self.logger.info(f"Tagesstatistik-CSV erstellt: {self.filename.name}")

        except IOError as e:
            self.logger.error(f"Fehler beim Erstellen der Tagesstatistik-CSV: {e}")

    def log_daily_stats(self, stats: DailyStats) -> None:
        """
        Schreibt Tagesstatistiken in die CSV-Datei.

        Args:
            stats: Zu loggende Tagesstatistiken
        """
        # Prüfe ob neue Monatsdatei benötigt wird
        current_month = datetime.now().strftime("%Y%m")
        expected_month = stats.date.strftime("%Y%m")

        if current_month != expected_month:
            # Neue Monatsdatei erstellen
            timestamp = expected_month
            base_name = self.config.DAILY_STATS_BASE_NAME.replace('.csv', '')
            self.filename = self.stats_dir / f"{base_name}_{timestamp}.csv"
            self.file_exists = self.filename.exists()

            if not self.file_exists:
                self._write_header()

        # Formatiere Zahlen basierend auf Decimal Separator
        def format_number(value: float, decimals: int = 2) -> str:
            """Formatiert eine Zahl mit konfigurierbarem Dezimaltrennzeichen"""
            if value is None:
                return "-"

            formatted = f"{value:.{decimals}f}"

            if self.config.CSV_DECIMAL_SEPARATOR == ",":
                formatted = formatted.replace(".", ",")

            return formatted

        # Erstelle Datenzeile
        row = [
            stats.date.strftime('%Y-%m-%d'),
            format_number(stats.runtime_hours, 1),
            format_number(stats.pv_energy),
            format_number(stats.consumption_energy),
            format_number(stats.self_consumption_energy),
            format_number(stats.feed_in_energy),
            format_number(stats.grid_energy),
            format_number(stats.battery_charge_energy),
            format_number(stats.battery_discharge_energy),
            format_number(stats.pv_power_max, 0),
            format_number(stats.consumption_power_max, 0),
            format_number(stats.feed_in_power_max, 0),
            format_number(stats.grid_power_max, 0),
            format_number(stats.surplus_power_max, 0),
            format_number(stats.battery_soc_min, 1) if stats.battery_soc_min is not None else "-",
            format_number(stats.battery_soc_max, 1) if stats.battery_soc_max is not None else "-",
            format_number(stats.autarky_avg, 1),
            format_number(stats.self_sufficiency_rate, 1)
        ]

        try:
            with open(self.filename, 'a', newline='', encoding=self.config.CSV_ENCODING) as f:
                writer = csv.writer(f, delimiter=self.config.CSV_DELIMITER)
                writer.writerow(row)

            self.logger.info(f"Tagesstatistik gespeichert für {stats.date}")

        except IOError as e:
            self.logger.error(f"Fehler beim Schreiben der Tagesstatistik: {e}")