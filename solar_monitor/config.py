"""
Konfigurationsmodul für den Fronius Solar Monitor.
"""

import logging
import os
from typing import Optional, Dict


class Config:
    """Zentrale Konfigurationsklasse"""

    # Fronius Wechselrichter
    FRONIUS_IP: str = os.getenv("FRONIUS_IP", "192.168.178.90")

    # Zeitintervalle
    UPDATE_INTERVAL: int = int(os.getenv("UPDATE_INTERVAL", "5"))  # Sekunden
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "5"))  # Sekunden

    # Logging
    LOG_LEVEL = getattr(logging, os.getenv("LOG_LEVEL", "INFO"))
    LOG_FILE: str = os.getenv("LOG_FILE", "solar_monitor.log")

    # Daten-Logging
    DATA_LOG_DIR: str = os.getenv("DATA_LOG_DIR", "Datalogs")  # Ordner für Log-Dateien
    DATA_LOG_BASE_NAME: str = os.getenv("DATA_LOG_BASE_NAME", "solar_data")  # Basis-Name ohne .csv
    DATA_LOG_FILE: str = os.getenv("DATA_LOG_FILE", "solar_data.csv")  # Deprecated - nur für Kompatibilität
    ENABLE_DATA_LOGGING: bool = os.getenv("ENABLE_DATA_LOGGING", "True").lower() == "true"

    # CSV Format Optionen
    CSV_DELIMITER: str = os.getenv("CSV_DELIMITER", ";")  # ; für Excel DE, , für international
    CSV_USE_GERMAN_HEADERS: bool = os.getenv("CSV_USE_GERMAN_HEADERS", "True").lower() == "true"
    CSV_ENCODING: str = os.getenv("CSV_ENCODING", "utf-8")  # utf-8, latin-1, cp1252 für Windows
    CSV_DECIMAL_SEPARATOR: str = os.getenv("CSV_DECIMAL_SEPARATOR", ",")  # . oder , für Dezimalzahlen
    CSV_INCLUDE_INFO_ROW: bool = os.getenv("CSV_INCLUDE_INFO_ROW", "True").lower() == "true"  # Info-Zeile unter Header

    # Batterie
    BATTERY_IDLE_THRESHOLD: float = float(os.getenv("BATTERY_IDLE_THRESHOLD", "10"))  # Watt

    # Display
    ENABLE_COLORS: bool = os.getenv("ENABLE_COLORS", "True").lower() == "true"

    # Tagesstatistiken
    DAILY_STATS_INTERVAL: int = int(os.getenv("DAILY_STATS_INTERVAL", "1800"))  # Sekunden (Standard: 30 Min)
    SHOW_DAILY_STATS: bool = os.getenv("SHOW_DAILY_STATS", "True").lower() == "true"

    # Überschuss-Anzeige
    SURPLUS_DISPLAY_THRESHOLD: float = float(os.getenv("SURPLUS_DISPLAY_THRESHOLD", "0"))  # Watt - Anzeige-Schwelle

    # Zentrale Schwellwerte für Farbcodierung
    THRESHOLDS: Dict[str, Dict[str, float]] = {
        'battery_soc': {
            'high': float(os.getenv("BATTERY_SOC_HIGH_THRESHOLD", "80")),      # Grün ab diesem Wert
            'medium': float(os.getenv("BATTERY_SOC_MEDIUM_THRESHOLD", "30"))   # Gelb ab diesem Wert
        },
        'autarky': {
            'high': float(os.getenv("AUTARKY_HIGH_THRESHOLD", "75")),          # Grün ab diesem Wert
            'medium': float(os.getenv("AUTARKY_MEDIUM_THRESHOLD", "50"))       # Gelb ab diesem Wert
        },
        'pv_power': {
            'high': float(os.getenv("PV_POWER_HIGH_THRESHOLD", "3000")),       # Watt - Grün ab diesem Wert
            'medium': float(os.getenv("PV_POWER_MEDIUM_THRESHOLD", "1000"))    # Watt - Gelb ab diesem Wert
        },
        'surplus': {
            'high': float(os.getenv("SURPLUS_HIGH_THRESHOLD", "2000")),        # Watt - Viel Überschuss
            'medium': float(os.getenv("SURPLUS_MEDIUM_THRESHOLD", "500"))      # Watt - Mittlerer Überschuss
        }
    }

    # Kompatibilität für alte Konfiguration (Deprecated)
    @property
    def BATTERY_SOC_HIGH_THRESHOLD(self):
        return self.THRESHOLDS['battery_soc']['high']

    @BATTERY_SOC_HIGH_THRESHOLD.setter
    def BATTERY_SOC_HIGH_THRESHOLD(self, value):
        self.THRESHOLDS['battery_soc']['high'] = value

    @property
    def BATTERY_SOC_MEDIUM_THRESHOLD(self):
        return self.THRESHOLDS['battery_soc']['medium']

    @BATTERY_SOC_MEDIUM_THRESHOLD.setter
    def BATTERY_SOC_MEDIUM_THRESHOLD(self, value):
        self.THRESHOLDS['battery_soc']['medium'] = value

    @property
    def AUTARKY_HIGH_THRESHOLD(self):
        return self.THRESHOLDS['autarky']['high']

    @AUTARKY_HIGH_THRESHOLD.setter
    def AUTARKY_HIGH_THRESHOLD(self, value):
        self.THRESHOLDS['autarky']['high'] = value

    @property
    def AUTARKY_MEDIUM_THRESHOLD(self):
        return self.THRESHOLDS['autarky']['medium']

    @AUTARKY_MEDIUM_THRESHOLD.setter
    def AUTARKY_MEDIUM_THRESHOLD(self, value):
        self.THRESHOLDS['autarky']['medium'] = value

    @property
    def PV_POWER_HIGH_THRESHOLD(self):
        return self.THRESHOLDS['pv_power']['high']

    @PV_POWER_HIGH_THRESHOLD.setter
    def PV_POWER_HIGH_THRESHOLD(self, value):
        self.THRESHOLDS['pv_power']['high'] = value

    @property
    def PV_POWER_MEDIUM_THRESHOLD(self):
        return self.THRESHOLDS['pv_power']['medium']

    @PV_POWER_MEDIUM_THRESHOLD.setter
    def PV_POWER_MEDIUM_THRESHOLD(self, value):
        self.THRESHOLDS['pv_power']['medium'] = value

    @property
    def SURPLUS_HIGH_THRESHOLD(self):
        return self.THRESHOLDS['surplus']['high']

    @SURPLUS_HIGH_THRESHOLD.setter
    def SURPLUS_HIGH_THRESHOLD(self, value):
        self.THRESHOLDS['surplus']['high'] = value

    @property
    def SURPLUS_MEDIUM_THRESHOLD(self):
        return self.THRESHOLDS['surplus']['medium']

    @SURPLUS_MEDIUM_THRESHOLD.setter
    def SURPLUS_MEDIUM_THRESHOLD(self, value):
        self.THRESHOLDS['surplus']['medium'] = value

    def validate(self) -> bool:
        """Validiert die Konfiguration"""
        if self.UPDATE_INTERVAL < 1:
            raise ValueError("UPDATE_INTERVAL muss mindestens 1 Sekunde sein")

        if self.REQUEST_TIMEOUT < 1:
            raise ValueError("REQUEST_TIMEOUT muss mindestens 1 Sekunde sein")

        if self.BATTERY_IDLE_THRESHOLD < 0:
            raise ValueError("BATTERY_IDLE_THRESHOLD muss positiv sein")

        # Validiere CSV-Optionen
        if self.CSV_DELIMITER not in [",", ";", "\t", "|"]:
            raise ValueError("CSV_DELIMITER muss eines von ',', ';', '\\t', '|' sein")

        if self.CSV_DECIMAL_SEPARATOR not in [".", ","]:
            raise ValueError("CSV_DECIMAL_SEPARATOR muss '.' oder ',' sein")

        if self.CSV_ENCODING not in ["utf-8", "latin-1", "cp1252", "iso-8859-1"]:
            raise ValueError("CSV_ENCODING muss ein gültiges Encoding sein")

        # Validiere Schwellwerte
        for key, thresholds in self.THRESHOLDS.items():
            if thresholds['high'] <= thresholds['medium']:
                raise ValueError(f"THRESHOLDS['{key}']['high'] muss größer als THRESHOLDS['{key}']['medium'] sein")

        # Validiere Tagesstatistik-Intervall
        if self.DAILY_STATS_INTERVAL < 60:
            raise ValueError("DAILY_STATS_INTERVAL sollte mindestens 60 Sekunden sein")

        return True