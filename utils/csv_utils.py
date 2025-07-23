"""
CSV Utilities für den Smart Energy Manager.
"""

import csv
import logging
from pathlib import Path
from typing import List, Any, Optional
from datetime import datetime


class CSVFormatter:
    """Zentrale Klasse für CSV-Formatierung"""

    def __init__(self, config):
        """
        Initialisiert den CSVFormatter.

        Args:
            config: Konfigurationsobjekt mit CSV-Einstellungen
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

    def format_number(self, value: Optional[float], decimals: int = 0,
                      with_sign: bool = False) -> str:
        """
        Formatiert eine Zahl für CSV-Export.

        Args:
            value: Zu formatierender Wert
            decimals: Anzahl Nachkommastellen
            with_sign: Ob Vorzeichen immer angezeigt werden soll

        Returns:
            Formatierter String
        """
        if value is None:
            return "-"

        try:
            if decimals == 0:
                formatted = f"{value:+.0f}" if with_sign else f"{value:.0f}"
            else:
                formatted = f"{value:+.{decimals}f}" if with_sign else f"{value:.{decimals}f}"

            # Dezimaltrennzeichen anpassen
            if self.config.csv.decimal_separator == ",":
                formatted = formatted.replace(".", ",")

            return formatted
        except (ValueError, TypeError):
            return "-"

    def format_timestamp(self, timestamp: datetime,
                         format_string: str = '%Y-%m-%d %H:%M:%S') -> str:
        """
        Formatiert einen Zeitstempel für CSV.

        Args:
            timestamp: Zu formatierender Zeitstempel
            format_string: Format-String für strftime

        Returns:
            Formatierter Zeitstempel
        """
        return timestamp.strftime(format_string)

    def create_session_info(self, title: str, **kwargs) -> List[str]:
        """
        Erstellt Session-Info-Zeilen für CSV-Header.

        Args:
            title: Titel der Session-Info
            **kwargs: Zusätzliche Info-Felder

        Returns:
            Liste mit Info-Zeilen
        """
        info_lines = [
            f"# {title}",
            f"# Erstellt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"# CSV-Format: Delimiter='{self.config.csv.delimiter}', "
            f"Decimal='{self.config.csv.decimal_separator}', "
            f"Encoding='{self.config.csv.encoding}'"
        ]

        # Zusätzliche Infos
        for key, value in kwargs.items():
            info_lines.append(f"# {key}: {value}")

        return info_lines


class CSVWriter:
    """Thread-safe CSV Writer"""

    def __init__(self, config):
        """
        Initialisiert den CSVWriter.

        Args:
            config: Konfigurationsobjekt
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._file_locks = {}  # Für Thread-Safety

    def write_header(self, filepath: Path, headers: List[str],
                     info_lines: Optional[List[str]] = None) -> bool:
        """
        Schreibt CSV-Header in eine neue Datei.

        Args:
            filepath: Pfad zur CSV-Datei
            headers: Liste mit Header-Spalten
            info_lines: Optionale Info-Zeilen

        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            # Erstelle Verzeichnis falls nötig
            filepath.parent.mkdir(parents=True, exist_ok=True)

            with open(filepath, 'w', newline='',
                      encoding=self.config.csv.encoding) as f:
                writer = csv.writer(f, delimiter=self.config.csv.delimiter)

                # Header schreiben
                writer.writerow(headers)

                # Info-Zeile wenn konfiguriert
                if self.config.csv.include_info_row and hasattr(self.config, 'CSV_INFO_ROW'):
                    writer.writerow(self.config.CSV_INFO_ROW)

                # Session-Info
                if info_lines:
                    writer.writerow([])  # Leerzeile
                    for line in info_lines:
                        writer.writerow([line])
                    writer.writerow([])  # Leerzeile nach Info

            self.logger.info(f"CSV-Header geschrieben: {filepath.name}")
            return True

        except IOError as e:
            self.logger.error(f"Fehler beim Schreiben der CSV-Header: {e}")
            return False

    def append_row(self, filepath: Path, row: List[Any]) -> bool:
        """
        Fügt eine Zeile an eine CSV-Datei an.

        Args:
            filepath: Pfad zur CSV-Datei
            row: Zu schreibende Datenzeile

        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            with open(filepath, 'a', newline='',
                      encoding=self.config.csv.encoding) as f:
                writer = csv.writer(f, delimiter=self.config.csv.delimiter)
                writer.writerow(row)
            return True

        except IOError as e:
            self.logger.error(f"Fehler beim Schreiben in CSV: {e}")
            return False

    def file_exists(self, filepath: Path) -> bool:
        """
        Prüft ob eine Datei existiert.

        Args:
            filepath: Zu prüfender Dateipfad

        Returns:
            True wenn Datei existiert
        """
        return filepath.exists()

    def create_backup(self, filepath: Path) -> Optional[Path]:
        """
        Erstellt ein Backup einer Datei.

        Args:
            filepath: Zu sichernde Datei

        Returns:
            Pfad zur Backup-Datei oder None bei Fehler
        """
        if not filepath.exists():
            return None

        backup_path = filepath.with_suffix(filepath.suffix + '.bak')

        try:
            import shutil
            shutil.copy2(filepath, backup_path)
            self.logger.debug(f"Backup erstellt: {backup_path}")
            return backup_path
        except IOError as e:
            self.logger.error(f"Fehler beim Erstellen des Backups: {e}")
            return None