"""
Abstrakte Interfaces für das Logging-System.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Dict, Optional
from pathlib import Path
from datetime import datetime


class LogFormatter(ABC):
    """Abstrakte Basis für alle Formatter"""

    @abstractmethod
    def format(self, data: Any) -> Dict[str, Any]:
        """
        Formatiert Daten für Output.

        Args:
            data: Zu formatierende Daten

        Returns:
            Dictionary mit formatierten Daten
        """
        pass

    @abstractmethod
    def get_headers(self) -> List[str]:
        """
        Gibt die Header für die Ausgabe zurück.

        Returns:
            Liste mit Header-Strings
        """
        pass


class LogWriter(ABC):
    """Abstrakte Basis für alle Writer"""

    @abstractmethod
    def write(self, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Schreibt formatierte Daten.

        Args:
            data: Zu schreibende Daten
            metadata: Optionale Metadaten (z.B. Pfad, Timestamp)

        Returns:
            True bei Erfolg, False bei Fehler
        """
        pass

    @abstractmethod
    def write_header(self, headers: List[str], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Schreibt Header.

        Args:
            headers: Header-Liste
            metadata: Optionale Metadaten

        Returns:
            True bei Erfolg, False bei Fehler
        """
        pass

    @abstractmethod
    def flush(self) -> bool:
        """
        Leert Buffer und schreibt ausstehende Daten.

        Returns:
            True bei Erfolg
        """
        pass


class LogHandler(ABC):
    """Abstrakte Basis für alle Handler"""

    @abstractmethod
    def handle(self, log_type: str, data: Any) -> bool:
        """
        Verarbeitet Log-Daten.

        Args:
            log_type: Typ des Logs (solar, stats, device)
            data: Zu loggende Daten

        Returns:
            True bei Erfolg
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Schließt den Handler und gibt Ressourcen frei."""
        pass


class FileManager(ABC):
    """Abstrakte Basis für File-Management"""

    @abstractmethod
    def get_current_path(self, log_type: str) -> Path:
        """
        Gibt den aktuellen Pfad für einen Log-Typ zurück.

        Args:
            log_type: Typ des Logs

        Returns:
            Pfad zur Log-Datei
        """
        pass

    @abstractmethod
    def should_rotate(self, log_type: str) -> bool:
        """
        Prüft ob die Datei rotiert werden soll.

        Args:
            log_type: Typ des Logs

        Returns:
            True wenn Rotation nötig
        """
        pass

    @abstractmethod
    def rotate(self, log_type: str) -> Path:
        """
        Rotiert die Log-Datei.

        Args:
            log_type: Typ des Logs

        Returns:
            Neuer Dateipfad
        """
        pass