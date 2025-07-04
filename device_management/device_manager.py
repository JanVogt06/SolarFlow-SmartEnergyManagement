"""
Verwaltung mehrerer Geräte für den Smart Energy Manager - KORRIGIERT.
"""

import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import time

from .device import Device, DeviceState, DevicePriority


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

    def _validate_device_config(self, device_dict: Dict[str, Any]) -> List[str]:
        """
        Validiert eine Gerätekonfiguration.

        Args:
            device_dict: Dictionary mit Gerätekonfiguration

        Returns:
            Liste von Fehlermeldungen (leer wenn alles ok)
        """
        errors = []

        # Pflichtfelder
        required_fields = ['name', 'power_consumption', 'priority',
                          'switch_on_threshold', 'switch_off_threshold']

        for field in required_fields:
            if field not in device_dict:
                errors.append(f"Pflichtfeld '{field}' fehlt")

        # Name validieren
        if 'name' in device_dict:
            if not isinstance(device_dict['name'], str) or not device_dict['name'].strip():
                errors.append("Name muss ein nicht-leerer String sein")

        # Numerische Werte validieren
        numeric_fields = {
            'power_consumption': (0, float('inf'), "Leistungsaufnahme"),
            'priority': (1, 10, "Priorität"),
            'switch_on_threshold': (0, float('inf'), "Einschalt-Schwellwert"),
            'switch_off_threshold': (0, float('inf'), "Ausschalt-Schwellwert"),
            'min_runtime': (0, 1440, "Mindestlaufzeit"),  # Max 24 Stunden
            'max_runtime_per_day': (0, 1440, "Maximale Tageslaufzeit")
        }

        for field, (min_val, max_val, desc) in numeric_fields.items():
            if field in device_dict:
                try:
                    value = float(device_dict[field])
                    if not (min_val <= value <= max_val):
                        errors.append(f"{desc} muss zwischen {min_val} und {max_val} liegen")
                except (ValueError, TypeError):
                    errors.append(f"{desc} muss eine Zahl sein")

        # Schwellwerte-Logik prüfen
        if ('switch_on_threshold' in device_dict and 'switch_off_threshold' in device_dict):
            try:
                on_threshold = float(device_dict['switch_on_threshold'])
                off_threshold = float(device_dict['switch_off_threshold'])
                if off_threshold > on_threshold:
                    errors.append("Ausschalt-Schwellwert darf nicht höher als Einschalt-Schwellwert sein")
            except (ValueError, TypeError):
                pass  # Fehler wurde schon oben erfasst

        # Zeitbereiche validieren
        if 'allowed_time_ranges' in device_dict:
            if not isinstance(device_dict['allowed_time_ranges'], list):
                errors.append("allowed_time_ranges muss eine Liste sein")
            else:
                for i, time_range in enumerate(device_dict['allowed_time_ranges']):
                    if not isinstance(time_range, list) or len(time_range) != 2:
                        errors.append(f"Zeitbereich {i+1} muss eine Liste mit 2 Zeiten sein")
                    else:
                        # Validiere Zeitformat
                        for j, time_str in enumerate(time_range):
                            try:
                                time.fromisoformat(time_str)
                            except ValueError:
                                errors.append(f"Zeitbereich {i+1}, Zeit {j+1}: Ungültiges Zeitformat (erwartet: HH:MM:SS)")

        return errors

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

            # FIX 4: Validiere alle Geräte vor dem Laden
            all_errors = []
            for i, device_dict in enumerate(devices_data):
                errors = self._validate_device_config(device_dict)
                if errors:
                    device_name = device_dict.get('name', f'Gerät {i+1}')
                    all_errors.append(f"{device_name}: " + "; ".join(errors))

            if all_errors:
                error_msg = "Fehler in der Gerätekonfiguration:\n" + "\n".join(all_errors)
                self.logger.error(error_msg)
                raise ValueError(error_msg)

            # Lade Geräte wenn Validierung erfolgreich
            for device_dict in devices_data:
                # Konvertiere Zeit-Strings zurück
                time_ranges = []
                for start_str, end_str in device_dict.get('allowed_time_ranges', []):
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

            # Zeige Prioritätsübersicht
            for device in self.get_devices_by_priority():
                self.logger.debug(f"  {device.name}: Priorität {device.priority} "
                                f"({device.get_priority_name()})")

        except json.JSONDecodeError as e:
            self.logger.error(f"Fehler beim Parsen der JSON-Datei: {e}")
            raise
        except ValueError as e:
            # Validierungsfehler wurden bereits geloggt
            raise
        except Exception as e:
            self.logger.error(f"Unerwarteter Fehler beim Laden der Geräte: {e}")
            raise