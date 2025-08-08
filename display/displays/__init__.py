"""Display-Module für verschiedene Ansichten."""

from .solar_display import SolarDisplay
from .device_display import DeviceDisplay
from .stats_display import StatsDisplay
from .simple_display import SimpleDisplay
from .live_display import LiveDisplay

__all__ = [
    "SolarDisplay",
    "DeviceDisplay",
    "StatsDisplay",
    "SimpleDisplay",
    "LiveDisplay"
]