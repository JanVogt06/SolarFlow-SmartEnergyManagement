"""
Hauptmonitor-Klasse für den Fronius Solar Monitor mit Gerätesteuerung und neuem Logging-System.
"""

import logging
import time
from datetime import datetime, timedelta, date as DateType
from typing import Optional, Dict, Tuple, Any
from pathlib import Path

from .api import FroniusAPI
from .config import Config
from display import DisplayManager
from .models import SolarData
from .daily_stats import DailyStats

# Neues Logging-System
from log_system import LogManager, SolarLogger, StatsLogger, DeviceLogger
from log_system.formatters import (
    SolarFormatter, StatsFormatter,
    DeviceEventFormatter, DeviceStatusFormatter
)
from log_system.writers import CSVWriter, DatabaseWriter
from log_system.handlers import FileHandler

from device_management import DeviceManager, EnergyController, DeviceState


class SolarMonitor:
    """Hauptklasse für den Solar Monitor mit Gerätesteuerung"""

    def __init__(self, config: Optional[Config] = None) -> None:
        """
        Initialisiert den SolarMonitor.

        Args:
            config: Konfigurationsobjekt (optional)
        """
        self.config: Config = config or Config()
        self.config.validate()

        # Komponenten initialisieren
        self.api: FroniusAPI = FroniusAPI(
            self.config.connection.fronius_ip,
            self.config.connection.request_timeout
        )
        self.display = DisplayManager(self.config)
        self.logger = logging.getLogger(__name__)

        # Neues Logging-System initialisieren
        self._init_logging_system()

        # Gerätesteuerung initialisieren
        self.device_manager: Optional[DeviceManager] = None
        self.energy_controller: Optional[EnergyController] = None
        if self.config.devices.enable_control:
            self._init_device_control()

        self.running: bool = False
        self._setup_system_logging()

        # Statistiken
        self.stats: Dict[str, Any] = {
            'updates': 0,
            'errors': 0,
            'start_time': None,
            'last_update': None
        }

        # Tagesstatistiken mit Config initialisieren
        self.daily_stats: DailyStats = DailyStats()
        self.daily_stats.set_config(self.config)
        self.last_stats_display: Optional[float] = None

        # Gerätesteuerung
        self.last_device_update: Optional[float] = None
        self.last_surplus_power: Optional[float] = None
        self.last_device_status_log: Optional[float] = None

    def _init_logging_system(self) -> None:
        """Initialisiert das neue Logging-System"""
        # LogManager erstellen
        self.log_manager = LogManager(self.config)

        # FileHandler für Pfadverwaltung
        self.file_handler = FileHandler(self.config)

        # Formatter registrieren
        self.log_manager.register_formatter('solar', SolarFormatter(self.config))
        self.log_manager.register_formatter('stats', StatsFormatter(self.config))
        self.log_manager.register_formatter('device_event', DeviceEventFormatter(self.config))
        self.log_manager.register_formatter('device_status', DeviceStatusFormatter(self.config))

        # Writer registrieren
        self.log_manager.register_writer('csv', CSVWriter(self.config, self.file_handler))
        if self.config.database.enable_database:
            self.log_manager.register_writer('database', DatabaseWriter(self.config))

        # High-Level Logger erstellen
        self.solar_logger = SolarLogger(self.log_manager)
        self.stats_logger = StatsLogger(self.log_manager)
        self.device_logger = DeviceLogger(self.log_manager)

        self.logger.info("Neues Logging-System initialisiert")

    def _init_device_control(self) -> None:
        """Initialisiert die Gerätesteuerung"""
        try:
            config_file = Path(self.config.devices.config_file)
            self.device_manager = DeviceManager(config_file)
            self.energy_controller = EnergyController(self.device_manager)

            # Setze Hysterese-Zeit
            self.energy_controller.hysteresis_time = timedelta(
                minutes=self.config.devices.hysteresis_minutes
            )

            self.logger.info(f"Gerätesteuerung aktiviert. Konfiguration: {config_file}")
            self.logger.info(f"Gefundene Geräte: {len(self.device_manager.devices)}")

            # Liste Geräte auf
            for device in self.device_manager.get_devices_by_priority():
                self.logger.info(
                    f"  - {device.name}: {device.power_consumption}W, "
                    f"Priorität {device.priority}, "
                    f"Schwellwerte: Ein={device.switch_on_threshold}W, "
                    f"Aus={device.switch_off_threshold}W"
                )

        except Exception as e:
            self.logger.error(f"Fehler bei der Initialisierung der Gerätesteuerung: {e}")
            self.config.devices.enable_control = False
            self.device_manager = None
            self.energy_controller = None

    def _setup_system_logging(self) -> None:
        """Konfiguriert das System-Logging"""
        # Root Logger konfigurieren
        root_logger = logging.getLogger()
        root_logger.setLevel(self.config.logging.log_level)

        # Entferne alle bestehenden Handler
        root_logger.handlers = []

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(self.config.logging.log_level)
        root_logger.addHandler(console_handler)

        # File Handler
        if self.config.logging.log_file:
            try:
                file_handler = logging.FileHandler(self.config.logging.log_file)
                file_handler.setFormatter(formatter)
                file_handler.setLevel(self.config.logging.log_level)
                root_logger.addHandler(file_handler)
            except IOError as e:
                print(f"Warnung: Konnte Log-Datei nicht erstellen: {e}")

    def start(self) -> None:
        """Startet den Monitor"""
        self.logger.info("Fronius Solar Monitor wird gestartet...")
        self.logger.info(
            f"Konfiguration: IP={self.config.connection.fronius_ip}, "
            f"Intervall={self.config.timing.update_interval}s"
        )

        # Teste Verbindung
        self.logger.info("Teste Verbindung zum Wechselrichter...")
        if self.api.test_connection():
            self.logger.info("Verbindung erfolgreich!")
        else:
            self.logger.warning("Verbindungstest fehlgeschlagen, versuche trotzdem fortzufahren...")

        self.stats['start_time'] = time.time()
        self.running = True

        try:
            self.run()
        except Exception as e:
            self.logger.error(f"Unerwarteter Fehler: {e}", exc_info=True)
            self.stop()

    def stop(self) -> None:
        """Stoppt den Monitor"""
        self.running = False

        # Statistiken ausgeben
        if self.stats['start_time']:
            runtime = time.time() - self.stats['start_time']
            self.logger.info(
                f"Monitor gestoppt. Laufzeit: {runtime:.0f}s, "
                f"Updates: {self.stats['updates']}, "
                f"Fehler: {self.stats['errors']}"
            )

        # Tagesstatistiken beim Beenden anzeigen
        if self.config.display.show_daily_stats and self.daily_stats.first_update:
            print("\n" + "="*60)
            print("ABSCHLUSS-STATISTIK")
            print("="*60)
            self.display.show_daily_stats(self.daily_stats)

        # Tagesstatistiken beim Beenden speichern
        if self.daily_stats.runtime_hours > 0:
            self.stats_logger.log(self.daily_stats)

        # Geräte beim Beenden ausschalten und zusammenfassen
        if self.energy_controller:
            self._shutdown_devices()

        # Logging-System sauber beenden
        self.log_manager.close_all()

    def _shutdown_devices(self) -> None:
        """Schaltet alle Geräte aus und erstellt Zusammenfassung"""
        self.logger.info("Schalte alle Geräte aus...")

        if self.device_manager:
            # Alle aktiven Geräte ausschalten
            for device in self.device_manager.get_active_devices():
                old_state = device.state
                device.state = DeviceState.OFF
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

    def run(self) -> None:
        """Hauptschleife des Monitors"""
        self._log_startup_info()

        consecutive_errors: int = 0
        max_consecutive_errors: int = 5

        try:
            while self.running:
                consecutive_errors = self._process_update_cycle(
                    consecutive_errors,
                    max_consecutive_errors
                )

                if consecutive_errors >= max_consecutive_errors:
                    break

                # Warte bis zum nächsten Update
                time.sleep(self.config.timing.update_interval)

        except KeyboardInterrupt:
            print("\n\nBeende Programm...")
            self.stop()

    def _log_startup_info(self) -> None:
        """Loggt Informationen beim Start"""
        self.logger.info("Monitor gestartet. Drücke Ctrl+C zum Beenden.")

        if self.config.display.show_daily_stats:
            interval_min = self.config.timing.daily_stats_interval / 60
            self.logger.info(f"Tagesstatistiken werden alle {interval_min:.0f} Minuten angezeigt.")

        if self.config.devices.enable_control:
            self.logger.info("Intelligente Gerätesteuerung ist aktiviert.")
            if self.config.logging.enable_device_logging:
                self.logger.info(
                    f"Geräte-Logging aktiviert (Events: {self.config.logging.device_log_events}, "
                    f"Status: {self.config.logging.device_log_status} alle "
                    f"{self.config.timing.device_log_interval}s)"
                )

    def _process_update_cycle(self, consecutive_errors: int, max_errors: int) -> int:
        """
        Verarbeitet einen Update-Zyklus.

        Args:
            consecutive_errors: Aktuelle Anzahl aufeinanderfolgender Fehler
            max_errors: Maximale erlaubte Fehler

        Returns:
            Aktualisierte Anzahl aufeinanderfolgender Fehler
        """
        try:
            # Daten abrufen
            data = self.api.get_power_flow_data()

            if data:
                # Erfolg - Error Counter zurücksetzen
                consecutive_errors = 0
                self._process_successful_data(data)
            else:
                consecutive_errors += 1
                self._handle_data_error(consecutive_errors, max_errors)

        except KeyboardInterrupt:
            raise  # Weiterleiten für sauberes Beenden
        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"Fehler in der Hauptschleife: {e}", exc_info=True)
            consecutive_errors += 1

        return consecutive_errors

    def _process_successful_data(self, data: SolarData) -> None:
        """
        Verarbeitet erfolgreich empfangene Daten.

        Args:
            data: Empfangene Solardaten
        """
        # Statistiken aktualisieren
        self._update_statistics()

        # Gerätesteuerung aktualisieren
        if self.config.devices.enable_control:
            self._update_devices(data)

        # Daten anzeigen
        self._display_data(data)

        # Daten loggen
        if self.config.logging.enable_data_logging:
            self.solar_logger.log(data)

        # Tagesstatistiken verarbeiten
        self._process_daily_statistics(data)

    def _update_statistics(self) -> None:
        """Aktualisiert die Laufzeit-Statistiken"""
        self.stats['updates'] += 1
        self.stats['last_update'] = time.time()

    def _display_data(self, data: SolarData) -> None:
        """
        Zeigt die Daten an.

        Args:
            data: Anzuzeigende Daten
        """
        self.display.show_solar_data(data, self.device_manager)

    def _process_daily_statistics(self, data: SolarData) -> None:
        """
        Verarbeitet Tagesstatistiken.

        Args:
            data: Aktuelle Solardaten
        """
        # Prüfe auf Tageswechsel
        if data.timestamp:
            current_date = data.timestamp.date()
            if self.daily_stats.date != current_date:
                self._handle_date_change(current_date, data)

        # Tagesstatistiken aktualisieren
        self.daily_stats.update(data, self.config.timing.update_interval)

        # Periodische Anzeige
        if self._should_display_daily_stats():
            self.display.show_daily_stats(self.daily_stats)
            self.last_stats_display = time.time()

    def _handle_date_change(self, new_date: DateType, data: SolarData) -> None:
        """
        Behandelt einen Tageswechsel.

        Args:
            new_date: Neues Datum
            data: Aktuelle Solardaten
        """
        # Speichere gestrige Statistiken
        if self.daily_stats.runtime_hours > 0:
            self.stats_logger.log(self.daily_stats)
            self.logger.info(f"Tagesstatistik für {self.daily_stats.date} gespeichert")

        # Reset für neuen Tag
        self.daily_stats.reset()
        self.daily_stats.date = new_date
        self.daily_stats.first_update = data.timestamp

        # Gerätestatistiken zurücksetzen
        self._check_daily_device_reset(new_date)

    def _should_display_daily_stats(self) -> bool:
        """Prüft ob Tagesstatistiken angezeigt werden sollen"""
        if not self.config.display.show_daily_stats:
            return False

        if self.last_stats_display is None:
            self.last_stats_display = time.time()
            return False

        return time.time() - self.last_stats_display >= self.config.timing.daily_stats_interval

    def _handle_data_error(self, consecutive_errors: int, max_errors: int) -> None:
        """
        Behandelt Fehler beim Datenabruf.

        Args:
            consecutive_errors: Anzahl aufeinanderfolgender Fehler
            max_errors: Maximale erlaubte Fehler
        """
        self.stats['errors'] += 1
        self.logger.warning(
            f"Keine Daten empfangen (Fehler {consecutive_errors}/{max_errors})"
        )

    # ====== DEVICE CONTROL METHODS ======

    def _update_devices(self, data: SolarData) -> None:
        """
        Aktualisiert die Gerätesteuerung basierend auf den Solardaten.

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

        # Periodisches Status-Logging
        self._log_device_status_if_needed(data)

        # Merke Werte für nächsten Vergleich
        self.last_surplus_power = data.surplus_power
        self.last_device_update = time.time()

    def _should_update_devices(self, data: SolarData) -> bool:
        """
        Prüft ob Geräte-Update notwendig ist.

        Args:
            data: Aktuelle Solardaten

        Returns:
            True wenn Update notwendig
        """
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
        """
        Verarbeitet Geräteänderungen.

        Args:
            changes: Dictionary mit Änderungen
            data: Aktuelle Solardaten
        """
        for device_name, action in changes.items():
            self.logger.info(f"Gerät '{device_name}' {action}")

        # Logge Änderungen
        if self.config.logging.device_log_events:
            self.device_logger.log_changes(changes, data.surplus_power, self.device_manager)

    def _log_device_status_if_needed(self, data: SolarData) -> None:
        """
        Loggt Gerätestatus wenn nötig.

        Args:
            data: Aktuelle Solardaten
        """
        if not self.config.logging.device_log_status:
            return

        if self.last_device_status_log is None:
            self.last_device_status_log = time.time()
        elif time.time() - self.last_device_status_log >= self.config.timing.device_log_interval:
            devices = self.device_manager.get_devices_by_priority()
            self.device_logger.log_status(devices, data.surplus_power)
            self.last_device_status_log = time.time()

    def _check_daily_device_reset(self, current_date: DateType) -> None:
        """
        Prüft und führt täglichen Reset der Gerätestatistiken durch.

        Args:
            current_date: Aktuelles Datum
        """
        if self.energy_controller and self.daily_stats.date != current_date:
            # Erstelle Tageszusammenfassung vor dem Reset
            if self.config.logging.device_log_daily_summary and self.device_manager:
                self.device_logger.create_daily_summary(
                    self.device_manager.get_devices_by_priority(),
                    self.file_handler.base_dir / self.config.directories.device_log_dir
                )

            # Reset durchführen
            self.energy_controller.reset_daily_stats()
            self.logger.info("Tägliche Gerätestatistiken zurückgesetzt")

    def get_current_data(self) -> Optional[SolarData]:
        """
        Holt die aktuellen Daten (für externe Verwendung).

        Returns:
            Aktuelle Solardaten oder None
        """
        return self.api.get_power_flow_data()

    def get_daily_stats(self) -> DailyStats:
        """
        Gibt die aktuellen Tagesstatistiken zurück.

        Returns:
            Tagesstatistiken
        """
        return self.daily_stats

    def get_device_manager(self) -> Optional[DeviceManager]:
        """
        Gibt den DeviceManager zurück (für externe Verwendung).

        Returns:
            DeviceManager oder None wenn Gerätesteuerung nicht aktiv
        """
        return self.device_manager

    def get_energy_controller(self) -> Optional[EnergyController]:
        """
        Gibt den EnergyController zurück (für externe Verwendung).

        Returns:
            EnergyController oder None wenn Gerätesteuerung nicht aktiv
        """
        return self.energy_controller