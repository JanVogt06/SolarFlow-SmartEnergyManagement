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

    def get_file_size(self) -> int:
        """
        Gibt die Größe der Log-Datei in Bytes zurück.

        Returns:
            Dateigröße in Bytes
        """
        try:
            return os.path.getsize(self.filename)
        except OSError:
            return 0

    def rotate_if_needed(self, max_size_mb: float = 100) -> None:
        """
        Rotiert die Log-Datei wenn sie zu groß wird.

        Args:
            max_size_mb: Maximale Größe in MB
        """
        max_size_bytes = max_size_mb * 1024 * 1024

        if self.get_file_size() > max_size_bytes:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_filename = f"{self.filename}.{timestamp}"

            try:
                os.rename(self.filename, new_filename)
                self._write_header()
                self.logger.info(f"Log-Datei rotiert: {new_filename}")
            except OSError as e:
                self.logger.error(f"Fehler beim Rotieren der Log-Datei: {e}")


class DatabaseLogger:
    """
    Placeholder für zukünftige Datenbank-Integration.
    Könnte SQLite, PostgreSQL oder InfluxDB verwenden.
    """

    def __init__(self, connection_string: str):
        """
        Initialisiert den DatabaseLogger.

        Args:
            connection_string: Datenbank-Verbindungsstring
        """
        self.connection_string = connection_string
        self.logger = logging.getLogger(__name__)
        # TODO: Implementierung

    def log_data(self, data: SolarData) -> None:
        """
        Schreibt Daten in die Datenbank.

        Args:
            data: Zu loggende Solardaten
        """
        # TODO: Implementierung
        pass

    def get_historical_data(self, start: datetime, end: datetime) -> List[SolarData]:
        """
        Holt historische Daten aus der Datenbank.

        Args:
            start: Startzeit
            end: Endzeit

        Returns:
            Liste von SolarData-Objekten
        """
        # TODO: Implementierung
        return []


class AggregateLogger:
    """Logger für aggregierte Daten (Stündlich, Täglich, etc.)"""

    def __init__(self, filename: str = "solar_data_daily.csv"):
        """
        Initialisiert den AggregateLogger.

        Args:
            filename: Name der CSV-Datei für aggregierte Daten
        """
        self.filename = filename
        self.logger = logging.getLogger(__name__)
        self.current_day = None
        self.daily_data = {
            'energy_produced': 0.0,  # kWh
            'energy_consumed': 0.0,  # kWh
            'energy_fed_in': 0.0,  # kWh
            'energy_from_grid': 0.0,  # kWh
            'max_pv_power': 0.0,  # W
            'avg_autarky': 0.0,  # %
            'data_points': 0
        }

    def update(self, data: SolarData, interval_seconds: int) -> None:
        """
        Aktualisiert die aggregierten Daten.

        Args:
            data: Aktuelle Solardaten
            interval_seconds: Update-Intervall in Sekunden
        """
        # TODO: Implementierung der Aggregation
        pass