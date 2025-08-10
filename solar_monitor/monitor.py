"""
Hauptmonitor-Klasse für den Fronius Solar Monitor.
"""

import logging
import time
import sys
from typing import Optional
from .api import FroniusAPI
from .config import Config
from .models import SolarData
from display import DisplayManager
from .core import (
    DataProcessor,
    StatsManager,
    DeviceController,
    LoggingCoordinator
)


class SolarMonitor:
    """Hauptklasse für den Solar Monitor"""

    def __init__(self, config: Optional[Config] = None) -> None:
        """
        Initialisiert den SolarMonitor.

        Args:
            config: Konfigurationsobjekt (optional)
        """
        self.config = config or Config()
        self.config.validate()

        # API initialisieren
        self.api = FroniusAPI(
            self.config.connection.fronius_ip,
            self.config.connection.request_timeout
        )

        # Display initialisieren
        self.display = DisplayManager(self.config)

        # Logging-System initialisieren
        self.logging_coordinator = LoggingCoordinator(self.config)
        self.logging_coordinator.setup_system_logging()

        # Core-Komponenten initialisieren
        self.data_processor = DataProcessor(self.config)
        self.stats_manager = StatsManager(
            self.config,
            self.display,
            self.logging_coordinator.stats_logger
        )
        self.device_controller = DeviceController(
            self.config,
            self.logging_coordinator.device_logger,
            self.logging_coordinator.file_handler
        )

        self.logger = logging.getLogger(__name__)
        self.running = False
        self.start_time: Optional[float] = None

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

        self.start_time = time.time()
        self.running = True

        try:
            self.run()
        except Exception as e:
            self.logger.error(f"Unerwarteter Fehler: {e}", exc_info=True)
            self.stop()

    def stop(self) -> None:
        """Stoppt den Monitor"""
        self.running = False

        # Live-Display aufräumen BEVOR andere Ausgaben kommen
        if self.config.display.use_live_display:
            self.display.cleanup_live_display()
            # Kurze Pause damit Terminal sich erholt
            time.sleep(0.1)

        # Statistiken ausgeben
        if self.start_time:
            runtime = time.time() - self.start_time
            stats = self.data_processor.get_statistics()
            self.logger.info(
                f"Monitor gestoppt. Laufzeit: {runtime:.0f}s, "
                f"Updates: {stats['updates']}, "
                f"Fehler: {stats['errors']}"
            )

        # Abschluss-Statistiken anzeigen
        self.stats_manager.show_final_stats()

        # Tagesstatistiken speichern
        self.stats_manager.save_current_stats()

        # Geräte herunterfahren
        self.device_controller.shutdown()

        # Logging-System schließen
        self.logging_coordinator.close()

    def run(self) -> None:
        """Hauptschleife des Monitors"""
        # Logging auf stderr umleiten wenn Live-Display aktiv
        if self.config.display.use_live_display:
            self._configure_stderr_logging()
            # Live Display EINMAL initialisieren
            self.display.live.initialize()
            # Clear screen für sauberen Start
            print("\033[2J\033[H", end='')

        self.logging_coordinator.log_startup_info(self.device_controller.is_active())

        consecutive_errors = 0
        max_consecutive_errors = 5

        try:
            while self.running:
                consecutive_errors = self._process_update_cycle(
                    consecutive_errors,
                    max_consecutive_errors
                )

                if consecutive_errors >= max_consecutive_errors:
                    # Bei Live-Display: Fehlermeldung ins Display integrieren
                    if self.config.display.use_live_display:
                        # Pausiere das Live Display für die Meldung
                        if self.display.live.live:
                            self.display.live.live.stop()
                        print("Zu viele aufeinanderfolgende Fehler, beende Monitor", file=sys.stderr)
                        time.sleep(2)
                    else:
                        self.logger.error("Zu viele aufeinanderfolgende Fehler, beende Monitor")
                    break

                # Warte bis zum nächsten Update
                time.sleep(self.config.timing.update_interval)

        except KeyboardInterrupt:
            # Kein print hier - wird in stop() behandelt
            pass
        finally:
            self.stop()

    def _configure_stderr_logging(self):
        """Konfiguriert Logging auf stderr für Live-Display"""
        # Alle StreamHandler auf stderr umleiten
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:  # Kopie der Liste
            if isinstance(handler, logging.StreamHandler):
                # Entferne alte Handler
                root_logger.removeHandler(handler)

        # Neuer Handler nur für stderr
        stderr_handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        stderr_handler.setFormatter(formatter)
        stderr_handler.setLevel(self.config.logging.log_level)
        root_logger.addHandler(stderr_handler)

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

            # Daten verarbeiten
            if self.data_processor.process_data(data):
                consecutive_errors = 0

                # Daten validieren
                if data and self.data_processor.validate_data(data):
                    self._handle_valid_data(data)

            else:
                consecutive_errors += 1
                self.logger.warning(
                    f"Keine Daten empfangen (Fehler {consecutive_errors}/{max_errors})"
                )

        except KeyboardInterrupt:
            raise  # Weiterleiten für sauberes Beenden
        except Exception as e:
            self.logger.error(f"Fehler im Update-Zyklus: {e}", exc_info=True)
            consecutive_errors += 1

        return consecutive_errors

    def _handle_valid_data(self, data: SolarData) -> None:
        """
        Verarbeitet valide Solar-Daten.

        Args:
            data: Validierte Solar-Daten
        """
        # Gerätesteuerung aktualisieren
        self.device_controller.update(data)

        # Verwende Live-Display wenn aktiviert
        if self.config.display.use_live_display:
            self.display.show_live_data(data, self.device_controller.device_manager)
        else:
            # Alte Anzeige-Methode
            self.display.show_solar_data(data, self.device_controller.device_manager)

        # Daten loggen
        self.logging_coordinator.log_solar_data(data)

        # Gerätestatus loggen
        self.device_controller.log_status(data.surplus_power)

        # Tagesstatistiken aktualisieren
        self.stats_manager.update(data)

        # Prüfe auf Datumswechsel für Geräte-Reset
        if data.timestamp and self.stats_manager.check_date_change(data.timestamp.date()):
            self.device_controller.reset_daily_stats()

    def get_current_data(self) -> Optional[SolarData]:
        """
        Holt die aktuellen Daten (für externe Verwendung).

        Returns:
            Aktuelle Solardaten oder None
        """
        return self.api.get_power_flow_data()

    def get_daily_stats(self):
        """
        Gibt die aktuellen Tagesstatistiken zurück.

        Returns:
            Tagesstatistiken
        """
        return self.stats_manager.get_current_stats()

    def get_device_manager(self):
        """
        Gibt den DeviceManager zurück.

        Returns:
            DeviceManager oder None
        """
        return self.device_controller.device_manager

    def get_energy_controller(self):
        """
        Gibt den EnergyController zurück.

        Returns:
            EnergyController oder None
        """
        return self.device_controller.energy_controller