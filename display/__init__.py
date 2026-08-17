"""
Display Package für den Smart Energy Manager.
"""

from .display_manager import DisplayManager
from .displays import SolarDisplay, DeviceDisplay, StatsDisplay, SimpleDisplay
from .core import ColorManager, Formatter, Colors, Layout
from .components import Header, Table, ProgressBar, Separator

__all__ = [
    # Haupt-Manager
    "DisplayManager",

    # Display-Module
    "SolarDisplay",
    "DeviceDisplay",
    "StatsDisplay",
    "SimpleDisplay",

    # Core-Komponenten
    "ColorManager",
    "Formatter",
    "Colors",
    "Layout",

    # UI-Komponenten
    "Header",
    "Table",
    "ProgressBar",
    "Separator"
]