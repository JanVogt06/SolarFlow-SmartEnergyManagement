"""
Display Manager für zentrale Verwaltung aller Display-Module.
"""

from typing import Any, Optional
from .displays import SolarDisplay, DeviceDisplay, StatsDisplay, SimpleDisplay, LiveDisplay


class DisplayManager:
    """Verwaltet alle Display-Module zentral"""

    def __init__(self, config: Any):
        """
        Initialisiert den DisplayManager.

        Args:
            config: Konfigurationsobjekt
        """
        self.config = config

        # Initialisiere Display-Module
        self.solar = SolarDisplay(config)
        self.stats = StatsDisplay(config)
        self.simple = SimpleDisplay(config)

        # NEU: Live Display
        self.live = LiveDisplay(config)
        self._live_mode_active = False

        # Device Display nur wenn Gerätesteuerung aktiv
        self.device: Optional[DeviceDisplay] = None
        if config.devices.enable_control:
            self.device = DeviceDisplay(config)

    def show_solar_data(self, data: Any, device_manager: Optional[Any] = None) -> None:
        """
        Zeigt Solar-Daten an, optional mit Geräten.

        Args:
            data: SolarData-Objekt
            device_manager: Optionaler DeviceManager
        """
        self.solar.display(data)

        if self.device and device_manager:
            self.device.display(data, device_manager=device_manager)

    def show_live_data(self, data: Any, device_manager: Optional[Any] = None) -> None:
        """
        Zeigt Daten im Live-Update Modus.

        Args:
            data: SolarData-Objekt
            device_manager: Optionaler DeviceManager
        """
        self._live_mode_active = True
        self.live.display(data, device_manager)

    def cleanup_live_display(self) -> None:
        """Räumt das Live-Display auf"""
        if self._live_mode_active:
            self.live.cleanup()
            self._live_mode_active = False

    def show_daily_stats(self, stats: Any) -> None:
        """
        Zeigt Tagesstatistiken an.

        Args:
            stats: DailyStats-Objekt
        """
        self.stats.display(stats)

    def show_simple(self, data: Any) -> None:
        """
        Zeigt einfache Ansicht.

        Args:
            data: SolarData-Objekt
        """
        self.simple.display(data)

    def show_multiline(self, data: Any, device_manager: Optional[Any] = None) -> None:
        """
        Zeigt kompakte mehrzeilige Ansicht.

        Args:
            data: SolarData-Objekt
            device_manager: Optionaler DeviceManager
        """
        if device_manager:
            self.simple.display_devices_compact(data, device_manager)
        else:
            self.simple.display_multiline(data)

    def show_solar_with_progress(self, data: Any) -> None:
        """
        Zeigt Solar-Daten mit Progress Bars.

        Args:
            data: SolarData-Objekt
        """
        self.solar.display_with_progress_bars(data)

    def show_device_timeline(self, devices: list) -> None:
        """
        Zeigt Geräte-Timeline.

        Args:
            devices: Liste von Geräten
        """
        if self.device:
            self.device.display_timeline(devices, 24)