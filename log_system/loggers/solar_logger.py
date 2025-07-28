"""
Solar Logger - Orchestriert das Logging von Solar-Daten.
"""

import log_system
from typing import Any, Optional
from ..core.log_manager import LogManager
from ..core.log_entry import SolarLogEntry


class SolarLogger:
    """Logger für Solar-Daten"""

    def __init__(self, log_manager: LogManager):
        """
        Initialisiert den SolarLogger.

        Args:
            log_manager: Zentraler LogManager
        """
        self.log_manager = log_manager
        self.logger = log_system.getLogger(__name__)

    def log(self, solar_data: Any) -> bool:
        """
        Loggt Solar-Daten.

        Args:
            solar_data: SolarData-Objekt

        Returns:
            True bei Erfolg
        """
        try:
            # Erstelle Log-Entry
            entry = SolarLogEntry(solar_data)

            # Delegiere an LogManager
            return self.log_manager.log(entry)

        except Exception as e:
            self.logger.error(f"Fehler beim Logging von Solar-Daten: {e}")
            return False