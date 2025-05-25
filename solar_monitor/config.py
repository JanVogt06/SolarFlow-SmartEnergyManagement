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

    # Autarkie-Farben Schwellwerte
    AUTARKY_HIGH_THRESHOLD: float = 75.0  # Grün ab diesem Wert
    AUTARKY_MEDIUM_THRESHOLD: float = 50.0  # Gelb ab diesem Wert

    # Display
    ENABLE_COLORS: bool = os.getenv("ENABLE_COLORS", "True").lower() == "true"

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

        return True