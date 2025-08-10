"""
Gerätesteuerungs-Integration für den Solar Monitor.
"""

import logging
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from device_management import DeviceManager, EnergyController, DeviceState
from ..models import SolarData


class DeviceController:
    """Koordiniert die Gerätesteuerung"""

    def __init__(self, config: Any, device_logger: Any, file_handler: Any):
        """
        Initialisiert den DeviceController.

        Args:
            config: Konfigurationsobjekt
            device_logger: Logger für Geräte-Events
            file_handler: File Handler für Pfade
        """
        self.config = config
        self.device_logger = device_logger
        self.file_handler = file_handler
        self.logger = logging.getLogger(__name__)

        self.device_manager: Optional[DeviceManager] = None
        self.energy_controller: Optional[EnergyController] = None

        # Tracking
        self.last_device_update: Optional[float] = None
        self.last_surplus_power: Optional[float] = None

        if config.devices.enable_control:
            self._init_device_control()

    def _init_device_control(self) -> None:
        """Initialisiert die Gerätesteuerung"""
        try:
            config_file = Path(self.config.devices.config_file)
            self.device_manager = DeviceManager(config_file)

            # HUE INTEGRATION
            hue_interface = None
            if self.config.devices.enable_hue and self.config.devices.hue_bridge_ip:
                self.logger.info("Initialisiere Hue-Integration...")
                try:
                    # Importiere Hue Interface
                    from hue_interface import HueInterface

                    hue_interface = HueInterface(self.config.devices.hue_bridge_ip)
                    if hue_interface.connect():
                        self.logger.info("✅ Hue Bridge verbunden!")

                        # Zeige gefundene Hue-Geräte
                        hue_devices = hue_interface.list_devices()
                        if hue_devices:
                            self.logger.info(f"Gefundene Hue-Geräte ({len(hue_devices)}):")
                            for hd in hue_devices:
                                self.logger.info(f"  - {hd}")
                    else:
                        self.logger.warning("❌ Hue Bridge Verbindung fehlgeschlagen!")
                        self.logger.info("Tipp: Beim ersten Start muss der Knopf auf der Bridge gedrückt werden!")
                        hue_interface = None

                except ImportError:
                    self.logger.error("phue Library nicht installiert! Führe aus: pip install phue")
                    hue_interface = None
                except Exception as e:
                    self.logger.error(f"Fehler bei Hue-Initialisierung: {e}")
                    hue_interface = None

            # Energy Controller mit oder ohne Hue
            self.energy_controller = EnergyController(self.device_manager)
            if hue_interface:
                self.energy_controller.hue_interface = hue_interface
                self.logger.info("Gerätesteuerung mit Hue-Hardware aktiviert")
            else:
                self.logger.info("Gerätesteuerung nur virtuell (ohne Hardware)")

            # Setze Hysterese-Zeit
            self.energy_controller.hysteresis_time = timedelta(
                minutes=self.config.devices.hysteresis_minutes
            )

            self.logger.info(f"Gerätesteuerung aktiviert. Konfiguration: {config_file}")
            self.logger.info(f"Gefundene Geräte: {len(self.device_manager.devices)}")

            # Liste Geräte auf
            for device in self.device_manager.get_devices_by_priority():
                # Prüfe ob Gerät in Hue existiert
                hue_status = ""
                if hue_interface and device.name in hue_interface.device_map:
                    hue_status = " [✓ Hue]"
                elif hue_interface:
                    hue_status = " [✗ Nicht in Hue!]"

                self.logger.info(
                    f"  - {device.name}: {device.power_consumption}W, "
                    f"Priorität {device.priority}, "
                    f"Schwellwerte: Ein={device.switch_on_threshold}W, "
                    f"Aus={device.switch_off_threshold}W{hue_status}"
                )

        except Exception as e:
            self.logger.error(f"Fehler bei der Initialisierung der Gerätesteuerung: {e}")
            self.config.devices.enable_control = False
            self.device_manager = None
            self.energy_controller = None

    def update(self, data: SolarData) -> None:
        """
        Aktualisiert die Gerätesteuerung.

        Args:
            data: Aktuelle Solardaten
        """
        if not self.energy_controller:
            return

        # Prüfe ob Update notwendig
        if not self._should_update_devices(data):
            return

        # Führe Update durch
        changes = self.energy_controller.update(data.surplus_power, data.timestamp)

        # Verarbeite Änderungen
        if changes:
            self._process_device_changes(changes, data)

        # Merke Werte für nächsten Vergleich
        self.last_surplus_power = data.surplus_power
        self.last_device_update = time.time()

    def _should_update_devices(self, data: SolarData) -> bool:
        """Prüft ob Geräte-Update notwendig ist"""
        if not self.config.devices.update_only_on_change:
            return True

        # Berechne Änderung des Überschusses
        if self.last_surplus_power is None:
            return True

        change = abs(data.surplus_power - self.last_surplus_power)

        # Update bei signifikanter Änderung (>50W)
        if change >= 50:
            return True

        # Oder alle 60 Sekunden
        if self.last_device_update:
            time_since_update = time.time() - self.last_device_update
            return time_since_update >= 60

        return True

    def _process_device_changes(self, changes: Dict[str, str], data: SolarData) -> None:
        """Verarbeitet Geräteänderungen"""
        for device_name, action in changes.items():
            self.logger.info(f"Gerät '{device_name}' {action}")

        # Logge Änderungen
        if self.config.logging.device_log_events:
            self.device_logger.log_changes(changes, data.surplus_power, self.device_manager)

    def log_status(self, surplus_power: float) -> None:
        """Loggt den aktuellen Gerätestatus"""
        if not self.device_manager or not self.config.logging.device_log_status:
            return

        devices = self.device_manager.get_devices_by_priority()
        self.device_logger.log_status(devices, surplus_power)

    def shutdown(self) -> None:
        """Fährt die Gerätesteuerung herunter"""
        if not self.device_manager:
            return

        self.logger.info("Schalte alle Geräte aus...")

        # Hole Hue Interface falls vorhanden
        hue_interface = None
        if self.energy_controller and hasattr(self.energy_controller, 'hue_interface'):
            hue_interface = self.energy_controller.hue_interface

        # Alle aktiven Geräte ausschalten
        for device in self.device_manager.get_active_devices():
            old_state = device.state

            # Versuche Hue Hardware auszuschalten
            if hue_interface:
                try:
                    success = hue_interface.switch_off(device.name)
                    if success:
                        self.logger.debug(f"Hue Hardware '{device.name}' beim Shutdown ausgeschaltet")
                    else:
                        self.logger.warning(f"Konnte Hue Hardware '{device.name}' beim Shutdown nicht ausschalten")
                except Exception as e:
                    self.logger.error(f"Hue Fehler beim Shutdown: {e}")

            # Laufzeit berechnen bevor Status geändert wird
            if device.last_state_change:
                runtime = int((datetime.now() - device.last_state_change).total_seconds() / 60)
                device.runtime_today += runtime
                self.logger.debug(f"Gerät '{device.name}' lief {runtime} Minuten, "
                                  f"Gesamt heute: {device.runtime_today} Minuten")

            device.state = DeviceState.OFF
            device.last_state_change = datetime.now()
            self.logger.info(f"Gerät '{device.name}' ausgeschaltet (Programmende)")

            # Event loggen
            if self.config.logging.device_log_events:
                self.device_logger.log_event(
                    device, "ausgeschaltet", "Programmende",
                    self.last_surplus_power or 0, old_state
                )

        # Tageszusammenfassung erstellen
        if self.config.logging.device_log_daily_summary:
            self.device_logger.create_daily_summary(
                self.device_manager.get_devices_by_priority(),
                self.file_handler.base_dir / self.config.directories.device_log_dir
            )

        # Speichere Gerätekonfiguration
        self.device_manager.save_devices()

    def reset_daily_stats(self) -> None:
        """Setzt die täglichen Gerätestatistiken zurück"""
        if self.energy_controller:
            # Erstelle Zusammenfassung vor Reset
            if self.config.logging.device_log_daily_summary and self.device_manager:
                self.device_logger.create_daily_summary(
                    self.device_manager.get_devices_by_priority(),
                    self.file_handler.base_dir / self.config.directories.device_log_dir
                )

            self.energy_controller.reset_daily_stats()
            self.logger.info("Tägliche Gerätestatistiken zurückgesetzt")

    def is_active(self) -> bool:
        """Prüft ob Gerätesteuerung aktiv ist"""
        return self.config.devices.enable_control and self.device_manager is not None