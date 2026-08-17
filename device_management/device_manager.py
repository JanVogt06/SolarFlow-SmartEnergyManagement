"""
Verwaltung mehrerer Geräte für den Smart Energy Manager.
"""

import json
import logging
import threading
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datetime import time, datetime

from utils import read_json, write_json
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
        self.config_file = config_file or Path(__file__).resolve().parent.parent / "devices.json"

        # RLock, weil sich Methoden gegenseitig aufrufen (add_device → get_device)
        self._lock = threading.RLock()

        if self.config_file.exists():
            self.load_devices()

    def add_device(self, device: Device) -> None:
        """Fügt ein Gerät hinzu"""
        with self._lock:
            if any(d.name == device.name for d in self.devices):
                raise ValueError(f"Gerät mit Namen '{device.name}' existiert bereits")

            self.devices.append(device)
            self.logger.info(f"Gerät '{device.name}' hinzugefügt (Priorität: {device.priority})")

    def remove_device(self, name: str) -> bool:
        """Entfernt ein Gerät"""
        with self._lock:
            for i, device in enumerate(self.devices):
                if device.name == name:
                    self.devices.pop(i)
                    self.logger.info(f"Gerät '{name}' entfernt")
                    return True
        return False

    def get_device(self, name: str) -> Optional[Device]:
        """Gibt ein Gerät nach Namen zurück"""
        with self._lock:
            for device in self.devices:
                if device.name == name:
                    return device
        return None

    def get_devices_by_priority(self) -> List[Device]:
        """Gibt Geräte sortiert nach Priorität zurück (1 = höchste).

        Liefert eine NEUE Liste (Snapshot) — Aufrufer können sicher iterieren,
        auch wenn parallel über die API Geräte hinzugefügt/entfernt werden.
        """
        with self._lock:
            return sorted(self.devices, key=lambda d: d.priority)

    def get_active_devices(self) -> List[Device]:
        """Gibt alle eingeschalteten Geräte zurück (Snapshot-Liste)"""
        with self._lock:
            return [d for d in self.devices if d.state == DeviceState.ON]

    def get_total_consumption(self) -> float:
        """Berechnet Gesamtverbrauch aller aktiven Geräte"""
        with self._lock:
            return sum(d.power_consumption for d in self.devices if d.state == DeviceState.ON)

    def snapshot_devices(self) -> List[Device]:
        """Gibt einen Snapshot der Geräteliste zurück (sicher zum Iterieren)."""
        with self._lock:
            return list(self.devices)

    def _validate_device_config(self, device_dict: Dict[str, Any]) -> List[str]:
        """
        Validiert eine Gerätekonfiguration mit verbesserter Zeitbereichs-Validierung.

        Args:
            device_dict: Dictionary mit Gerätekonfiguration

        Returns:
            Liste von Fehlermeldungen (leer wenn alles ok)
        """
        errors = []

        required_fields = ['name', 'power_consumption', 'priority',
                           'switch_on_threshold', 'switch_off_threshold']

        for field in required_fields:
            if field not in device_dict:
                errors.append(f"Pflichtfeld '{field}' fehlt")

        if 'name' in device_dict:
            if not isinstance(device_dict['name'], str) or not device_dict['name'].strip():
                errors.append("Name muss ein nicht-leerer String sein")

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

        if ('switch_on_threshold' in device_dict and 'switch_off_threshold' in device_dict):
            try:
                on_threshold = float(device_dict['switch_on_threshold'])
                off_threshold = float(device_dict['switch_off_threshold'])
                if off_threshold > on_threshold:
                    errors.append("Ausschalt-Schwellwert darf nicht höher als Einschalt-Schwellwert sein")
            except (ValueError, TypeError):
                pass  # Fehler wurde schon oben erfasst

        if 'allowed_time_ranges' in device_dict:
            time_errors = self._validate_time_ranges_config(device_dict['allowed_time_ranges'])
            errors.extend(time_errors)

        return errors

    def _validate_time_ranges_config(self, time_ranges: Any) -> List[str]:
        """
        Validiert Zeitbereichs-Konfiguration detailliert.

        Args:
            time_ranges: Zeitbereichs-Konfiguration aus JSON

        Returns:
            Liste von Fehlermeldungen
        """
        errors = []

        if not isinstance(time_ranges, list):
            return ["allowed_time_ranges muss eine Liste sein"]

        valid_ranges = []

        for i, time_range in enumerate(time_ranges):
            if not isinstance(time_range, list) or len(time_range) != 2:
                errors.append(f"Zeitbereich {i + 1} muss eine Liste mit 2 Zeiten sein [start, ende]")
                continue

            start_str, end_str = time_range

            try:
                start_time = time.fromisoformat(start_str)
            except (ValueError, TypeError, AttributeError):
                errors.append(
                    f"Zeitbereich {i + 1}, Startzeit: Ungültiges Format '{start_str}' "
                    f"(erwartet: HH:MM:SS oder HH:MM)"
                )
                continue

            try:
                end_time = time.fromisoformat(end_str)
            except (ValueError, TypeError, AttributeError):
                errors.append(
                    f"Zeitbereich {i + 1}, Endzeit: Ungültiges Format '{end_str}' "
                    f"(erwartet: HH:MM:SS oder HH:MM)"
                )
                continue

            if start_time == end_time and start_time != time(0, 0):
                errors.append(
                    f"Zeitbereich {i + 1}: Start und Ende sind identisch ({start_str}). "
                    f"Das Gerät würde nur zu dieser exakten Zeit laufen."
                )

            valid_ranges.append((start_time, end_time, i))

        if len(valid_ranges) >= 2:
            overlap_warnings = self._check_time_overlaps(valid_ranges)
            if overlap_warnings:
                for warning in overlap_warnings:
                    self.logger.warning(warning)

        return errors

    def _check_time_overlaps(self, valid_ranges: List[Tuple[time, time, int]]) -> List[str]:
        """
        Prüft auf überlappende Zeitbereiche.

        Args:
            valid_ranges: Liste von (start, end, original_index) Tupeln

        Returns:
            Liste von Warnmeldungen
        """
        warnings = []

        intervals = []
        for start, end, idx in valid_ranges:
            start_min = start.hour * 60 + start.minute
            end_min = end.hour * 60 + end.minute

            if start <= end:
                intervals.append([(start_min, end_min, idx)])
            else:
                intervals.append([
                    (start_min, 24 * 60, idx),
                    (0, end_min, idx)
                ])

        for i in range(len(intervals)):
            for j in range(i + 1, len(intervals)):
                for int1 in intervals[i]:
                    for int2 in intervals[j]:
                        if Device._check_interval_overlap(int1[:2], int2[:2]):
                            idx1, idx2 = int1[2], int2[2]
                            warnings.append(
                                f"Zeitbereiche {idx1 + 1} und {idx2 + 1} überlappen sich. "
                                f"Das kann zu unerwartetem Verhalten führen."
                            )
                            break
                    if warnings:
                        break

        return warnings

    def save_devices(self) -> bool:
        """Speichert Geräte in die JSON-Datei.

        Erstellt unter Lock einen Snapshot der zu serialisierenden Daten,
        damit parallele Mutationen während des Schreibvorgangs nicht zu
        inkonsistentem JSON führen.

        Returns:
            True wenn die Datei geschrieben werden konnte
        """
        with self._lock:
            devices_data = [
                {
                    'name': device.name,
                    'description': device.description,
                    'power_consumption': device.power_consumption,
                    'priority': int(device.priority),
                    'min_runtime': device.min_runtime,
                    'max_runtime_per_day': device.max_runtime_per_day,
                    'switch_on_threshold': device.switch_on_threshold,
                    'switch_off_threshold': device.switch_off_threshold,
                    'allowed_time_ranges': [
                        [start.isoformat(), end.isoformat()]
                        for start, end in device.allowed_time_ranges
                    ]
                }
                for device in self.devices
            ]

        if not write_json(self.config_file, devices_data):
            self.logger.error(
                f"Geräte konnten nicht nach {self.config_file} geschrieben werden - "
                f"Änderungen gehen beim Neustart verloren"
            )
            return False

        self.logger.info(f"Gespeichert: {len(devices_data)} Geräte")
        return True

    def load_devices(self) -> None:
        """Lädt Geräte aus JSON-Datei mit verbesserter Validierung"""
        try:
            devices_data = read_json(self.config_file)

            if devices_data is None:
                self.logger.warning(
                    f"Keine oder leere Gerätekonfiguration: {self.config_file} - "
                    f"starte mit leerer Geräteliste. "
                    f"Geräte können über die API hinzugefügt werden."
                )
                with self._lock:
                    self.devices.clear()
                return

            all_errors = []
            valid_devices = []

            for i, device_dict in enumerate(devices_data):
                errors = self._validate_device_config(device_dict)
                if errors:
                    device_name = device_dict.get('name', f'Gerät {i + 1}')
                    all_errors.append(f"\n{device_name}:\n  " + "\n  ".join(errors))
                else:
                    valid_devices.append((i, device_dict))

            if all_errors:
                error_msg = "Fehler in der Gerätekonfiguration:" + "".join(all_errors)
                self.logger.error(error_msg)

                if valid_devices:
                    self.logger.warning(
                        f"{len(valid_devices)} von {len(devices_data)} Geräten "
                        f"sind gültig und könnten geladen werden."
                    )
                    devices_data = [device_dict for _, device_dict in valid_devices]
                else:
                    raise ValueError("Keine gültigen Geräte in der Konfiguration")

            new_devices: List[Device] = []
            for device_dict in devices_data:
                time_ranges = []
                for start_str, end_str in device_dict.get('allowed_time_ranges', []):
                    try:
                        start = time.fromisoformat(start_str)
                    except ValueError:
                        start = datetime.strptime(start_str, "%H:%M").time()

                    try:
                        end = time.fromisoformat(end_str)
                    except ValueError:
                        end = datetime.strptime(end_str, "%H:%M").time()

                    time_ranges.append((start, end))

                priority_int = int(device_dict['priority'])

                device = Device(
                    name=device_dict['name'],
                    description=device_dict.get('description', ''),
                    power_consumption=device_dict['power_consumption'],
                    priority=priority_int,
                    min_runtime=device_dict.get('min_runtime', 0),
                    max_runtime_per_day=device_dict.get('max_runtime_per_day', 0),
                    switch_on_threshold=device_dict['switch_on_threshold'],
                    switch_off_threshold=device_dict['switch_off_threshold'],
                    allowed_time_ranges=time_ranges
                )
                new_devices.append(device)

            with self._lock:
                self.devices.clear()
                self.devices.extend(new_devices)

            self.logger.info(f"Erfolgreich geladen: {len(new_devices)} Geräte")

            for device in self.get_devices_by_priority():
                self.logger.debug(
                    f"  {device.name}: {device.power_consumption}W, "
                    f"Priorität {device.priority}, "
                    f"Zeitbereiche: {device.format_time_ranges()}"
                )

        except json.JSONDecodeError as e:
            self.logger.error(f"Fehler beim Parsen der JSON-Datei: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unerwarteter Fehler beim Laden der Geräte: {e}")
            raise