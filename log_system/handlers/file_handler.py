"""
File Handler für das Logging-System.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from ..core.interfaces import FileManager


class FileHandler(FileManager):
    """Verwaltet Dateipfade ohne Rotation"""

    def __init__(self, config: Any):
        """
        Initialisiert den FileHandler.

        Args:
            config: Konfigurationsobjekt
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        self.base_dir = Path(config.directories.data_log_dir)

        self.type_config = {
            'solar': {
                'sub_dir': config.directories.solar_data_dir,
                'base_name': config.directories.data_log_base_name,
                'session_based': False
            },
            'stats': {
                'sub_dir': config.directories.daily_stats_dir,
                'base_name': config.directories.daily_stats_base_name,
                'session_based': False
            },
            'device_event': {
                'sub_dir': config.directories.device_log_dir,
                'base_name': config.directories.device_events_base_name,
                'session_based': False
            },
            'device_status': {
                'sub_dir': config.directories.device_log_dir,
                'base_name': config.directories.device_status_base_name,
                'session_based': False
            }
        }

        self._current_paths: Dict[tuple, Path] = {}

        self._session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def get_current_path(self, log_type: str) -> Path:
        """
        Gibt den aktuellen Pfad für einen Log-Typ zurück.

        Args:
            log_type: Typ des Logs

        Returns:
            Pfad zur Log-Datei
        """
        config = self.type_config.get(log_type)
        if not config:
            raise ValueError(f"Unbekannter log_type: {log_type}")

        if config['session_based']:
            time_key = self._session_timestamp
        else:
            time_key = datetime.now().strftime("%Y%m%d")

        cache_key = (log_type, time_key)

        if cache_key in self._current_paths:
            return self._current_paths[cache_key]

        log_dir = self.base_dir / config['sub_dir']
        log_dir.mkdir(parents=True, exist_ok=True)

        base_name = config['base_name'].replace('.csv', '')
        filename = f"{base_name}_{time_key}.csv"
        path = log_dir / filename

        stale_keys = [k for k in self._current_paths if k[0] == log_type and k != cache_key]
        for k in stale_keys:
            del self._current_paths[k]

        self._current_paths[cache_key] = path

        return path

    def should_rotate(self, log_type: str) -> bool:
        """
        Rotation ist deaktiviert.

        Args:
            log_type: Typ des Logs

        Returns:
            Immer False (keine Rotation)
        """
        return False

    def rotate(self, log_type: str) -> Path:
        """
        Rotation ist deaktiviert, gibt einfach den aktuellen Pfad zurück.

        Args:
            log_type: Typ des Logs

        Returns:
            Aktueller Dateipfad
        """
        return self.get_current_path(log_type)