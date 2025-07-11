"""
Device Logger für den Smart Energy Manager.
"""

from typing import List, Any, Dict
from datetime import datetime
from pathlib import Path

from .base_logger import MultiFileLogger
from device_management import Device, DeviceState, DeviceManager
from .database.database_manager import DatabaseManager


class DeviceLogger(MultiFileLogger):
    """Logger für Geräte-Events und Status"""

    def __init__(self, config, device_manager: DeviceManager, db_manager: DatabaseManager):
        """
        Initialisiert den DeviceLogger.

        Args:
            config: Konfigurationsobjekt
            device_manager: DeviceManager-Instanz
            use_database: Ob Daten auch in die Datenbank geschrieben werden sollen
        """
        super().__init__(
            config=config,
            base_dir=config.DATA_LOG_DIR,
            sub_dir=config.DEVICE_LOG_DIR
        )

        self.db_manager = db_manager

        self.device_manager = device_manager

        # Datenbank-Manager initialisieren
        self.use_database = config.ENABLE_DATABASE
        self.db_manager = None
        if self.use_database:
            try:
                self.db_manager = DatabaseManager(self.config)
                self.logger.info("Datenbank-Integration aktiviert für DeviceLogger")
            except Exception as e:
                self.logger.error(f"Fehler bei Datenbank-Initialisierung: {e}")
                self.use_database = False

        # Rest der Initialisierung bleibt gleich...
        self.add_file('events', config.DEVICE_EVENTS_BASE_NAME, session_based=True)
        self.add_file('status', config.DEVICE_STATUS_BASE_NAME, session_based=False, timestamp_format="%Y%m%d")
        self._init_event_file()
        self._init_status_file()
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

        success = self.initialize_file('events', headers, info_lines)
        if not success:
            self.logger.error("Fehler beim Initialisieren der Event-Datei")

    def _init_status_file(self) -> None:
        """Initialisiert die Status-Log-Datei"""
        # Prüfe ob Datei bereits existiert UND initialisiert ist
        if 'status' in self.files and self._initialized_files.get('status', False):
            # Datei ist bereits initialisiert
            return

        # Prüfe ob physische Datei existiert
        if 'status' in self.files and self.csv_writer.file_exists(self.files['status']):
            # Datei existiert, markiere als initialisiert
            self._initialized_files['status'] = True
            return

        # Erstelle neue Datei mit Headers
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

        success = self.initialize_file('status', headers, info_lines)
        if not success:
            self.logger.error("Fehler beim Initialisieren der Status-Datei")
        else:
            self.logger.debug("Status-Datei erfolgreich initialisiert")

    def log_device_event(self, device: Device, action: str, reason: str,
                         surplus_power: float, old_state: DeviceState) -> bool:
        """
        Loggt ein Geräte-Event in CSV und Datenbank.

        Args:
            device: Betroffenes Gerät
            action: Durchgeführte Aktion
            reason: Grund für die Aktion
            surplus_power: Aktueller Überschuss
            old_state: Vorheriger Status

        Returns:
            True bei Erfolg
        """
        # CSV-Logging (existierende Implementierung)
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
            str(device.priority.value)
        ]

        csv_success = self.log_to_file('events', row)

        # Datenbank-Logging
        db_success = True
        if self.use_database and self.db_manager:
            db_success = self.db_manager.insert_device_event(
                device, action, reason, surplus_power, old_state
            )

        if csv_success:
            self.logger.debug(f"Event geloggt: {device.name} - {action}")

        return csv_success and db_success

    def log_device_status(self, surplus_power: float) -> bool:
        """
        Loggt den aktuellen Status aller Geräte in CSV und Datenbank.

        Args:
            surplus_power: Aktueller Überschuss

        Returns:
            True bei Erfolg
        """
        # CSV-Logging (existierende Implementierung bleibt gleich)
        csv_success = self._log_device_status_csv(surplus_power)

        # Datenbank-Logging
        db_success = True
        if self.use_database and self.db_manager:
            devices = self.device_manager.get_devices_by_priority()
            db_success = self.db_manager.insert_device_status_snapshot(
                devices, surplus_power
            )

        return csv_success and db_success

    def _log_device_status_csv(self, surplus_power: float) -> bool:
        """Hilfsmethode für CSV-Status-Logging (existierende Implementierung)"""
        # Der existierende Code aus log_device_status wird hierher verschoben
        # um die Methode übersichtlicher zu machen
        current_date = datetime.now().strftime("%Y%m%d")
        if 'status' in self.files:
            expected_date = self.files['status'].stem.split('_')[-1]
            if current_date != expected_date:
                self.add_file('status', self.config.DEVICE_STATUS_BASE_NAME,
                              session_based=False, timestamp_format="%Y%m%d")
                self._init_status_file()

        if not self._initialized_files.get('status', False):
            self.logger.warning("Status-Datei nicht initialisiert, versuche erneut...")
            self._init_status_file()
            if not self._initialized_files.get('status', False):
                self.logger.error("Konnte Status-Datei nicht initialisieren")
                return False

        timestamp = self.csv_formatter.format_timestamp(datetime.now())
        row = [timestamp]
        total_on = 0
        total_consumption = 0.0

        for device in self.device_manager.get_devices_by_priority():
            state_str = "1" if device.state == DeviceState.ON else "0"
            row.extend([
                state_str,
                self.csv_formatter.format_number(device.runtime_today)
            ])
            if device.state == DeviceState.ON:
                total_on += 1
                total_consumption += device.power_consumption

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