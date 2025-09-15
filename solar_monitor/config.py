"""
Konfigurationsmodul für den Fronius Solar Monitor.
"""

import logging
import os
from dataclasses import dataclass, field
from typing import Dict, Optional
from pathlib import Path
from typing import Dict, Optional, Any


@dataclass
class ConnectionConfig:
    """Verbindungseinstellungen"""
    fronius_ip: str = field(default_factory=lambda: os.getenv("FRONIUS_IP", "192.168.178.90"))
    request_timeout: int = field(default_factory=lambda: int(os.getenv("REQUEST_TIMEOUT", "5")))


@dataclass
class TimingConfig:
    """Zeit- und Intervall-Einstellungen"""
    update_interval: int = field(default_factory=lambda: int(os.getenv("UPDATE_INTERVAL", "5")))
    daily_stats_interval: int = field(default_factory=lambda: int(os.getenv("DAILY_STATS_INTERVAL", "1800")))


@dataclass
class LoggingConfig:
    """Logging-Einstellungen"""
    log_level: int = field(default_factory=lambda: getattr(logging, os.getenv("LOG_LEVEL", "INFO")))
    log_file: str = field(default_factory=lambda: os.getenv("LOG_FILE", "solar_monitor.log"))

    # Feature-Flags
    enable_data_logging: bool = field(default_factory=lambda: os.getenv("ENABLE_DATA_LOGGING", "True").lower() == "true")
    enable_daily_stats_logging: bool = field(default_factory=lambda: os.getenv("ENABLE_DAILY_STATS_LOGGING", "True").lower() == "true")
    enable_device_logging: bool = field(default_factory=lambda: os.getenv("ENABLE_DEVICE_LOGGING", "True").lower() == "true")

    # Logging-Details
    device_log_events: bool = field(default_factory=lambda: os.getenv("DEVICE_LOG_EVENTS", "True").lower() == "true")
    device_log_status: bool = field(default_factory=lambda: os.getenv("DEVICE_LOG_STATUS", "True").lower() == "true")
    device_log_daily_summary: bool = field(default_factory=lambda: os.getenv("DEVICE_LOG_DAILY_SUMMARY", "True").lower() == "true")


@dataclass
class DirectoryConfig:
    """Verzeichnis-Einstellungen"""
    data_log_dir: str = field(default_factory=lambda: os.getenv("DATA_LOG_DIR", "Datalogs"))
    solar_data_dir: str = field(default_factory=lambda: os.getenv("SOLAR_DATA_DIR", "Solardata"))
    daily_stats_dir: str = field(default_factory=lambda: os.getenv("DAILY_STATS_DIR", "Dailystats"))
    device_log_dir: str = field(default_factory=lambda: os.getenv("DEVICE_LOG_DIR", "Devicelogs"))

    # Dateinamen
    data_log_base_name: str = field(default_factory=lambda: os.getenv("DATA_LOG_BASE_NAME", "solar_data"))
    daily_stats_base_name: str = field(default_factory=lambda: os.getenv("DAILY_STATS_BASE_NAME", "daily_stats"))
    device_events_base_name: str = field(default_factory=lambda: os.getenv("DEVICE_EVENTS_BASE_NAME", "device_events"))
    device_status_base_name: str = field(default_factory=lambda: os.getenv("DEVICE_STATUS_BASE_NAME", "device_status"))


@dataclass
class CSVConfig:
    """CSV-Format Einstellungen"""
    delimiter: str = field(default_factory=lambda: os.getenv("CSV_DELIMITER", ";"))
    encoding: str = field(default_factory=lambda: os.getenv("CSV_ENCODING", "utf-8"))
    decimal_separator: str = field(default_factory=lambda: os.getenv("CSV_DECIMAL_SEPARATOR", ","))
    use_german_headers: bool = field(default_factory=lambda: os.getenv("CSV_USE_GERMAN_HEADERS", "True").lower() == "true")
    include_info_row: bool = field(default_factory=lambda: os.getenv("CSV_INCLUDE_INFO_ROW", "True").lower() == "true")


@dataclass
class DeviceControlConfig:
    """Gerätesteuerungs-Einstellungen"""
    enable_control: bool = field(default_factory=lambda: os.getenv("ENABLE_DEVICE_CONTROL", "True").lower() == "true")
    config_file: str = field(default_factory=lambda: os.getenv("DEVICE_CONFIG_FILE", "devices.json"))
    hysteresis_minutes: int = field(default_factory=lambda: int(os.getenv("DEVICE_HYSTERESIS_MINUTES", "5")))
    update_only_on_change: bool = field(
        default_factory=lambda: os.getenv("DEVICE_UPDATE_ONLY_ON_CHANGE", "True").lower() == "true")

    # HUE INTEGRATION
    enable_hue: bool = field(default_factory=lambda: os.getenv("ENABLE_HUE", "False").lower() == "true")
    hue_bridge_ip: str = field(default_factory=lambda: os.getenv("HUE_BRIDGE_IP", "192.168.178.26"))
    hue_connection_timeout: int = field(default_factory=lambda: int(os.getenv("HUE_CONNECTION_TIMEOUT", "10")))


@dataclass
class DisplayConfig:
    """Anzeige-Einstellungen"""
    enable_colors: bool = field(default_factory=lambda: os.getenv("ENABLE_COLORS", "True").lower() == "true")
    show_daily_stats: bool = field(default_factory=lambda: os.getenv("SHOW_DAILY_STATS", "True").lower() == "true")
    surplus_display_threshold: float = field(default_factory=lambda: float(os.getenv("SURPLUS_DISPLAY_THRESHOLD", "0")))
    use_live_display: bool = field(default_factory=lambda: os.getenv("USE_LIVE_DISPLAY", "True").lower() == "true")


@dataclass
class CostConfig:
    """Kosten- und Tarif-Einstellungen"""
    electricity_price: float = field(default_factory=lambda: float(os.getenv("ELECTRICITY_PRICE", "0.40")))
    electricity_price_night: float = field(default_factory=lambda: float(os.getenv("ELECTRICITY_PRICE_NIGHT", "0.30")))
    feed_in_tariff: float = field(default_factory=lambda: float(os.getenv("FEED_IN_TARIFF", "0.082")))

    # Zeitbasierte Tarife
    night_tariff_start: str = field(default_factory=lambda: os.getenv("NIGHT_TARIFF_START", "22:00"))
    night_tariff_end: str = field(default_factory=lambda: os.getenv("NIGHT_TARIFF_END", "06:00"))

    # Währung
    currency_symbol: str = field(default_factory=lambda: os.getenv("CURRENCY_SYMBOL", "€"))
    currency_format: str = field(default_factory=lambda: os.getenv("CURRENCY_FORMAT", "de-DE"))


@dataclass
class DatabaseConfig:
    """Datenbank-Einstellungen"""
    enable_database: bool = field(default_factory=lambda: os.getenv("ENABLE_DATABASE", "True").lower() == "true")
    database_path: str = field(default_factory=lambda: os.getenv("DATABASE_PATH", "Datalogs/solar_energy.db"))


@dataclass
class BatteryConfig:
    """Batterie-Einstellungen"""
    idle_threshold: float = field(default_factory=lambda: float(os.getenv("BATTERY_IDLE_THRESHOLD", "10")))
    soc_high_threshold: float = field(default_factory=lambda: float(os.getenv("BATTERY_SOC_HIGH_THRESHOLD", "80")))
    soc_medium_threshold: float = field(default_factory=lambda: float(os.getenv("BATTERY_SOC_MEDIUM_THRESHOLD", "30")))


@dataclass
class ThresholdsConfig:
    """Schwellwerte für verschiedene Metriken"""
    battery_soc: Dict[str, float] = field(default_factory=lambda: {
        'high': float(os.getenv("BATTERY_SOC_HIGH_THRESHOLD", "80")),
        'medium': float(os.getenv("BATTERY_SOC_MEDIUM_THRESHOLD", "30"))
    })

    autarky: Dict[str, float] = field(default_factory=lambda: {
        'high': float(os.getenv("AUTARKY_HIGH_THRESHOLD", "75")),
        'medium': float(os.getenv("AUTARKY_MEDIUM_THRESHOLD", "50"))
    })

    pv_power: Dict[str, float] = field(default_factory=lambda: {
        'high': float(os.getenv("PV_POWER_HIGH_THRESHOLD", "3000")),
        'medium': float(os.getenv("PV_POWER_MEDIUM_THRESHOLD", "1000"))
    })

    surplus: Dict[str, float] = field(default_factory=lambda: {
        'high': float(os.getenv("SURPLUS_HIGH_THRESHOLD", "2000")),
        'medium': float(os.getenv("SURPLUS_MEDIUM_THRESHOLD", "500"))
    })


@dataclass
class APIConfig:
    """API Server Einstellungen"""
    enabled: bool = field(default_factory=lambda: os.getenv("API_ENABLED", "True").lower() == "true")
    host: str = field(default_factory=lambda: os.getenv("API_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("API_PORT", "8000")))


class Config:
    """Zentrale Konfigurationsklasse mit gruppierten Einstellungen"""

    def __init__(self):
        """Initialisiert alle Konfigurationsgruppen"""
        self.connection = ConnectionConfig()
        self.timing = TimingConfig()
        self.logging = LoggingConfig()
        self.directories = DirectoryConfig()
        self.csv = CSVConfig()
        self.devices = DeviceControlConfig()
        self.display = DisplayConfig()
        self.costs = CostConfig()
        self.database = DatabaseConfig()
        self.battery = BatteryConfig()
        self.thresholds = ThresholdsConfig()
        self.api = APIConfig()  # Neue API-Konfiguration

    @property
    def THRESHOLDS(self) -> Dict[str, Dict[str, float]]:
        return {
            'battery_soc': self.thresholds.battery_soc,
            'autarky': self.thresholds.autarky,
            'pv_power': self.thresholds.pv_power,
            'surplus': self.thresholds.surplus
        }

    # ========== Validierung ==========

    def validate(self) -> bool:
        """Validiert die Konfiguration"""
        errors = []

        # Timing-Validierung
        if self.timing.update_interval < 1:
            errors.append("update_interval muss mindestens 1 Sekunde sein")

        if self.timing.daily_stats_interval < 60:
            errors.append("daily_stats_interval sollte mindestens 60 Sekunden sein")

        # Connection-Validierung
        if self.connection.request_timeout < 1:
            errors.append("request_timeout muss mindestens 1 Sekunde sein")

        # CSV-Validierung
        if self.csv.delimiter not in [",", ";", "\t", "|"]:
            errors.append("csv.delimiter muss eines von ',', ';', '\\t', '|' sein")

        if self.csv.decimal_separator not in [".", ","]:
            errors.append("csv.decimal_separator muss '.' oder ',' sein")

        if self.csv.encoding not in ["utf-8", "latin-1", "cp1252", "iso-8859-1"]:
            errors.append("csv.encoding muss ein gültiges Encoding sein")

        # Battery-Validierung
        if self.battery.idle_threshold < 0:
            errors.append("battery.idle_threshold muss positiv sein")

        # API-Validierung
        if self.api.port < 1 or self.api.port > 65535:
            errors.append("api.port muss zwischen 1 und 65535 liegen")

        # Schwellwert-Validierung
        for key, thresholds in self.thresholds.__dict__.items():
            if isinstance(thresholds, dict) and 'high' in thresholds and 'medium' in thresholds:
                if thresholds['high'] <= thresholds['medium']:
                    errors.append(f"thresholds.{key}['high'] muss größer als thresholds.{key}['medium'] sein")

        if errors:
            for error in errors:
                logging.error(f"Konfigurationsfehler: {error}")
            return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert die Konfiguration in ein Dictionary"""
        return {
            'connection': self.connection.__dict__,
            'timing': self.timing.__dict__,
            'logging': self.logging.__dict__,
            'directories': self.directories.__dict__,
            'csv': self.csv.__dict__,
            'devices': self.devices.__dict__,
            'display': self.display.__dict__,
            'costs': self.costs.__dict__,
            'database': self.database.__dict__,
            'battery': self.battery.__dict__,
            'thresholds': self.thresholds.__dict__,
            'api': self.api.__dict__
        }

    def save_to_file(self, filepath: Path) -> None:
        """Speichert die Konfiguration in eine JSON-Datei"""
        import json
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, filepath: Path) -> 'Config':
        """Lädt Konfiguration aus einer JSON-Datei"""
        import json
        config = cls()

        if filepath.exists():
            with open(filepath, 'r') as f:
                data = json.load(f)

            # Lade die Werte in die entsprechenden Gruppen
            for group_name, group_data in data.items():
                if hasattr(config, group_name):
                    group = getattr(config, group_name)
                    for key, value in group_data.items():
                        if hasattr(group, key):
                            setattr(group, key, value)

        return config