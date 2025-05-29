"""
Daten-Logging für den Fronius Solar Monitor.
"""

import csv
import logging
import os
from datetime import datetime
from typing import List, Optional

from .models import SolarData


class DataLogger:
    """Klasse zum Logging der Solardaten"""

    def __init__(self, filename: str = "solar_data.csv"):
        """
        Initialisiert den DataLogger.

        Args:
            filename: Name der CSV-Datei
        """
        self.filename = filename
        self.logger = logging.getLogger(__name__)
        self._ensure_header()

    def _ensure_header(self) -> None:
        """Stellt sicher, dass die CSV-Header existieren"""
        if not os.path.exists(self.filename):
            self._write_header()

    def _write_header(self) -> None:
        """Schreibt die CSV-Header"""
        headers = [
            "timestamp",
            "pv_power",
            "grid_power",
            "battery_power",
            "load_power",
            "battery_soc",
            "feed_in_power",
            "grid_consumption",
            "self_consumption",
            "autarky_rate"
        ]

        try:
            with open(self.filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            self.logger.info(f"CSV-Datei {self.filename} erstellt")
        except IOError as e:
            self.logger.error(f"Fehler beim Erstellen der CSV-Datei: {e}")

    def log_data(self, data: SolarData) -> None:
        """
        Schreibt Daten in die CSV-Datei.

        Args:
            data: Zu loggende Solardaten
        """
        row = [
            data.timestamp.isoformat(),
            data.pv_power,
            data.grid_power,
            data.battery_power,
            data.load_power,
            data.battery_soc if data.battery_soc is not None else "",
            data.feed_in_power,
            data.grid_consumption,
            data.self_consumption,
            round(data.autarky_rate, 2)
        ]

        try:
            with open(self.filename, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(row)
        except IOError as e:
            self.logger.error(f"Fehler beim Schreiben der Log-Datei: {e}")