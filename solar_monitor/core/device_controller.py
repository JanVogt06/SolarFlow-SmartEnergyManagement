"""
Gerätesteuerungs-Integration für den Solar Monitor.
"""

import logging
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from device_management import DeviceManager, EnergyController, DeviceState
from device_management.interfaces import ISmartDeviceInterface, NullDeviceInterface
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
        self.device_interface: Optional[ISmartDeviceInterface] = None

        # Tracking
        self.last_device_update: Optional[float] = None
        self.last_surplus_power: Optional[float] = None

        if config.devices.enable_control:
            self._init_device_control()

    def _init_device_control(self) -> None:
        """Initialisiert die Gerätesteuerung.

        WICHTIG: Bei leerer/fehlerhafter Gerätekonfiguration wird die Steuerung
        NICHT deaktiviert - es wird mit leerer Geräteliste weitergearbeitet.
        Geräte können jederzeit über die API hinzugefügt werden.
        """
        config_file = Path(self.config.devices.config_file)

        # DeviceManager erstellen - behandelt leere Dateien graceful
        try:
            self.device_manager = DeviceManager(config_file)
        except Exception as e:
            self.logger.warning(
                f"Gerätekonfiguration konnte nicht geladen werden: {e} - "
                f"Starte mit leerer Geräteliste."
            )
            # DeviceManager ohne Datei erstellen (leere Liste)
            self.device_manager = DeviceManager(config_file=None)
            self.device_manager.config_file = config_file

        # Device Interface initialisieren (Hue Bridge etc.)
        try:
            self.device_interface = self._create_device_interface()
        except Exception as e:
            self.logger.error(f"Fehler bei Interface-Initialisierung: {e}")
            self.device_interface = NullDeviceInterface()

        # Energy Controller mit Interface erstellen
        try:
            self.energy_controller = EnergyController(
                self.device_manager,
                self.device_interface
            )

            # Setze Hysterese-Zeit
            self.energy_controller.hysteresis_time = timedelta(
                minutes=self.config.devices.hysteresis_minutes
            )
        except Exception as e:
            self.logger.error(f"Fehler bei EnergyController-Initialisierung: {e}")
            self.energy_controller = None

        self.logger.info(f"Gerätesteuerung aktiviert. Konfiguration: {config_file}")
        self.logger.info(f"Gefundene Geräte: {len(self.device_manager.devices)}")
        self.logger.info(f"Hardware-Interface: {self.device_interface.interface_type}")

        # Liste Geräte auf
        if self.device_manager.devices:
            self._list_devices()

        # Stelle sauberen Startzustand her
        self._ensure_clean_start_state()

    def _create_device_interface(self) -> ISmartDeviceInterface:
        """Erstellt das passende Device Interface basierend auf Konfiguration"""
        # HUE Interface
        if self.config.devices.enable_hue and self.config.devices.hue_bridge_ip:
            self.logger.info("Initialisiere Hue-Integration...")
            try:
                from device_management.hue_interface import HueInterface

                hue_interface = HueInterface(self.config.devices.hue_bridge_ip)
                if hue_interface.connect():
                    self.logger.info("Hue Bridge erfolgreich verbunden!")

                    # Zeige gefundene Hue-Geräte
                    hue_devices = hue_interface.list_devices()
                    if hue_devices:
                        self.logger.info(f"Gefundene Hue-Geräte ({len(hue_devices)}):")
                        for hd in hue_devices:
                            self.logger.info(f"  - {hd}")

                    return hue_interface
                else:
                    self.logger.warning("Hue Bridge Verbindung fehlgeschlagen!")
                    self.logger.info("Tipp: Beim ersten Start muss der Knopf auf der Bridge gedrückt werden!")

            except ImportError:
                self.logger.error("phue Library nicht installiert! Führe aus: pip install phue")
            except Exception as e:
                self.logger.error(f"Fehler bei Hue-Initialisierung: {e}")

        # Fallback: Null Interface (nur virtuelle Steuerung)
        self.logger.info("Verwende virtuelle Gerätesteuerung (ohne Hardware)")
        return NullDeviceInterface()

    def _list_devices(self) -> None:
        """Listet alle konfigurierten Geräte auf"""
        for device in self.device_manager.get_devices_by_priority():
            # Prüfe ob Gerät im Hardware-Interface verfügbar ist
            hw_status = ""
            if self.device_interface.interface_type != "null":
                if self.device_interface.is_device_available(device.name):
                    hw_status = f" [{self.device_interface.interface_type.upper()} OK]"
                else:
                    hw_status = f" [Nicht in {self.device_interface.interface_type.upper()}!]"

            self.logger.info(
                f"  - {device.name}: {device.power_consumption}W, "
                f"Priorität {device.priority}, "
                f"Schwellwerte: Ein={device.switch_on_threshold}W, "
                f"Aus={device.switch_off_threshold}W{hw_status}"
            )

    def _ensure_clean_start_state(self) -> None:
        """Stellt sicher, dass alle verwalteten Geräte beim Start aus sind"""
        if not self.device_interface or self.device_interface.interface_type == "null":
            return

        self.logger.info("Stelle sauberen Startzustand her - schalte alle verwalteten Geräte aus...")

        for device in self.device_manager.devices:
            # Prüfe ob Gerät im Interface verfügbar ist
            if self.device_interface.is_device_available(device.name):
                # Schalte aus, egal welcher Status
                if self.device_interface.switch_off(device.name):
                    self.logger.info(f"'{device.name}' ausgeschaltet (Startzustand)")

            # Setze virtuellen Status
            device.state = DeviceState.OFF
            device.last_state_change = datetime.now()
            device.runtime_today = 0  # Reset Tagesstatistik beim Start

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

        # Batterie-Ladestand (Default 100% wenn keine Batterie)
        battery_soc = data.battery_soc if data.battery_soc is not None else 100.0

        # Führe Update durch mit Batterie-Informationen
        changes = self.energy_controller.update(
            surplus_power=data.surplus_power,
            current_time=data.timestamp,
            battery_power=data.battery_power,
            battery_soc=battery_soc
        )

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

        # Alle aktiven Geräte ausschalten
        for device in self.device_manager.get_active_devices():
            old_state = device.state

            # Versuche Hardware auszuschalten
            if self.device_interface and self.device_interface.connected:
                try:
                    success = self.device_interface.switch_off(device.name)
                    if success:
                        self.logger.debug(f"Hardware '{device.name}' beim Shutdown ausgeschaltet")
                    else:
                        self.logger.warning(f"Konnte Hardware '{device.name}' beim Shutdown nicht ausschalten")
                except Exception as e:
                    self.logger.error(f"Hardware-Fehler beim Shutdown: {e}")

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

        # Device Interface trennen
        if self.device_interface and self.device_interface.connected:
            self.device_interface.disconnect()

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