"""
CSV Writer für das Logging-System.
"""

import csv
from pathlib import Path
from typing import Dict, Any, Optional, List, Set
from datetime import datetime
from .base_writer import BaseWriter


class CSVWriter(BaseWriter):
    """Writer für CSV-Dateien"""

    def __init__(self, config: Any, file_manager: Any):
        """
        Initialisiert den CSV Writer.

        Args:
            config: Konfigurationsobjekt
            file_manager: FileManager für Pfadverwaltung
        """
        super().__init__(config)
        self.file_manager = file_manager
        self.delimiter = config.csv.delimiter
        self.encoding = config.csv.encoding

        # Track welche Dateien bereits Header haben
        self._files_with_headers: Set[Path] = set()

        # Cache für dynamische Header (Device Status)
        self._dynamic_headers: Dict[str, List[str]] = {}

    def write(self, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Schreibt Daten in CSV-Datei.

        Args:
            data: Zu schreibende Daten
            metadata: Metadaten mit log_type

        Returns:
            True bei Erfolg
        """
        if not metadata or 'log_type' not in metadata:
            self.logger.error("Keine log_type in Metadaten")
            return False

        # Füge zu Buffer hinzu
        return super().write(data, metadata)

    def flush(self) -> bool:
        """
        Schreibt Buffer in CSV-Dateien.

        Returns:
            True bei Erfolg
        """
        if not self._buffer:
            return True

        # Gruppiere Buffer nach log_type
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for entry in self._buffer:
            log_type = entry['metadata'].get('log_type')
            if log_type not in grouped:
                grouped[log_type] = []
            grouped[log_type].append(entry)

        # Schreibe jede Gruppe
        success = True
        for log_type, entries in grouped.items():
            if not self._write_group(log_type, entries):
                success = False

        # Buffer leeren
        self._buffer.clear()
        return success

    def _write_group(self, log_type: str, entries: List[Dict[str, Any]]) -> bool:
        """
        Schreibt eine Gruppe von Einträgen.

        Args:
            log_type: Typ des Logs
            entries: Liste von Einträgen

        Returns:
            True bei Erfolg
        """
        try:
            # Hole aktuellen Pfad
            filepath = self.file_manager.get_current_path(log_type)

            # Stelle sicher dass Verzeichnis existiert
            filepath.parent.mkdir(parents=True, exist_ok=True)

            # Prüfe ob Header geschrieben werden muss
            file_exists = filepath.exists()
            write_header = filepath not in self._files_with_headers and not file_exists

            # Hole Feldnamen
            fieldnames = self._get_fieldnames(log_type, entries[0]['data'])

            # Öffne Datei
            mode = 'w' if write_header else 'a'
            with open(filepath, mode, newline='', encoding=self.encoding) as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=fieldnames,
                    delimiter=self.delimiter
                )

                # Schreibe Header wenn nötig
                if write_header:
                    # Spezielle Header für device_status
                    if log_type == 'device_status':
                        self._write_device_status_header(f, entries[0]['data'])
                    else:
                        writer.writeheader()

                    self._files_with_headers.add(filepath)

                    # Session-Info wenn konfiguriert (außer für device_status)
                    if self.config.csv.include_info_row and log_type != 'device_status':
                        self._write_session_info(f, log_type)

                # Schreibe Daten
                for entry in entries:
                    writer.writerow(entry['data'])

            return True

        except Exception as e:
            self.logger.error(f"Fehler beim Schreiben nach {log_type}: {e}")
            return False

    def _get_fieldnames(self, log_type: str, sample_data: Dict[str, Any]) -> List[str]:
        """
        Bestimmt die Feldnamen für einen Log-Typ.

        Args:
            log_type: Typ des Logs
            sample_data: Beispiel-Daten

        Returns:
            Liste von Feldnamen
        """
        # Für Device Status: Dynamisch aus Daten
        if log_type == 'device_status':
            return sorted(sample_data.keys())

        # Sonst: Feste Reihenfolge
        field_orders = {
            'solar': [
                'timestamp', 'pv_power', 'grid_power', 'battery_power',
                'load_power', 'battery_soc', 'total_production',
                'feed_in_power', 'grid_consumption', 'self_consumption',
                'autarky_rate', 'surplus_power'
            ],
            'stats': [
                'date', 'runtime_hours', 'pv_energy', 'consumption_energy',
                'self_consumption_energy', 'feed_in_energy', 'grid_energy',
                'grid_energy_day', 'grid_energy_night', 'battery_charge_energy',
                'battery_discharge_energy', 'pv_power_max', 'consumption_power_max',
                'feed_in_power_max', 'grid_power_max', 'surplus_power_max',
                'battery_soc_min', 'battery_soc_max', 'autarky_avg',
                'self_sufficiency_rate', 'cost_grid_consumption',
                'revenue_feed_in', 'cost_saved', 'total_benefit',
                'cost_without_solar'
            ],
            'device_event': [
                'timestamp', 'device_name', 'action', 'from_state',
                'to_state', 'reason', 'surplus_power', 'device_power',
                'on_threshold', 'off_threshold', 'runtime_today', 'priority'
            ]
        }

        return field_orders.get(log_type, sorted(sample_data.keys()))

    def _write_device_status_header(self, file_handle: Any, sample_data: Dict[str, Any]) -> None:
        """
        Schreibt spezielle Header für Device Status.

        Args:
            file_handle: Offene Datei
            sample_data: Beispiel-Daten für Header-Generierung
        """
        # Erstelle lesbare Header basierend auf den Daten-Keys
        headers = []

        # Timestamp immer zuerst
        headers.append("Zeitstempel" if self.config.csv.use_german_headers else "Timestamp")

        # Sammle alle Geräte-Keys
        device_keys = []
        for key in sorted(sample_data.keys()):
            if key.endswith('_state'):
                device_name = key.replace('_state', '').replace('_', ' ').title()
                device_keys.append((device_name, key.replace('_state', '')))

        # Füge Geräte-Header hinzu
        for device_name, device_key in device_keys:
            if self.config.csv.use_german_headers:
                headers.extend([
                    f"{device_name} Status",
                    f"{device_name} Laufzeit (min)"
                ])
            else:
                headers.extend([
                    f"{device_name} State",
                    f"{device_name} Runtime (min)"
                ])

        # Zusammenfassungs-Header
        if self.config.csv.use_german_headers:
            headers.extend([
                "Gesamt Ein",
                "Gesamtverbrauch (W)",
                "Überschuss (W)",
                "Genutzter Überschuss (W)"
            ])
        else:
            headers.extend([
                "Total On",
                "Total Consumption (W)",
                "Surplus (W)",
                "Used Surplus (W)"
            ])

        # Schreibe Header
        writer = csv.writer(file_handle, delimiter=self.delimiter)
        writer.writerow(headers)

    def _write_session_info(self, file_handle: Any, log_type: str) -> None:
        """
        Schreibt Session-Info in Datei.

        Args:
            file_handle: Offene Datei
            log_type: Typ des Logs
        """
        writer = csv.writer(file_handle, delimiter=self.delimiter)

        info_lines = [
            f"# {log_type.upper()} Log",
            f"# Erstellt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"# CSV-Format: Delimiter='{self.delimiter}', Encoding='{self.encoding}'"
        ]

        for line in info_lines:
            writer.writerow([line])

        # Leerzeile nach Info
        writer.writerow([])

    def write_header(self, headers: List[str], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Explizites Header-Schreiben (für spezielle Fälle).

        Args:
            headers: Header-Liste
            metadata: Metadaten mit log_type

        Returns:
            True bei Erfolg
        """
        if not metadata or 'log_type' not in metadata:
            return False

        log_type = metadata['log_type']
        filepath = self.file_manager.get_current_path(log_type)

        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)

            with open(filepath, 'w', newline='', encoding=self.encoding) as f:
                writer = csv.writer(f, delimiter=self.delimiter)
                writer.writerow(headers)
                self._files_with_headers.add(filepath)

            return True

        except Exception as e:
            self.logger.error(f"Fehler beim Header-Schreiben: {e}")
            return False