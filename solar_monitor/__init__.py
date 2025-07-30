"""
Fronius Solar Monitor Package
"""

from .config import Config
from .models import SolarData
from .api import FroniusAPI
from .monitor import SolarMonitor
from .daily_stats import DailyStats

# Core-Module für erweiterte Nutzung
from .core import (
    DataProcessor,
    StatsManager,
    DeviceController,
    LoggingCoordinator
)
__author__ = "Jan Vogt"

__all__ = [
    # Haupt-Klassen
    "Config",
    "SolarData",
    "FroniusAPI",
    "SolarMonitor",
    "DailyStats",

    # Core-Module
    "DataProcessor",
    "StatsManager",
    "DeviceController",
    "LoggingCoordinator"
]