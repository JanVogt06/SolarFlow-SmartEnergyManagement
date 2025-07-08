"""
Daily Stats Logger für den Smart Energy Manager.
"""

from typing import List, Any

from .base_logger import BaseLogger
from solar_monitor.daily_stats import DailyStats
from .database.database_manager import DatabaseManager

class DailyStatsLogger(BaseLogger):
    """Logger für Tagesstatistiken"""

    def __init__(self, config):
        """
        Initialisiert den DailyStatsLogger.

        Args:
            config: Konfigurationsobjekt
            use_database: Ob Daten auch in die Datenbank geschrieben werden sollen
        """
        super().__init__(
            config=config,
            base_dir=config.DATA_LOG_DIR,
            sub_dir=config.DAILY_STATS_DIR,
            base_filename=config.DAILY_STATS_BASE_NAME,
            session_based=False
        )

        # Datenbank-Manager initialisieren
        self.use_database = config.ENABLE_DATABASE
        self.db_manager = None
        if self.use_database:
            try:
                self.db_manager = DatabaseManager(self.config)
                self.logger.info("Datenbank-Integration aktiviert für DailyStatsLogger")
            except Exception as e:
                self.logger.error(f"Fehler bei Datenbank-Initialisierung: {e}")
                self.use_database = False

    def _get_file_timestamp_format(self) -> str:
        """Eine Datei pro Monat"""
        return "%Y%m"

    def _get_headers(self) -> List[str]:
        """Gibt die CSV-Header zurück"""
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

        return headers

    def _get_session_info(self) -> List[str]:
        """Gibt Session-spezifische Info-Zeilen zurück"""
        title = "Tagesstatistik Log"
        kwargs = {
            "Monatsdatei": "Ja",
            "Statistik-Intervall": f"{self.config.DAILY_STATS_INTERVAL}s"
        }

        return self.csv_formatter.create_session_info(title, **kwargs)

    def _format_row(self, stats: DailyStats) -> List[Any]:
        """
        Formatiert DailyStats für CSV-Export.

        Args:
            stats: Zu loggende Tagesstatistiken

        Returns:
            Liste mit formatierten Werten
        """
        # Formatiere Datum
        date_str = stats.date.strftime('%Y-%m-%d')

        # Formatiere alle Werte
        row = [
            date_str,
            self.csv_formatter.format_number(stats.runtime_hours, decimals=1),
            self.csv_formatter.format_number(stats.pv_energy, decimals=2),
            self.csv_formatter.format_number(stats.consumption_energy, decimals=2),
            self.csv_formatter.format_number(stats.self_consumption_energy, decimals=2),
            self.csv_formatter.format_number(stats.feed_in_energy, decimals=2),
            self.csv_formatter.format_number(stats.grid_energy, decimals=2),
            self.csv_formatter.format_number(stats.battery_charge_energy, decimals=2),
            self.csv_formatter.format_number(stats.battery_discharge_energy, decimals=2),
            self.csv_formatter.format_number(stats.pv_power_max),
            self.csv_formatter.format_number(stats.consumption_power_max),
            self.csv_formatter.format_number(stats.feed_in_power_max),
            self.csv_formatter.format_number(stats.grid_power_max),
            self.csv_formatter.format_number(stats.surplus_power_max),
            self.csv_formatter.format_number(stats.battery_soc_min, decimals=1)
                if stats.battery_soc_min is not None else "-",
            self.csv_formatter.format_number(stats.battery_soc_max, decimals=1)
                if stats.battery_soc_max is not None else "-",
            self.csv_formatter.format_number(stats.autarky_avg, decimals=1),
            self.csv_formatter.format_number(stats.self_sufficiency_rate, decimals=1)
        ]

        return row

    def log(self, stats: DailyStats) -> bool:
        """
        Loggt Tagesstatistiken in CSV und Datenbank.

        Args:
            stats: Zu loggende Tagesstatistiken

        Returns:
            True bei Erfolg
        """
        # CSV-Logging
        csv_success = super().log(stats)

        # Datenbank-Logging
        db_success = True
        if self.use_database and self.db_manager:
            db_success = self.db_manager.insert_daily_stats(stats)
            if not db_success:
                self.logger.warning("Fehler beim Schreiben in Datenbank")

        return csv_success and db_success