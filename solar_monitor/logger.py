"""
Daten-Logging für den Fronius Solar Monitor mit Config-Integration.
"""

import csv
import logging
import os
from datetime import datetime
from typing import List, Optional

from .models import SolarData
from .config import Config


class DataLogger:
    """Klasse zum Logging der Solardaten"""

    def __init__(self, config: Config):
        """
        Initialisiert den DataLogger mit Konfiguration.

        Args:
            config: Konfigurationsobjekt
        """
        self.config = config
        self.filename = config.DATA_LOG_FILE
        self.logger = logging.getLogger(__name__)
        self._ensure_header()

    def _ensure_header(self) -> None:
        """Stellt sicher, dass die CSV-Header existieren"""
        if not os.path.exists(self.filename):
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

            self.logger.info(f"CSV-Datei {self.filename} erstellt (Delimiter: '{self.config.CSV_DELIMITER}', Encoding: {self.config.CSV_ENCODING})")
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


# Hilfsfunktion zum Lesen der CSV mit korrekten Einstellungen
def read_csv_data(config: Config, filename: str = None, last_n_rows: int = None) -> List[dict]:
    """
    Liest CSV-Daten mit den korrekten Config-Einstellungen.

    Args:
        config: Konfigurationsobjekt
        filename: CSV-Datei (optional, nutzt config.DATA_LOG_FILE wenn None)
        last_n_rows: Nur die letzten N Zeilen lesen (optional)

    Returns:
        Liste von Dictionaries mit den Daten
    """
    filename = filename or config.DATA_LOG_FILE

    if not os.path.exists(filename):
        return []

    data = []
    with open(filename, 'r', encoding=config.CSV_ENCODING) as f:
        reader = csv.DictReader(f, delimiter=config.CSV_DELIMITER)

        # Überspringe Info-Zeile wenn vorhanden
        if config.CSV_INCLUDE_INFO_ROW:
            next(reader, None)

        for row in reader:
            # Konvertiere Dezimaltrennzeichen zurück
            if config.CSV_DECIMAL_SEPARATOR == ",":
                for key, value in row.items():
                    if value and value != "-":
                        row[key] = value.replace(",", ".")
            data.append(row)

    if last_n_rows:
        return data[-last_n_rows:]

    return data