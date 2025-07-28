"""
Abstrakte Basisklasse für alle Logger im Smart Energy Manager.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any

from utils.csv_utils import CSVFormatter, CSVWriter


class BaseLogger(ABC):
    """Abstrakte Basisklasse für alle CSV-Logger"""

    def __init__(self, config: Any, base_dir: str, sub_dir: str,
                 base_filename: str, session_based: bool = True) -> None:
        """
        Initialisiert den BaseLogger.

        Args:
            config: Konfigurationsobjekt
            base_dir: Basis-Verzeichnis (z.B. "Datalogs")
            sub_dir: Unterverzeichnis (z.B. "Solardata")
            base_filename: Basis-Dateiname ohne Endung (z.B. "solar_data")
            session_based: Ob pro Session eine neue Datei erstellt wird
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

        # CSV-Utilities
        self.csv_formatter = CSVFormatter(config)
        self.csv_writer = CSVWriter(config)

        # Verzeichnisstruktur
        self.base_dir = Path(config.directories.data_log_dir if hasattr(config, 'DATA_LOG_DIR') else base_dir)
        self.log_dir = self.base_dir / sub_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Dateiname generieren
        self.base_filename = base_filename.replace('.csv', '')
        self.session_based = session_based
        self.filepath = self._generate_filepath()

        # Initial-Setup
        self._initialized = False
        self._initialize()

    def _generate_filepath(self) -> Path:
        """
        Generiert den Dateipfad basierend auf Konfiguration.

        Returns:
            Pfad zur Log-Datei
        """
        if self.session_based:
            # Eine Datei pro Session mit Timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.base_filename}_{timestamp}.csv"
        else:
            # Eine Datei pro Tag/Monat
            timestamp = datetime.now().strftime(self._get_file_timestamp_format())
            filename = f"{self.base_filename}_{timestamp}.csv"

        return self.log_dir / filename

    def _get_file_timestamp_format(self) -> str:
        """
        Gibt das Timestamp-Format für Dateinamen zurück.

        Kann von Subklassen überschrieben werden.

        Returns:
            strftime Format-String
        """
        return "%Y%m%d"  # Standard: Eine Datei pro Tag

    def _initialize(self) -> None:
        """Initialisiert die Log-Datei"""
        if not self.csv_writer.file_exists(self.filepath):
            headers = self._get_headers()
            info_lines = self._get_session_info()

            if self.csv_writer.write_header(self.filepath, headers, info_lines):
                self._initialized = True
                self.logger.info(f"Log-Datei initialisiert: {self.filepath}")
            else:
                self.logger.error(f"Fehler bei der Initialisierung: {self.filepath}")
        else:
            self._initialized = True
            self.logger.debug(f"Log-Datei existiert bereits: {self.filepath}")

    def _check_new_file_needed(self) -> bool:
        """
        Prüft ob eine neue Datei benötigt wird (z.B. bei Tageswechsel).

        Returns:
            True wenn neue Datei benötigt wird
        """
        if self.session_based:
            return False  # Session-basierte Dateien wechseln nie

        # Prüfe ob aktueller Timestamp vom Dateinamen abweicht
        current_timestamp = datetime.now().strftime(self._get_file_timestamp_format())
        file_timestamp = self.filepath.stem.split('_')[-1]

        return current_timestamp != file_timestamp

    def _rotate_file_if_needed(self) -> None:
        """Rotiert die Log-Datei wenn nötig (z.B. bei Tageswechsel)"""
        if self._check_new_file_needed():
            self.filepath = self._generate_filepath()
            self._initialized = False
            self._initialize()
            self.logger.info(f"Neue Log-Datei erstellt: {self.filepath}")

    @abstractmethod
    def _get_headers(self) -> List[str]:
        """
        Gibt die CSV-Header zurück.

        Muss von Subklassen implementiert werden.

        Returns:
            Liste mit Header-Spalten
        """
        pass

    def _get_session_info(self) -> List[str]:
        """
        Gibt Session-Info-Zeilen zurück.

        Kann von Subklassen überschrieben werden.

        Returns:
            Liste mit Info-Zeilen
        """
        title = f"{self.__class__.__name__} Log"
        kwargs = {
            "Logger": self.__class__.__name__,
            "Verzeichnis": str(self.log_dir),
            "Session-basiert": "Ja" if self.session_based else "Nein"
        }

        return self.csv_formatter.create_session_info(title, **kwargs)

    @abstractmethod
    def _format_row(self, data: Any) -> List[Any]:
        """
        Formatiert Daten für eine CSV-Zeile.

        Muss von Subklassen implementiert werden.

        Args:
            data: Zu formatierende Daten

        Returns:
            Liste mit formatierten Werten für CSV
        """
        pass

    def log(self, data: Any) -> bool:
        """
        Haupt-Log-Methode für alle Logger.

        Args:
            data: Zu loggende Daten

        Returns:
            True bei Erfolg, False bei Fehler
        """
        if not self._initialized:
            self.logger.error("Logger nicht initialisiert")
            return False

        # Prüfe ob neue Datei benötigt wird
        self._rotate_file_if_needed()

        # Formatiere Daten
        try:
            row = self._format_row(data)
        except Exception as e:
            self.logger.error(f"Fehler beim Formatieren der Daten: {e}")
            return False

        # Schreibe Zeile
        return self.csv_writer.append_row(self.filepath, row)

class MultiFileLogger(BaseLogger):
    """
    Erweiterte Basisklasse für Logger mit mehreren Dateien.

    Z.B. für DeviceLogger mit Events und Status in separaten Dateien.
    """

    def __init__(self, config: Any, base_dir: str, sub_dir: str) -> None:
        """
        Initialisiert den MultiFileLogger.

        Args:
            config: Konfigurationsobjekt
            base_dir: Basis-Verzeichnis
            sub_dir: Unterverzeichnis
        """
        # Initialisiere ohne automatische Datei-Erstellung
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.csv_formatter = CSVFormatter(config)
        self.csv_writer = CSVWriter(config)

        # Verzeichnisstruktur
        self.base_dir = Path(config.directories.data_log_dir if hasattr(config, 'DATA_LOG_DIR') else base_dir)
        self.log_dir = self.base_dir / sub_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Dictionary für mehrere Dateien
        self.files: Dict[str, Path] = {}
        self._initialized_files: Dict[str, bool] = {}

    def add_file(self, file_key: str, base_filename: str,
                 session_based: bool = True,
                 timestamp_format: str = "%Y%m%d") -> None:
        """
        Fügt eine neue Log-Datei hinzu.

        Args:
            file_key: Eindeutiger Schlüssel für die Datei
            base_filename: Basis-Dateiname
            session_based: Ob Session-basiert
            timestamp_format: Format für Zeitstempel
        """
        base_filename = base_filename.replace('.csv', '')

        if session_based:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        else:
            timestamp = datetime.now().strftime(timestamp_format)

        filename = f"{base_filename}_{timestamp}.csv"
        self.files[file_key] = self.log_dir / filename
        self._initialized_files[file_key] = False

    def initialize_file(self, file_key: str, headers: List[str],
                       info_lines: Optional[List[str]] = None) -> bool:
        """
        Initialisiert eine spezifische Log-Datei.

        Args:
            file_key: Schlüssel der Datei
            headers: CSV-Header
            info_lines: Info-Zeilen

        Returns:
            True bei Erfolg
        """
        if file_key not in self.files:
            self.logger.error(f"Unbekannter Datei-Schlüssel: {file_key}")
            return False

        filepath = self.files[file_key]

        if not self.csv_writer.file_exists(filepath):
            if self.csv_writer.write_header(filepath, headers, info_lines):
                self._initialized_files[file_key] = True
                self.logger.info(f"Log-Datei initialisiert: {filepath}")
                return True
        else:
            self._initialized_files[file_key] = True
            return True

        return False

    def log_to_file(self, file_key: str, row: List[Any]) -> bool:
        """
        Schreibt Daten in eine spezifische Datei.

        Args:
            file_key: Schlüssel der Datei
            row: Zu schreibende Zeile

        Returns:
            True bei Erfolg
        """
        if file_key not in self.files:
            self.logger.error(f"Unbekannter Datei-Schlüssel: {file_key}")
            return False

        if not self._initialized_files.get(file_key, False):
            self.logger.error(f"Datei nicht initialisiert: {file_key}")
            return False

        return self.csv_writer.append_row(self.files[file_key], row)

    # Abstrakte Methoden für Kompatibilität
    def _get_headers(self) -> List[str]:
        """Nicht verwendet in MultiFileLogger"""
        return []

    def _format_row(self, data: Any) -> List[Any]:
        """Nicht verwendet in MultiFileLogger"""
        return []