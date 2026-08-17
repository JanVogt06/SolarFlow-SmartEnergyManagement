"""
Fronius Solar Monitor Package
"""

from .config import Config
from .models import SolarData
from .api import FroniusAPI
from .monitor import SolarMonitor
from .daily_stats import DailyStats
from .settings import SettingsStore

from .core import (
    DataProcessor,
    StatsManager,
    DeviceController,
    LoggingCoordinator
)
__author__ = "Jan Vogt"

__all__ = [
    "Config",
    "SolarData",
    "FroniusAPI",
    "SolarMonitor",
    "DailyStats",
    "SettingsStore",

    "DataProcessor",
    "StatsManager",
    "DeviceController",
    "LoggingCoordinator"
]