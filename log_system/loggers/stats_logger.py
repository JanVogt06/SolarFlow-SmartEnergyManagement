"""
Stats Logger - Orchestriert das Logging von Tagesstatistiken.
"""

import log_system
from typing import Any
from ..core.log_manager import LogManager
from ..core.log_entry import StatsLogEntry


class StatsLogger:
    """Logger für Tagesstatistiken"""

    def __init__(self, log_manager: LogManager):
        """
        Initialisiert den StatsLogger.

        Args:
            log_manager: Zentraler LogManager
        """
        self.log_manager = log_manager
        self.logger = log_system.getLogger(__name__)

    def log(self, daily_stats: Any) -> bool:
        """
        Loggt Tagesstatistiken.

        Args:
            daily_stats: DailyStats-Objekt

        Returns:
            True bei Erfolg
        """
        try:
            # Erstelle Log-Entry
            entry = StatsLogEntry(daily_stats)

            # Delegiere an LogManager
            return self.log_manager.log(entry)

        except Exception as e:
            self.logger.error(f"Fehler beim Logging von Tagesstatistiken: {e}")
            return False