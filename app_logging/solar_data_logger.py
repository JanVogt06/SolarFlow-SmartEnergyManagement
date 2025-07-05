"""
Daten-Logging für den Fronius Solar Monitor mit Session-basierten Dateien.
"""

import csv
import logging
import os
from datetime import datetime
from pathlib import Path

from solar_monitor.models import SolarData
from solar_monitor.config import Config


class DataLogger:
    """Klasse zum Logging der Solardaten mit Session-basierten Dateien"""

    def __init__(self, config: Config):
        """
        Initialisiert den DataLogger mit Konfiguration.

        Args:
            config: Konfigurationsobjekt
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Erstelle Verzeichnisstruktur
        self.base_dir = Path(config.DATA_LOG_DIR)
        self.data_dir = self.base_dir / config.SOLAR_DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Generiere eindeutigen Dateinamen mit Timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = config.DATA_LOG_BASE_NAME.replace('.csv', '')
        self.filename = self.data_dir / f"{base_name}_{timestamp}.csv"

        self.logger.info(f"Neue Log-Datei: {self.filename}")

        # Header schreiben
        self._write_header()

    def _write_header(self) -> None:
        """Schreibt die CSV-Header"""

        if self.config.CSV_USE_GERMAN_HEADERS:
            headers = [
                "Zeitstempel",
                "PV-Erzeugung (W)",
                "Netz (W)",  # + = Bezug, - = Einspeisung
                "Batterie (W)",  # + = Entladung, - = Ladung
                "Hausverbrauch (W)",
                "Batterie-Stand (%)",
                "Gesamtproduktion (W)",
                "Einspeisung (W)",
                "Netzbezug (W)",
                "Eigenverbrauch (W)",
                "Autarkie (%)",
                "Überschuss (W)"
            ]

            info_row = [
                "Format: YYYY-MM-DD HH:MM:SS",
                "Solarproduktion",
                "Negativ=Einspeisung",
                "Negativ=Laden",
                "Gesamtverbrauch",
                "Ladestand",
                "PV + Batterie-Entladung",
                "Ins Netz",
                "Vom Netz",
                "Direktverbrauch",
                "Unabhängigkeit",
                "Verfügbar"
            ] if self.config.CSV_INCLUDE_INFO_ROW else None
        else:
            headers = [
                "Timestamp",
                "PV Power (W)",
                "Grid Power (W)",  # + = consumption, - = feed-in
                "Battery Power (W)",  # + = discharge, - = charge
                "Load Power (W)",
                "Battery SOC (%)",
                "Total Production (W)",
                "Feed-in Power (W)",
                "Grid Consumption (W)",
                "Self Consumption (W)",
                "Autarky Rate (%)",
                "Surplus Power (W)"
            ]

            info_row = [
                "Format: YYYY-MM-DD HH:MM:SS",
                "Solar production",
                "Negative=Feed-in",
                "Negative=Charging",
                "Total consumption",
                "State of charge",
                "PV + Battery discharge",
                "To grid",
                "From grid",
                "Direct consumption",
                "Independence",
                "Available"
            ] if self.config.CSV_INCLUDE_INFO_ROW else None

        try:
            with open(self.filename, 'w', newline='', encoding=self.config.CSV_ENCODING) as f:
                writer = csv.writer(f, delimiter=self.config.CSV_DELIMITER)
                writer.writerow(headers)

                # Schreibe Info-Zeile wenn konfiguriert
                if info_row:
                    writer.writerow(info_row)

                # Schreibe Session-Info als Kommentar
                writer.writerow([])  # Leerzeile
                session_info = [
                    f"# Session Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    f"# Fronius IP: {self.config.FRONIUS_IP}",
                    f"# Update Interval: {self.config.UPDATE_INTERVAL}s",
                    f"# CSV Format: Delimiter='{self.config.CSV_DELIMITER}', Decimal='{self.config.CSV_DECIMAL_SEPARATOR}'"
                ]
                for info in session_info:
                    writer.writerow([info])
                writer.writerow([])  # Leerzeile nach Kommentaren

            self.logger.info(f"CSV-Datei erstellt: {self.filename.name}")
            self.logger.debug(f"Format: Delimiter='{self.config.CSV_DELIMITER}', "
                            f"Encoding={self.config.CSV_ENCODING}, "
                            f"Decimal='{self.config.CSV_DECIMAL_SEPARATOR}'")

        except IOError as e:
            self.logger.error(f"Fehler beim Erstellen der CSV-Datei: {e}")

    def log_data(self, data: SolarData) -> None:
        """
        Schreibt Daten in die CSV-Datei.

        Args:
            data: Zu loggende Solardaten
        """
        # Formatiere Zeitstempel
        timestamp = data.timestamp.strftime('%Y-%m-%d %H:%M:%S')

        # Formatiere Zahlen basierend auf Decimal Separator
        def format_number(value: float, decimals: int = 0, with_sign: bool = False) -> str:
            """Formatiert eine Zahl mit konfigurierbarem Dezimaltrennzeichen"""
            if decimals == 0:
                formatted = f"{value:+.0f}" if with_sign else f"{value:.0f}"
            else:
                formatted = f"{value:+.{decimals}f}" if with_sign else f"{value:.{decimals}f}"

            if self.config.CSV_DECIMAL_SEPARATOR == ",":
                formatted = formatted.replace(".", ",")

            return formatted

        # Erstelle Datenzeile
        row = [
            timestamp,
            format_number(data.pv_power),
            format_number(data.grid_power, with_sign=True),
            format_number(data.battery_power, with_sign=True) if data.battery_power != 0 else "0",
            format_number(data.load_power),
            format_number(data.battery_soc, decimals=1) if data.battery_soc is not None else "-",
            format_number(data.total_production),
            format_number(data.feed_in_power),
            format_number(data.grid_consumption),
            format_number(data.self_consumption),
            format_number(data.autarky_rate, decimals=1),
            format_number(data.surplus_power)
        ]

        try:
            with open(self.filename, 'a', newline='', encoding=self.config.CSV_ENCODING) as f:
                writer = csv.writer(f, delimiter=self.config.CSV_DELIMITER)
                writer.writerow(row)
        except IOError as e:
            self.logger.error(f"Fehler beim Schreiben der Log-Datei: {e}")