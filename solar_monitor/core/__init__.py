"""
Core-Module für den Solar Monitor.
"""

from .data_processor import DataProcessor
from .stats_manager import StatsManager
from .device_controller import DeviceController
from .logging_coordinator import LoggingCoordinator

__all__ = [
    "DataProcessor",
    "StatsManager",
    "DeviceController",
    "LoggingCoordinator"
]