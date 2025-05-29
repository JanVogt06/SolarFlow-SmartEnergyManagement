"""
Konfigurationsmodul für den Fronius Solar Monitor.
"""

import logging
import os
from typing import Optional


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
    DATA_LOG_FILE: str = os.getenv("DATA_LOG_FILE", "solar_data.csv")
    ENABLE_DATA_LOGGING: bool = os.getenv("ENABLE_DATA_LOGGING", "True").lower() == "true"

    # Batterie
    BATTERY_IDLE_THRESHOLD: float = float(os.getenv("BATTERY_IDLE_THRESHOLD", "10"))  # Watt

    # API-Optionen
    CHECK_API_VERSION: bool = os.getenv("CHECK_API_VERSION", "False").lower() == "true"

    # Display
    ENABLE_COLORS: bool = os.getenv("ENABLE_COLORS", "True").lower() == "true"

    # Batterie-Ladestand Farbschwellwerte
    BATTERY_SOC_HIGH_THRESHOLD: float = float(os.getenv("BATTERY_SOC_HIGH_THRESHOLD", "80"))  # Grün ab diesem Wert
    BATTERY_SOC_MEDIUM_THRESHOLD: float = float(os.getenv("BATTERY_SOC_MEDIUM_THRESHOLD", "30"))  # Gelb ab diesem Wert

    # Autarkie-Farben Schwellwerte
    AUTARKY_HIGH_THRESHOLD: float = float(os.getenv("AUTARKY_HIGH_THRESHOLD", "75"))  # Grün ab diesem Wert
    AUTARKY_MEDIUM_THRESHOLD: float = float(os.getenv("AUTARKY_MEDIUM_THRESHOLD", "50"))  # Gelb ab diesem Wert

    # PV-Leistung Farbschwellwerte (optional für zukünftige Verwendung)
    PV_POWER_HIGH_THRESHOLD: float = float(os.getenv("PV_POWER_HIGH_THRESHOLD", "3000"))  # Watt - Grün ab diesem Wert
    PV_POWER_MEDIUM_THRESHOLD: float = float(os.getenv("PV_POWER_MEDIUM_THRESHOLD", "1000"))  # Watt - Gelb ab diesem Wert

    # Überschuss-Schwellwerte (für Gerätesteuerung)
    SURPLUS_HIGH_THRESHOLD: float = float(os.getenv("SURPLUS_HIGH_THRESHOLD", "2000"))  # Watt - Viel Überschuss
    SURPLUS_MEDIUM_THRESHOLD: float = float(os.getenv("SURPLUS_MEDIUM_THRESHOLD", "500"))  # Watt - Mittlerer Überschuss
    SURPLUS_DISPLAY_THRESHOLD: float = float(os.getenv("SURPLUS_DISPLAY_THRESHOLD", "100"))  # Watt - Anzeige-Schwelle

    @classmethod
    def from_file(cls, filepath: str) -> "Config":
        """Lädt Konfiguration aus einer Datei (zukünftige Erweiterung)"""
        # Placeholder für zukünftige Implementierung
        return cls()

    def validate(self) -> bool:
        """Validiert die Konfiguration"""
        if self.UPDATE_INTERVAL < 1:
            raise ValueError("UPDATE_INTERVAL muss mindestens 1 Sekunde sein")

        if self.REQUEST_TIMEOUT < 1:
            raise ValueError("REQUEST_TIMEOUT muss mindestens 1 Sekunde sein")

        if self.BATTERY_IDLE_THRESHOLD < 0:
            raise ValueError("BATTERY_IDLE_THRESHOLD muss positiv sein")

        # Validiere Schwellwerte
        if self.AUTARKY_HIGH_THRESHOLD <= self.AUTARKY_MEDIUM_THRESHOLD:
            raise ValueError("AUTARKY_HIGH_THRESHOLD muss größer als AUTARKY_MEDIUM_THRESHOLD sein")

        if self.BATTERY_SOC_HIGH_THRESHOLD <= self.BATTERY_SOC_MEDIUM_THRESHOLD:
            raise ValueError("BATTERY_SOC_HIGH_THRESHOLD muss größer als BATTERY_SOC_MEDIUM_THRESHOLD sein")

        if self.PV_POWER_HIGH_THRESHOLD <= self.PV_POWER_MEDIUM_THRESHOLD:
            raise ValueError("PV_POWER_HIGH_THRESHOLD muss größer als PV_POWER_MEDIUM_THRESHOLD sein")

        if self.SURPLUS_HIGH_THRESHOLD <= self.SURPLUS_MEDIUM_THRESHOLD:
            raise ValueError("SURPLUS_HIGH_THRESHOLD muss größer als SURPLUS_MEDIUM_THRESHOLD sein")

        return True