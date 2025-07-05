"""
Device Logger für den Smart Energy Manager.
"""

from typing import List, Any, Dict
from datetime import datetime
from pathlib import Path

from .base_logger import MultiFileLogger
from device_management import Device, DeviceState, DeviceManager


class DeviceLogger(MultiFileLogger):
    """Logger für Geräte-Events und Status"""

    def __init__(self, config, device_manager: DeviceManager):
        """
        Initialisiert den DeviceLogger.

        Args:
            config: Konfigurationsobjekt
            device_manager: DeviceManager-Instanz
        """
        super().__init__(
            config=config,
            base_dir=config.DATA_LOG_DIR,
            sub_dir=config.DEVICE_LOG_DIR
        )

        self.device_manager = device_manager

        # Event-Log: Eine Datei pro Session
        self.add_file(
            'events',
            config.DEVICE_EVENTS_BASE_NAME,
            session_based=True
        )

        # Status-Log: Eine Datei pro Tag
        self.add_file(
            'status',
            config.DEVICE_STATUS_BASE_NAME,
            session_based=False,
            timestamp_format="%Y%m%d"
        )

        # Header initialisieren
        self._init_event_file()
        self._init_status_file()

        # Letzter Status für Änderungserkennung
        self.last_device_states = {}

    def _init_event_file(self) -> None:
        """Initialisiert die Event-Log-Datei"""
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

        info_lines = self.csv_formatter.create_session_info(
            "Geräte-Event-Log",
            **{"Anzahl Geräte": len(self.device_manager.devices)}
        )

        self.initialize_file('events', headers, info_lines)

    def _init_status_file(self) -> None:
        """Initialisiert die Status-Log-Datei"""
        # Prüfe ob Datei bereits existiert
        if self.csv_writer.file_exists(self.files['status']):
            return

        # Dynamische Header basierend auf konfigurierten Geräten
        if self.config.CSV_USE_GERMAN_HEADERS:
            headers = ["Zeitstempel"]
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

        info_lines = self.csv_formatter.create_session_info(
            f"Geräte-Status-Log für {datetime.now().strftime('%Y-%m-%d')}",
            **{"Status-Intervall": f"{self.config.DEVICE_LOG_INTERVAL}s"}
        )

        self.initialize_file('status', headers, info_lines)

    def log_device_event(self, device: Device, action: str, reason: str,
                        surplus_power: float, old_state: DeviceState) -> bool:
        """
        Loggt ein Geräte-Event.

        Args:
            device: Betroffenes Gerät
            action: Durchgeführte Aktion
            reason: Grund für die Aktion
            surplus_power: Aktueller Überschuss
            old_state: Vorheriger Status

        Returns:
            True bei Erfolg
        """
        timestamp = self.csv_formatter.format_timestamp(datetime.now())

        row = [
            timestamp,
            device.name,
            action,
            old_state.value,
            device.state.value,
            reason,
            self.csv_formatter.format_number(surplus_power),
            self.csv_formatter.format_number(device.power_consumption),
            self.csv_formatter.format_number(device.switch_on_threshold),
            self.csv_formatter.format_number(device.switch_off_threshold),
            self.csv_formatter.format_number(device.runtime_today),
            str(device.priority.value)  # Numerischer Wert der Priorität
        ]

        success = self.log_to_file('events', row)
        if success:
            self.logger.debug(f"Event geloggt: {device.name} - {action}")

        return success

    def log_device_status(self, surplus_power: float) -> bool:
        """
        Loggt den aktuellen Status aller Geräte.

        Args:
            surplus_power: Aktueller Überschuss

        Returns:
            True bei Erfolg
        """
        # Prüfe ob neue Datei für neuen Tag benötigt wird
        current_date = datetime.now().strftime("%Y%m%d")
        expected_date = self.files['status'].stem.split('_')[-1]

        if current_date != expected_date:
            # Neue Tagesdatei
            self.add_file(
                'status',
                self.config.DEVICE_STATUS_BASE_NAME,
                session_based=False,
                timestamp_format="%Y%m%d"
            )
            self._init_status_file()

        timestamp = self.csv_formatter.format_timestamp(datetime.now())

        # Baue Zeile auf
        row = [timestamp]

        total_on = 0
        total_consumption = 0.0

        # Status für jedes Gerät
        for device in self.device_manager.get_devices_by_priority():
            state_str = "1" if device.state == DeviceState.ON else "0"
            row.extend([
                state_str,
                self.csv_formatter.format_number(device.runtime_today)
            ])

            if device.state == DeviceState.ON:
                total_on += 1
                total_consumption += device.power_consumption

        # Zusammenfassung
        used_surplus = min(total_consumption, max(0, surplus_power))
        row.extend([
            str(total_on),
            self.csv_formatter.format_number(total_consumption),
            self.csv_formatter.format_number(surplus_power),
            self.csv_formatter.format_number(used_surplus)
        ])

        return self.log_to_file('status', row)

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
                # Bestimme alten Status
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

    def log_daily_summary(self) -> bool:
        """
        Erstellt eine Tageszusammenfassung.

        Returns:
            True bei Erfolg
        """
        summary_file = self.log_dir / f"device_summary_{datetime.now().strftime('%Y%m%d')}.txt"

        try:
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(f"Geräte-Tageszusammenfassung - {datetime.now().strftime('%d.%m.%Y')}\n")
                f.write("=" * 60 + "\n\n")

                total_energy = 0.0

                for device in self.device_manager.get_devices_by_priority():
                    energy = device.runtime_today * device.power_consumption / 60000
                    total_energy += energy

                    f.write(f"{device.name}:\n")
                    f.write(f"  Priorität: {device.priority.value} ({device.priority.label()})\n")
                    f.write(f"  Leistung: {device.power_consumption}W\n")
                    f.write(f"  Laufzeit heute: {device.runtime_today} Minuten\n")
                    f.write(f"  Energieverbrauch: {energy:.2f} kWh\n")
                    f.write(f"  Status: {device.state.value}\n")
                    f.write("\n")

                f.write(f"\nGesamt-Energieverbrauch gesteuerte Geräte: {total_energy:.2f} kWh\n")

            self.logger.info(f"Tageszusammenfassung erstellt: {summary_file.name}")
            return True

        except IOError as e:
            self.logger.error(f"Fehler beim Erstellen der Zusammenfassung: {e}")
            return False