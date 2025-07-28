"""
Basis-Writer für das Logging-System.
"""

import log_system
from typing import Dict, Any, Optional, List
from ..core.interfaces import LogWriter


class BaseWriter(LogWriter):
    """Basis-Implementierung für alle Writer"""

    def __init__(self, config: Any):
        """
        Initialisiert den Writer.

        Args:
            config: Konfigurationsobjekt
        """
        self.config = config
        self.logger = log_system.getLogger(self.__class__.__name__)
        self._buffer: List[Dict[str, Any]] = []
        self._buffer_size = 10  # Anzahl Einträge bevor automatischer Flush

    def write(self, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Basis-Implementierung fügt zu Buffer hinzu.

        Args:
            data: Zu schreibende Daten
            metadata: Optionale Metadaten

        Returns:
            True bei Erfolg
        """
        try:
            self._buffer.append({
                'data': data,
                'metadata': metadata or {}
            })

            # Auto-flush wenn Buffer voll
            if len(self._buffer) >= self._buffer_size:
                return self.flush()

            return True

        except Exception as e:
            self.logger.error(f"Fehler beim Schreiben: {e}")
            return False

    def flush(self) -> bool:
        """
        Leert den Buffer.

        Muss von Subklassen überschrieben werden.

        Returns:
            True bei Erfolg
        """
        # Subklassen müssen diese Methode implementieren
        self._buffer.clear()
        return True

    def write_header(self, headers: List[str], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Schreibt Header.

        Basis-Implementierung tut nichts.

        Args:
            headers: Header-Liste
            metadata: Optionale Metadaten

        Returns:
            True
        """
        return True