"""
Zentraler Log-Manager für Koordination.
"""

import logging
from typing import Dict, List, Any, Optional
from .interfaces import LogFormatter, LogWriter, LogHandler
from .log_entry import LogEntry, LogType


class LogManager:
    """Zentrale Verwaltung aller Logging-Komponenten"""

    def __init__(self, config: Any):
        """
        Initialisiert den LogManager.

        Args:
            config: Konfigurationsobjekt
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Registries für Komponenten
        self.formatters: Dict[str, LogFormatter] = {}
        self.writers: Dict[str, LogWriter] = {}
        self.handlers: Dict[str, LogHandler] = {}

        # Mapping von LogType zu Komponenten
        self.type_mapping: Dict[LogType, Dict[str, Any]] = {
            LogType.SOLAR: {
                'formatter': 'solar',
                'writers': ['csv', 'database']
            },
            LogType.STATS: {
                'formatter': 'stats',
                'writers': ['csv', 'database']
            },
            LogType.DEVICE_EVENT: {
                'formatter': 'device_event',
                'writers': ['csv', 'database']
            },
            LogType.DEVICE_STATUS: {
                'formatter': 'device_status',
                'writers': ['csv', 'database']
            }
        }
    def register_formatter(self, name: str, formatter: LogFormatter) -> None:
        """
        Registriert einen Formatter.

        Args:
            name: Name des Formatters
            formatter: Formatter-Instanz
        """
        self.formatters[name] = formatter
        self.logger.debug(f"Formatter '{name}' registriert")

    def register_writer(self, name: str, writer: LogWriter) -> None:
        """
        Registriert einen Writer.

        Args:
            name: Name des Writers
            writer: Writer-Instanz
        """
        self.writers[name] = writer
        self.logger.debug(f"Writer '{name}' registriert")

    def register_handler(self, name: str, handler: LogHandler) -> None:
        """
        Registriert einen Handler.

        Args:
            name: Name des Handlers
            handler: Handler-Instanz
        """
        self.handlers[name] = handler
        self.logger.debug(f"Handler '{name}' registriert")

    def log(self, entry: LogEntry) -> bool:
        """
        Loggt einen Eintrag.

        Args:
            entry: Log-Eintrag

        Returns:
            True bei Erfolg
        """
        try:
            # Hole Mapping für diesen LogType
            mapping = self.type_mapping.get(entry.log_type)
            if not mapping:
                self.logger.error(f"Kein Mapping für LogType {entry.log_type}")
                return False

            # Hole Formatter
            formatter_name = mapping['formatter']
            formatter = self.formatters.get(formatter_name)
            if not formatter:
                self.logger.error(f"Formatter '{formatter_name}' nicht gefunden")
                return False

            # Formatiere Daten
            formatted_data = formatter.format(entry.data)

            # Schreibe mit allen konfigurierten Writers
            success = True
            for writer_name in mapping['writers']:
                writer = self.writers.get(writer_name)
                if not writer:
                    self.logger.warning(f"Writer '{writer_name}' nicht gefunden")
                    continue

                # Prüfe ob Writer für diesen LogType aktiviert ist
                if not self._is_writer_enabled(writer_name, entry.log_type):
                    continue

                # Schreibe Daten
                metadata = {
                    'log_type': entry.log_type.value,
                    'timestamp': entry.timestamp,
                    **entry.metadata
                }

                if not writer.write(formatted_data, metadata):
                    self.logger.error(f"Fehler beim Schreiben mit Writer '{writer_name}'")
                    success = False

            return success

        except Exception as e:
            self.logger.error(f"Fehler beim Logging: {e}", exc_info=True)
            return False

    def _is_writer_enabled(self, writer_name: str, log_type: LogType) -> bool:
        """
        Prüft ob ein Writer für einen LogType aktiviert ist.

        Args:
            writer_name: Name des Writers
            log_type: Typ des Logs

        Returns:
            True wenn aktiviert
        """
        # CSV-Writer Checks
        if writer_name == 'csv':
            if log_type == LogType.SOLAR:
                return self.config.logging.enable_data_logging
            elif log_type == LogType.STATS:
                return self.config.logging.enable_daily_stats_logging
            elif log_type in [LogType.DEVICE_EVENT, LogType.DEVICE_STATUS]:
                return self.config.logging.enable_device_logging

        # Database-Writer Check
        elif writer_name == 'database':
            return self.config.database.enable_database

        return True

    def flush_all(self) -> None:
        """Leert alle Writer-Buffer."""
        for name, writer in self.writers.items():
            try:
                writer.flush()
            except Exception as e:
                self.logger.error(f"Fehler beim Flush von Writer '{name}': {e}")

    def close_all(self) -> None:
        """Schließt alle Handler und Writer."""
        # Erst alle Writer flushen
        self.flush_all()

        # Dann Handler schließen
        for name, handler in self.handlers.items():
            try:
                handler.close()
            except Exception as e:
                self.logger.error(f"Fehler beim Schließen von Handler '{name}': {e}")

        self.logger.info("LogManager geschlossen")