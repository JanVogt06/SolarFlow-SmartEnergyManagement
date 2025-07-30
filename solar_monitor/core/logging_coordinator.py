"""
Logging-Koordination für den Solar Monitor.
"""

import logging
from typing import Any
from log_system import LogManager, SolarLogger, StatsLogger, DeviceLogger
from log_system.formatters import (
    SolarFormatter, StatsFormatter,
    DeviceEventFormatter, DeviceStatusFormatter
)
from log_system.writers import CSVWriter, DatabaseWriter
from log_system.handlers import FileHandler


class LoggingCoordinator:
    """Koordiniert das gesamte Logging-System"""

    def __init__(self, config: Any):
        """
        Initialisiert den LoggingCoordinator.

        Args:
            config: Konfigurationsobjekt
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialisiere Logging-System
        self._init_logging_system()

    def _init_logging_system(self) -> None:
        """Initialisiert das Logging-System"""
        # LogManager erstellen
        self.log_manager = LogManager(self.config)

        # FileHandler für Pfadverwaltung
        self.file_handler = FileHandler(self.config)

        # Formatter registrieren
        self.log_manager.register_formatter('solar', SolarFormatter(self.config))
        self.log_manager.register_formatter('stats', StatsFormatter(self.config))
        self.log_manager.register_formatter('device_event', DeviceEventFormatter(self.config))
        self.log_manager.register_formatter('device_status', DeviceStatusFormatter(self.config))

        # Writer registrieren
        self.log_manager.register_writer('csv', CSVWriter(self.config, self.file_handler))
        if self.config.database.enable_database:
            self.log_manager.register_writer('database', DatabaseWriter(self.config))

        # High-Level Logger erstellen
        self.solar_logger = SolarLogger(self.log_manager)
        self.stats_logger = StatsLogger(self.log_manager)
        self.device_logger = DeviceLogger(self.log_manager)

        self.logger.info("Logging-System initialisiert")

    def setup_system_logging(self) -> None:
        """Konfiguriert das System-Logging"""
        # Root Logger konfigurieren
        root_logger = logging.getLogger()
        root_logger.setLevel(self.config.logging.log_level)

        # Entferne alle bestehenden Handler
        root_logger.handlers = []

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(self.config.logging.log_level)
        root_logger.addHandler(console_handler)

        # File Handler
        if self.config.logging.log_file:
            try:
                file_handler = logging.FileHandler(self.config.logging.log_file)
                file_handler.setFormatter(formatter)
                file_handler.setLevel(self.config.logging.log_level)
                root_logger.addHandler(file_handler)
            except IOError as e:
                print(f"Warnung: Konnte Log-Datei nicht erstellen: {e}")

    def log_solar_data(self, data: Any) -> bool:
        """
        Loggt Solar-Daten.

        Args:
            data: SolarData-Objekt

        Returns:
            True bei Erfolg
        """
        if self.config.logging.enable_data_logging:
            return self.solar_logger.log(data)
        return True

    def log_daily_stats(self, stats: Any) -> bool:
        """
        Loggt Tagesstatistiken.

        Args:
            stats: DailyStats-Objekt

        Returns:
            True bei Erfolg
        """
        return self.stats_logger.log(stats)

    def close(self) -> None:
        """Schließt das Logging-System sauber"""
        self.log_manager.close_all()
        self.logger.info("Logging-System geschlossen")

    def log_startup_info(self, has_device_control: bool) -> None:
        """Loggt Informationen beim Start"""
        self.logger.info("Monitor gestartet. Drücke Ctrl+C zum Beenden.")

        if self.config.display.show_daily_stats:
            interval_min = self.config.timing.daily_stats_interval / 60
            self.logger.info(f"Tagesstatistiken werden alle {interval_min:.0f} Minuten angezeigt.")

        if has_device_control:
            self.logger.info("Intelligente Gerätesteuerung ist aktiviert.")
            if self.config.logging.enable_device_logging:
                self.logger.info(
                    f"Geräte-Logging aktiviert (Events: {self.config.logging.device_log_events}, "
                    f"Status: {self.config.logging.device_log_status})"
                )