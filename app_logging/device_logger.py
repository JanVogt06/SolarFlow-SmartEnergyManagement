"""
Geräte-Logging für den Smart Energy Manager.

Diese Datei sollte unter device_management/device_logger.py gespeichert werden.
"""

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List

from device_management.device import Device, DeviceState
from device_management.device_manager import DeviceManager


class DeviceLogger:
    """Klasse zum Logging der Geräte-Events und Statistiken"""

    def __init__(self, config, device_manager: DeviceManager):
        """
        Initialisiert den DeviceLogger mit Konfiguration.

        Args:
            config: Konfigurationsobjekt
            device_manager: DeviceManager-Instanz
        """
        self.config = config
        self.device_manager = device_manager
        self.logger = logging.getLogger(__name__)

        # Erstelle Verzeichnisstruktur
        self.base_dir = Path(config.DATA_LOG_DIR)
        self.device_dir = self.base_dir / config.DEVICE_LOG_DIR
        self.device_dir.mkdir(parents=True, exist_ok=True)

        # Event-Log: Eine Datei pro Session
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        events_base = config.DEVICE_EVENTS_BASE_NAME.replace('.csv', '')
        self.events_file = self.device_dir / f"{events_base}_{timestamp}.csv"

        # Status-Log: Eine Datei pro Tag
        date_stamp = datetime.now().strftime("%Y%m%d")
        status_base = config.DEVICE_STATUS_BASE_NAME.replace('.csv', '')
        self.status_file = self.device_dir / f"{status_base}_{date_stamp}.csv"

        self.logger.info(f"Geräte-Event-Log: {self.events_file.name}")
        self.logger.info(f"Geräte-Status-Log: {self.status_file.name}")

        # Header schreiben
        self._write_event_header()
        self._write_status_header_if_needed()

        # Letzter Status für Änderungserkennung
        self.last_device_states = {}

    def _write_event_header(self) -> None:
        """Schreibt die Header für die Event-CSV"""
        if self.config.CSV_USE_GERMAN_HEADERS:
            headers = [
                "Zeitstempel",
                "Gerät",
                "Aktion",
                "Von Status",
                "Zu Status",
                "Grund",
                "Überschuss (W)",
                "Geräteverbrauch (W)",
                "Schwellwert Ein (W)",
                "Schwellwert Aus (W)",
                "Laufzeit heute (min)",
                "Priorität"
            ]
        else:
            headers = [
                "Timestamp",
                "Device",
                "Action",
                "From State",
                "To State",
                "Reason",
                "Surplus (W)",
                "Device Power (W)",
                "On Threshold (W)",
                "Off Threshold (W)",
                "Runtime Today (min)",
                "Priority"
            ]

        try:
            with open(self.events_file, 'w', newline='', encoding=self.config.CSV_ENCODING) as f:
                writer = csv.writer(f, delimiter=self.config.CSV_DELIMITER)
                writer.writerow(headers)

                # Session-Info
                writer.writerow([])
                session_info = f"# Geräte-Event-Log erstellt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                writer.writerow([session_info])
                writer.writerow([f"# Anzahl konfigurierte Geräte: {len(self.device_manager.devices)}"])
                writer.writerow([])

            self.logger.info("Geräte-Event-CSV erstellt")

        except IOError as e:
            self.logger.error(f"Fehler beim Erstellen der Event-CSV: {e}")

    def _write_status_header_if_needed(self) -> None:
        """Schreibt die Header für die Status-CSV wenn Datei neu ist"""
        if self.status_file.exists():
            return

        if self.config.CSV_USE_GERMAN_HEADERS:
            headers = ["Zeitstempel"]
            # Dynamisch für jedes Gerät
            for device in self.device_manager.get_devices_by_priority():
                headers.extend([
                    f"{device.name} Status",
                    f"{device.name} Laufzeit (min)"
                ])
            headers.extend([
                "Gesamt Ein",
                "Gesamtverbrauch (W)",
                "Überschuss (W)",
                "Genutzter Überschuss (W)"
            ])
        else:
            headers = ["Timestamp"]
            # Dynamisch für jedes Gerät
            for device in self.device_manager.get_devices_by_priority():
                headers.extend([
                    f"{device.name} State",
                    f"{device.name} Runtime (min)"
                ])
            headers.extend([
                "Total On",
                "Total Consumption (W)",
                "Surplus (W)",
                "Used Surplus (W)"
            ])

        try:
            with open(self.status_file, 'w', newline='', encoding=self.config.CSV_ENCODING) as f:
                writer = csv.writer(f, delimiter=self.config.CSV_DELIMITER)
                writer.writerow(headers)

                # Info
                writer.writerow([])
                info = f"# Geräte-Status-Log für {datetime.now().strftime('%Y-%m-%d')}"
                writer.writerow([info])
                writer.writerow([])

            self.logger.info("Geräte-Status-CSV erstellt")

        except IOError as e:
            self.logger.error(f"Fehler beim Erstellen der Status-CSV: {e}")

    def log_device_event(self, device: Device, action: str, reason: str,
                        surplus_power: float, old_state: DeviceState) -> None:
        """
        Loggt ein Geräte-Event.

        Args:
            device: Betroffenes Gerät
            action: Durchgeführte Aktion
            reason: Grund für die Aktion
            surplus_power: Aktueller Überschuss
            old_state: Vorheriger Status
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Formatiere Zahlen
        def format_number(value: float, decimals: int = 0) -> str:
            if value is None:
                return "-"
            formatted = f"{value:.{decimals}f}"
            if self.config.CSV_DECIMAL_SEPARATOR == ",":
                formatted = formatted.replace(".", ",")
            return formatted

        row = [
            timestamp,
            device.name,
            action,
            old_state.value,
            device.state.value,
            reason,
            format_number(surplus_power),
            format_number(device.power_consumption),
            format_number(device.switch_on_threshold),
            format_number(device.switch_off_threshold),
            format_number(device.runtime_today),
            str(device.priority)
        ]

        try:
            with open(self.events_file, 'a', newline='', encoding=self.config.CSV_ENCODING) as f:
                writer = csv.writer(f, delimiter=self.config.CSV_DELIMITER)
                writer.writerow(row)

            self.logger.debug(f"Event geloggt: {device.name} - {action}")

        except IOError as e:
            self.logger.error(f"Fehler beim Schreiben des Events: {e}")

    def log_device_status(self, surplus_power: float) -> None:
        """
        Loggt den aktuellen Status aller Geräte.

        Args:
            surplus_power: Aktueller Überschuss
        """
        # Prüfe ob neue Datei für neuen Tag benötigt wird
        current_date = datetime.now().strftime("%Y%m%d")
        expected_date = self.status_file.stem.split('_')[-1]

        if current_date != expected_date:
            # Neue Tagesdatei
            status_base = self.config.DEVICE_STATUS_BASE_NAME.replace('.csv', '')
            self.status_file = self.device_dir / f"{status_base}_{current_date}.csv"
            self._write_status_header_if_needed()

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Formatiere Zahlen
        def format_number(value: float, decimals: int = 0) -> str:
            if value is None:
                return "-"
            formatted = f"{value:.{decimals}f}"
            if self.config.CSV_DECIMAL_SEPARATOR == ",":
                formatted = formatted.replace(".", ",")
            return formatted

        # Baue Zeile auf
        row = [timestamp]

        total_on = 0
        total_consumption = 0.0

        # Status für jedes Gerät
        for device in self.device_manager.get_devices_by_priority():
            state_str = "1" if device.state == DeviceState.ON else "0"
            row.extend([
                state_str,
                format_number(device.runtime_today)
            ])

            if device.state == DeviceState.ON:
                total_on += 1
                total_consumption += device.power_consumption

        # Zusammenfassung
        used_surplus = min(total_consumption, max(0, surplus_power))
        row.extend([
            str(total_on),
            format_number(total_consumption),
            format_number(surplus_power),
            format_number(used_surplus)
        ])

        try:
            with open(self.status_file, 'a', newline='', encoding=self.config.CSV_ENCODING) as f:
                writer = csv.writer(f, delimiter=self.config.CSV_DELIMITER)
                writer.writerow(row)

        except IOError as e:
            self.logger.error(f"Fehler beim Schreiben des Status: {e}")

    def log_changes(self, changes: Dict[str, str], surplus_power: float) -> None:
        """
        Loggt Änderungen vom EnergyController.

        Args:
            changes: Dict mit Geräteänderungen {Name: Aktion}
            surplus_power: Aktueller Überschuss
        """
        for device_name, action in changes.items():
            device = self.device_manager.get_device(device_name)
            if device:
                # Bestimme alten Status aus dem letzten bekannten Zustand
                old_state = self.last_device_states.get(device_name, DeviceState.OFF)

                # Bestimme Grund basierend auf Aktion
                if "eingeschaltet" in action:
                    reason = f"Überschuss > {device.switch_on_threshold}W"
                elif "ausgeschaltet" in action:
                    if "Überschuss" in action:
                        reason = f"Überschuss < {device.switch_off_threshold}W"
                    elif "Zeit" in action:
                        reason = "Außerhalb erlaubter Zeit"
                    elif "Maximale" in action:
                        reason = "Maximale Tageslaufzeit erreicht"
                    else:
                        reason = "Manuell/System"
                else:
                    reason = action

                # Event loggen
                self.log_device_event(device, action, reason, surplus_power, old_state)

                # Status aktualisieren
                self.last_device_states[device_name] = device.state

    def log_daily_summary(self) -> None:
        """Erstellt eine Tageszusammenfassung"""
        summary_file = self.device_dir / f"device_summary_{datetime.now().strftime('%Y%m%d')}.txt"

        try:
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(f"Geräte-Tageszusammenfassung - {datetime.now().strftime('%d.%m.%Y')}\n")
                f.write("=" * 60 + "\n\n")

                for device in self.device_manager.get_devices_by_priority():
                    f.write(f"{device.name}:\n")
                    f.write(f"  Priorität: {device.priority}\n")
                    f.write(f"  Leistung: {device.power_consumption}W\n")
                    f.write(f"  Laufzeit heute: {device.runtime_today} Minuten\n")
                    f.write(f"  Energieverbrauch: {device.runtime_today * device.power_consumption / 60000:.2f} kWh\n")
                    f.write(f"  Status: {device.state.value}\n")
                    f.write("\n")

                # Gesamtstatistik
                total_energy = sum(d.runtime_today * d.power_consumption / 60000
                                 for d in self.device_manager.devices)
                f.write(f"\nGesamt-Energieverbrauch gesteuerte Geräte: {total_energy:.2f} kWh\n")

            self.logger.info(f"Tageszusammenfassung erstellt: {summary_file.name}")

        except IOError as e:
            self.logger.error(f"Fehler beim Erstellen der Zusammenfassung: {e}")