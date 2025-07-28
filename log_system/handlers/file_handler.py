"""
File Handler für das Logging-System.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Any
from ..core.interfaces import FileManager


class FileHandler(FileManager):
    """Verwaltet Dateipfade und Rotation"""

    def __init__(self, config: Any):
        """
        Initialisiert den FileHandler.

        Args:
            config: Konfigurationsobjekt
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Basis-Verzeichnisse
        self.base_dir = Path(config.directories.data_log_dir)

        # Mapping von log_type zu Konfiguration
        self.type_config = {
            'solar': {
                'sub_dir': config.directories.solar_data_dir,
                'base_name': config.directories.data_log_base_name,
                'session_based': True,
                'rotation': None
            },
            'stats': {
                'sub_dir': config.directories.daily_stats_dir,
                'base_name': config.directories.daily_stats_base_name,
                'session_based': False,
                'rotation': 'monthly'
            },
            'device_event': {
                'sub_dir': config.directories.device_log_dir,
                'base_name': config.directories.device_events_base_name,
                'session_based': True,
                'rotation': None
            },
            'device_status': {
                'sub_dir': config.directories.device_log_dir,
                'base_name': config.directories.device_status_base_name,
                'session_based': False,
                'rotation': 'daily'
            }
        }

        # Cache für aktuelle Pfade
        self._current_paths: Dict[str, Path] = {}
        self._path_dates: Dict[str, datetime] = {}

        # Session-Zeitstempel für session-basierte Dateien
        self._session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def get_current_path(self, log_type: str) -> Path:
        """
        Gibt den aktuellen Pfad für einen Log-Typ zurück.

        Args:
            log_type: Typ des Logs

        Returns:
            Pfad zur Log-Datei
        """
        # Prüfe Cache
        if log_type in self._current_paths:
            # Prüfe ob Rotation nötig
            if not self.should_rotate(log_type):
                return self._current_paths[log_type]

        # Generiere neuen Pfad
        config = self.type_config.get(log_type)
        if not config:
            raise ValueError(f"Unbekannter log_type: {log_type}")

        # Verzeichnis
        log_dir = self.base_dir / config['sub_dir']
        log_dir.mkdir(parents=True, exist_ok=True)

        # Dateiname
        base_name = config['base_name'].replace('.csv', '')

        if config['session_based']:
            # Session-basiert: Ein Mal pro Programmlauf
            filename = f"{base_name}_{self._session_timestamp}.csv"
        else:
            # Zeit-basiert: Nach Rotation-Schema
            timestamp = self._get_rotation_timestamp(config['rotation'])
            filename = f"{base_name}_{timestamp}.csv"

        path = log_dir / filename

        # Cache aktualisieren
        self._current_paths[log_type] = path
        self._path_dates[log_type] = datetime.now()

        return path

    def should_rotate(self, log_type: str) -> bool:
        """
        Prüft ob die Datei rotiert werden soll.

        Args:
            log_type: Typ des Logs

        Returns:
            True wenn Rotation nötig
        """
        config = self.type_config.get(log_type)
        if not config:
            return False

        # Session-basierte Dateien rotieren nie
        if config['session_based']:
            return False

        # Kein Cache-Eintrag = neue Datei nötig
        if log_type not in self._path_dates:
            return True

        # Prüfe Rotation
        rotation = config['rotation']
        if not rotation:
            return False

        last_date = self._path_dates[log_type]
        now = datetime.now()

        if rotation == 'daily':
            return last_date.date() != now.date()
        elif rotation == 'monthly':
            return (last_date.year, last_date.month) != (now.year, now.month)
        elif rotation == 'yearly':
            return last_date.year != now.year

        return False

    def rotate(self, log_type: str) -> Path:
        """
        Rotiert die Log-Datei.

        Args:
            log_type: Typ des Logs

        Returns:
            Neuer Dateipfad
        """
        # Entferne aus Cache
        self._current_paths.pop(log_type, None)
        self._path_dates.pop(log_type, None)

        # Generiere neuen Pfad
        new_path = self.get_current_path(log_type)

        self.logger.info(f"Log-Datei rotiert für {log_type}: {new_path.name}")

        return new_path

    def _get_rotation_timestamp(self, rotation: Optional[str]) -> str:
        """
        Gibt den Timestamp für die Rotation zurück.

        Args:
            rotation: Rotation-Schema

        Returns:
            Formatierter Timestamp
        """
        now = datetime.now()

        if rotation == 'daily':
            return now.strftime("%Y%m%d")
        elif rotation == 'monthly':
            return now.strftime("%Y%m")
        elif rotation == 'yearly':
            return now.strftime("%Y")
        else:
            # Fallback: Session-Timestamp
            return self._session_timestamp

    def cleanup_old_files(self, days_to_keep: int = 30) -> None:
        """
        Löscht alte Log-Dateien.

        Args:
            days_to_keep: Anzahl Tage die behalten werden sollen
        """
        cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)

        for log_type, config in self.type_config.items():
            log_dir = self.base_dir / config['sub_dir']
            if not log_dir.exists():
                continue

            # Suche alte Dateien
            pattern = f"{config['base_name']}*.csv"
            for file_path in log_dir.glob(pattern):
                if file_path.stat().st_mtime < cutoff_date:
                    try:
                        file_path.unlink()
                        self.logger.info(f"Alte Datei gelöscht: {file_path.name}")
                    except Exception as e:
                        self.logger.error(f"Fehler beim Löschen von {file_path.name}: {e}")