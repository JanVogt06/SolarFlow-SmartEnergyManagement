"""
Solar Data Logger für den Smart Energy Manager.
"""

from typing import List, Any

from .base_logger import BaseLogger
from solar_monitor.models import SolarData
from .database.database_manager import DatabaseManager


class SolarDataLogger(BaseLogger):
    """Logger für Solar-Leistungsdaten"""

    def __init__(self, config, db_manager: DatabaseManager):
        """
        Initialisiert den SolarDataLogger.

        Args:
            config: Konfigurationsobjekt
        """
        super().__init__(
            config=config,
            base_dir=config.DATA_LOG_DIR,
            sub_dir=config.SOLAR_DATA_DIR,
            base_filename=config.DATA_LOG_BASE_NAME,
            session_based=True
        )

        self.db_manager = db_manager

        # Datenbank-Manager initialisieren
        self.use_database = config.ENABLE_DATABASE
        self.db_manager = None
        if self.use_database:
            try:
                self.db_manager = DatabaseManager(self.config)
                self.logger.info("Datenbank-Integration aktiviert für SolarDataLogger")
            except Exception as e:
                self.logger.error(f"Fehler bei Datenbank-Initialisierung: {e}")
                self.use_database = False

    def _get_headers(self) -> List[str]:
        """Gibt die CSV-Header zurück"""
        if self.config.CSV_USE_GERMAN_HEADERS:
            headers = [
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
            headers = [
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

        return headers

    def _get_session_info(self) -> List[str]:
        """Gibt Session-spezifische Info-Zeilen zurück"""
        title = "Solar Data Log"
        kwargs = {
            "Fronius IP": self.config.FRONIUS_IP,
            "Update Interval": f"{self.config.UPDATE_INTERVAL}s",
            "Logging aktiviert": "Ja" if self.config.ENABLE_DATA_LOGGING else "Nein"
        }

        return self.csv_formatter.create_session_info(title, **kwargs)

    def _format_row(self, data: SolarData) -> List[Any]:
        """
        Formatiert SolarData für CSV-Export.

        Args:
            data: Zu loggende Solardaten

        Returns:
            Liste mit formatierten Werten
        """
        # Formatiere Zeitstempel
        timestamp = self.csv_formatter.format_timestamp(data.timestamp)

        # Formatiere alle Werte
        row = [
            timestamp,
            self.csv_formatter.format_number(data.pv_power),
            self.csv_formatter.format_number(data.grid_power, with_sign=True),
            self.csv_formatter.format_number(data.battery_power, with_sign=True)
                if data.battery_power != 0 else "0",
            self.csv_formatter.format_number(data.load_power),
            self.csv_formatter.format_number(data.battery_soc, decimals=1)
                if data.battery_soc is not None else "-",
            self.csv_formatter.format_number(data.total_production),
            self.csv_formatter.format_number(data.feed_in_power),
            self.csv_formatter.format_number(data.grid_consumption),
            self.csv_formatter.format_number(data.self_consumption),
            self.csv_formatter.format_number(data.autarky_rate, decimals=1),
            self.csv_formatter.format_number(data.surplus_power)
        ]

        return row

    def log(self, data: SolarData) -> bool:
        """
        Loggt Solardaten in CSV und Datenbank.

        Args:
            data: Zu loggende Solardaten

        Returns:
            True bei Erfolg
        """
        # CSV-Logging (Basis-Implementierung)
        csv_success = super().log(data)

        # Datenbank-Logging
        db_success = True
        if self.use_database and self.db_manager:
            db_success = self.db_manager.insert_solar_data(data)
            if not db_success:
                self.logger.warning("Fehler beim Schreiben in Datenbank")

        return csv_success and db_success