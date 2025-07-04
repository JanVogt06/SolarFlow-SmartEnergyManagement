"""
Verwaltung mehrerer Geräte für den Smart Energy Manager.
"""

import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

from .device import Device, DeviceState


class DeviceManager:
    """Verwaltet alle steuerbaren Geräte"""

    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialisiert den DeviceManager.

        Args:
            config_file: Pfad zur JSON-Konfigurationsdatei
        """
        self.logger = logging.getLogger(__name__)
        self.devices: List[Device] = []
        self.config_file = config_file or Path("devices.json")

        # Lade Geräte wenn Konfiguration existiert
        if self.config_file.exists():
            self.load_devices()

    def add_device(self, device: Device) -> None:
        """Fügt ein Gerät hinzu"""
        # Prüfe auf doppelte Namen
        if any(d.name == device.name for d in self.devices):
            raise ValueError(f"Gerät mit Namen '{device.name}' existiert bereits")

        self.devices.append(device)
        self.logger.info(f"Gerät '{device.name}' hinzugefügt (Priorität: {device.priority})")

    def remove_device(self, name: str) -> bool:
        """Entfernt ein Gerät"""
        for i, device in enumerate(self.devices):
            if device.name == name:
                self.devices.pop(i)
                self.logger.info(f"Gerät '{name}' entfernt")
                return True
        return False

    def get_device(self, name: str) -> Optional[Device]:
        """Gibt ein Gerät nach Namen zurück"""
        for device in self.devices:
            if device.name == name:
                return device
        return None

    def get_devices_by_priority(self) -> List[Device]:
        """Gibt Geräte sortiert nach Priorität zurück (1 = höchste)"""
        return sorted(self.devices, key=lambda d: d.priority)

    def get_active_devices(self) -> List[Device]:
        """Gibt alle eingeschalteten Geräte zurück"""
        return [d for d in self.devices if d.state == DeviceState.ON]

    def get_total_consumption(self) -> float:
        """Berechnet Gesamtverbrauch aller aktiven Geräte"""
        return sum(d.power_consumption for d in self.get_active_devices())

    def save_devices(self) -> None:
        """Speichert Geräte in JSON-Datei"""
        devices_data = []
        for device in self.devices:
            device_dict = {
                'name': device.name,
                'description': device.description,
                'power_consumption': device.power_consumption,
                'priority': device.priority,
                'min_runtime': device.min_runtime,
                'max_runtime_per_day': device.max_runtime_per_day,
                'switch_on_threshold': device.switch_on_threshold,
                'switch_off_threshold': device.switch_off_threshold,
                'allowed_time_ranges': [
                    [t[0].isoformat(), t[1].isoformat()]
                    for t in device.allowed_time_ranges
                ]
            }
            devices_data.append(device_dict)

        with open(self.config_file, 'w') as f:
            json.dump(devices_data, f, indent=2)

        self.logger.info(f"Gespeichert: {len(self.devices)} Geräte")

    def load_devices(self) -> None:
        """Lädt Geräte aus JSON-Datei"""
        if not self.config_file.exists():
            self.logger.info(f"Keine Gerätekonfiguration gefunden: {self.config_file}")
            return

        try:
            with open(self.config_file, 'r') as f:
                devices_data = json.load(f)

            self.devices.clear()
            for device_dict in devices_data:
                # Konvertiere Zeit-Strings zurück
                time_ranges = []
                for start_str, end_str in device_dict.get('allowed_time_ranges', []):
                    from datetime import time
                    start = time.fromisoformat(start_str)
                    end = time.fromisoformat(end_str)
                    time_ranges.append((start, end))

                device = Device(
                    name=device_dict['name'],
                    description=device_dict.get('description', ''),
                    power_consumption=device_dict['power_consumption'],
                    priority=device_dict['priority'],
                    min_runtime=device_dict.get('min_runtime', 0),
                    max_runtime_per_day=device_dict.get('max_runtime_per_day', 0),
                    switch_on_threshold=device_dict['switch_on_threshold'],
                    switch_off_threshold=device_dict['switch_off_threshold'],
                    allowed_time_ranges=time_ranges
                )
                self.devices.append(device)

            self.logger.info(f"Geladen: {len(self.devices)} Geräte")

        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Geräte: {e}")