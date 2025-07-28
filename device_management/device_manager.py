"""
Verwaltung mehrerer Geräte für den Smart Energy Manager - KORRIGIERT.
"""

import json
import log_system
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import time, datetime
from typing import Tuple

from .device import Device, DeviceState, DevicePriority


class DeviceManager:
    """Verwaltet alle steuerbaren Geräte"""

    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialisiert den DeviceManager.

        Args:
            config_file: Pfad zur JSON-Konfigurationsdatei
        """
        self.logger = log_system.getLogger(__name__)
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
        Validiert eine Gerätekonfiguration mit verbesserter Zeitbereichs-Validierung.

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

        # VERBESSERTE Zeitbereichs-Validierung
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

        # Prüfe Grundstruktur
        if not isinstance(time_ranges, list):
            return ["allowed_time_ranges muss eine Liste sein"]

        valid_ranges = []

        for i, time_range in enumerate(time_ranges):
            # Prüfe Format
            if not isinstance(time_range, list) or len(time_range) != 2:
                errors.append(f"Zeitbereich {i + 1} muss eine Liste mit 2 Zeiten sein [start, ende]")
                continue

            start_str, end_str = time_range

            # Validiere Zeitformat
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

            # Warne bei identischen Start- und Endzeiten (außer wenn beide 00:00)
            if start_time == end_time and start_time != time(0, 0):
                errors.append(
                    f"Zeitbereich {i + 1}: Start und Ende sind identisch ({start_str}). "
                    f"Das Gerät würde nur zu dieser exakten Zeit laufen."
                )

            valid_ranges.append((start_time, end_time, i))

        # Prüfe auf Überlappungen wenn mindestens 2 gültige Bereiche
        if len(valid_ranges) >= 2:
            overlap_warnings = self._check_time_overlaps(valid_ranges)
            if overlap_warnings:
                # Überlappungen sind Warnungen, keine Fehler
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

        # Konvertiere zu Minuten-Intervallen
        intervals = []
        for start, end, idx in valid_ranges:
            start_min = start.hour * 60 + start.minute
            end_min = end.hour * 60 + end.minute

            if start <= end:
                # Normaler Bereich
                intervals.append([(start_min, end_min, idx)])
            else:
                # Über Mitternacht - teile in zwei Bereiche
                intervals.append([
                    (start_min, 24 * 60, idx),
                    (0, end_min, idx)
                ])

        # Prüfe alle Kombinationen
        for i in range(len(intervals)):
            for j in range(i + 1, len(intervals)):
                for int1 in intervals[i]:
                    for int2 in intervals[j]:
                        if self._intervals_overlap_check(int1[:2], int2[:2]):
                            idx1, idx2 = int1[2], int2[2]
                            warnings.append(
                                f"Zeitbereiche {idx1 + 1} und {idx2 + 1} überlappen sich. "
                                f"Das kann zu unerwartetem Verhalten führen."
                            )
                            break
                    if warnings:
                        break

        return warnings

    def _intervals_overlap_check(self, interval1: Tuple[int, int], interval2: Tuple[int, int]) -> bool:
        """Prüft ob zwei Intervalle überlappen"""
        start1, end1 = interval1
        start2, end2 = interval2

        return not (end1 <= start2 or end2 <= start1)

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
        """Lädt Geräte aus JSON-Datei mit verbesserter Validierung"""
        if not self.config_file.exists():
            self.logger.info(f"Keine Gerätekonfiguration gefunden: {self.config_file}")
            return

        try:
            with open(self.config_file, 'r') as f:
                devices_data = json.load(f)

            self.devices.clear()

            # Validiere alle Geräte vor dem Laden
            all_errors = []
            valid_devices = []

            for i, device_dict in enumerate(devices_data):
                errors = self._validate_device_config(device_dict)
                if errors:
                    device_name = device_dict.get('name', f'Gerät {i + 1}')
                    all_errors.append(f"\n{device_name}:\n  " + "\n  ".join(errors))
                else:
                    valid_devices.append((i, device_dict))

            # Zeige alle Fehler auf einmal
            if all_errors:
                error_msg = "Fehler in der Gerätekonfiguration:" + "".join(all_errors)
                self.logger.error(error_msg)

                # Frage ob trotzdem die gültigen Geräte geladen werden sollen
                if valid_devices:
                    self.logger.warning(
                        f"{len(valid_devices)} von {len(devices_data)} Geräten "
                        f"sind gültig und könnten geladen werden."
                    )
                    # In Produktionsumgebung könnte hier eine Benutzerabfrage erfolgen
                    # Für jetzt: Lade nur die gültigen Geräte
                    devices_data = [device_dict for _, device_dict in valid_devices]
                else:
                    raise ValueError("Keine gültigen Geräte in der Konfiguration")

            # Lade die validierten Geräte
            for device_dict in devices_data:
                # Konvertiere Zeit-Strings
                time_ranges = []
                for start_str, end_str in device_dict.get('allowed_time_ranges', []):
                    # Unterstütze beide Formate: HH:MM und HH:MM:SS
                    try:
                        start = time.fromisoformat(start_str)
                    except ValueError:
                        # Versuche ohne Sekunden
                        start = datetime.strptime(start_str, "%H:%M").time()

                    try:
                        end = time.fromisoformat(end_str)
                    except ValueError:
                        end = datetime.strptime(end_str, "%H:%M").time()

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

            self.logger.info(f"Erfolgreich geladen: {len(self.devices)} Geräte")

            # Zeige Übersicht
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