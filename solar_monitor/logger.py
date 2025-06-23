"""
Daten-Logging für den Fronius Solar Monitor mit CSV-Ausgabe.
"""

import csv
import logging
import os

from .models import SolarData


class DataLogger:
    """Klasse zum Logging der Solardaten mit lesbarer CSV-Ausgabe"""

    def __init__(self, filename: str = "solar_data.csv", use_german_headers: bool = True):
        """
        Initialisiert den DataLogger.

        Args:
            filename: Name der CSV-Datei
            use_german_headers: Verwende deutsche Spaltenüberschriften
        """
        self.filename = filename
        self.logger = logging.getLogger(__name__)
        self.use_german_headers = use_german_headers
        self._ensure_header()

    def _ensure_header(self) -> None:
        """Stellt sicher, dass die CSV-Header existieren"""
        if not os.path.exists(self.filename):
            self._write_header()

    def _write_header(self) -> None:
        """Schreibt die CSV-Header mit Einheiten"""

        if self.use_german_headers:
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

        try:
            with open(self.filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';')  # Semikolon für Excel-Kompatibilität
                writer.writerow(headers)

                # Zusätzliche Info-Zeile
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
                ]
                writer.writerow(info_row if self.use_german_headers else [])

            self.logger.info(f"CSV-Datei {self.filename} erstellt")
        except IOError as e:
            self.logger.error(f"Fehler beim Erstellen der CSV-Datei: {e}")

    def log_data(self, data: SolarData) -> None:
        """
        Schreibt Daten in die CSV-Datei mit verbesserter Formatierung.

        Args:
            data: Zu loggende Solardaten
        """
        # Formatiere Zeitstempel lesbar
        timestamp = data.timestamp.strftime('%Y-%m-%d %H:%M:%S')

        # Formatiere Zahlen für bessere Lesbarkeit
        row = [
            timestamp,
            f"{data.pv_power:.0f}",  # Keine Nachkommastellen bei Watt
            f"{data.grid_power:+.0f}",  # Mit Vorzeichen
            f"{data.battery_power:+.0f}" if data.battery_power != 0 else "0",
            f"{data.load_power:.0f}",
            f"{data.battery_soc:.1f}" if data.battery_soc is not None else "-",
            f"{data.feed_in_power:.0f}",
            f"{data.grid_consumption:.0f}",
            f"{data.self_consumption:.0f}",
            f"{data.autarky_rate:.1f}",  # Eine Nachkommastelle bei Prozent
            f"{data.surplus_power:.0f}"
        ]

        try:
            with open(self.filename, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(row)
        except IOError as e:
            self.logger.error(f"Fehler beim Schreiben der Log-Datei: {e}")

    def create_hourly_summary(self, output_filename: str = None) -> None:
        """
        Erstellt eine stündliche Zusammenfassung der Daten.

        Args:
            output_filename: Name der Ausgabedatei (optional)
        """
        if not os.path.exists(self.filename):
            self.logger.warning("Keine Daten zum Zusammenfassen vorhanden")
            return

        output_filename = output_filename or self.filename.replace('.csv', '_stündlich.csv')

        # Hier würde die Zusammenfassungslogik kommen
        # Erstmal als Platzhalter
        self.logger.info(f"Stündliche Zusammenfassung würde in {output_filename} erstellt")


# Optionale Hilfsfunktion zum Lesen und Anzeigen der CSV
def display_last_entries(filename: str, count: int = 10) -> None:
    """
    Zeigt die letzten Einträge der CSV-Datei formatiert an.

    Args:
        filename: Name der CSV-Datei
        count: Anzahl der anzuzeigenden Einträge
    """
    if not os.path.exists(filename):
        print(f"Datei {filename} nicht gefunden")
        return

    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Überspringe Header
    if len(lines) <= 2:
        print("Keine Daten vorhanden")
        return

    # Zeige Header
    print("\n" + "="*100)
    print(lines[0].strip())
    print("-"*100)

    # Zeige letzte Einträge
    start_idx = max(2, len(lines) - count)
    for line in lines[start_idx:]:
        print(line.strip())
    print("="*100)