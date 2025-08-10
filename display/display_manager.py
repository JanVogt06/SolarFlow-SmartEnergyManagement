"""
Display Manager für zentrale Verwaltung aller Display-Module.
"""

from typing import Any, Optional
import logging


class DisplayManager:
    """Verwaltet alle Display-Module zentral"""

    def __init__(self, config: Any):
        """
        Initialisiert den DisplayManager.

        Args:
            config: Konfigurationsobjekt
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Standard-Module (immer verfügbar)
        from .displays import SolarDisplay, StatsDisplay, SimpleDisplay
        self.solar = SolarDisplay(config)
        self.stats = StatsDisplay(config)
        self.simple = SimpleDisplay(config)

        # Rich Live Display - nur wenn aktiviert
        self.live = None
        self._live_mode_active = False

        if config.display.use_live_display:
            try:
                # Versuche Rich Live Display zu laden
                from .displays import RichLiveDisplay
                self.live = RichLiveDisplay(config)
                self.logger.debug("Rich Live Display erfolgreich geladen")
            except Exception as e:
                # Bei Fehler: Deaktiviere Live Display und verwende normale Anzeige
                self.logger.warning(f"Rich Live Display konnte nicht geladen werden: {e}")
                self.logger.info("Wechsle zu Standard-Anzeige (ohne Live-Updates)")
                config.display.use_live_display = False
                self.live = None

        # Device Display nur wenn Gerätesteuerung aktiv
        from .displays import DeviceDisplay
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
        Zeigt Daten im Live-Update Modus (wenn verfügbar).

        Args:
            data: SolarData-Objekt
            device_manager: Optionaler DeviceManager
        """
        if self.config.display.use_live_display and self.live:
            self._live_mode_active = True
            try:
                self.live.display(data, device_manager)
            except Exception as e:
                self.logger.error(f"Fehler im Live Display: {e}")
                self.logger.info("Deaktiviere Live Display für diese Session")
                # Deaktiviere Live Display für den Rest der Session
                self.config.display.use_live_display = False
                self._live_mode_active = False
                # Zeige normale Anzeige
                self.show_solar_data(data, device_manager)
        else:
            # Normale Anzeige ohne Live-Updates
            self.show_solar_data(data, device_manager)

    def cleanup_live_display(self) -> None:
        """Räumt das Live-Display auf"""
        if self._live_mode_active and self.live:
            try:
                if hasattr(self.live, 'cleanup'):
                    self.live.cleanup()
            except Exception as e:
                self.logger.error(f"Fehler beim Live Display Cleanup: {e}")
            finally:
                self._live_mode_active = False

    def show_daily_stats(self, stats: Any) -> None:
        """
        Zeigt Tagesstatistiken an.

        Args:
            stats: DailyStats-Objekt
        """
        # Bei aktivem Live-Display müssen wir es temporär pausieren
        if self._live_mode_active and self.live and hasattr(self.live, 'live'):
            try:
                # Rich Live Display pausieren
                if self.live.live:
                    self.live.live.stop()
                # Stats anzeigen
                self.stats.display(stats)
                # Live Display wieder starten
                if self.live.live:
                    self.live.live.start()
            except Exception as e:
                self.logger.debug(f"Konnte Live Display nicht pausieren: {e}")
                # Zeige Stats trotzdem
                self.stats.display(stats)
        else:
            # Normale Ausgabe
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