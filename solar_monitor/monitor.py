"""
Hauptmonitor-Klasse für den Fronius Solar Monitor.
"""

import logging
import time
from typing import Optional

from .api import FroniusAPI
from .config import Config
from .display import DisplayFormatter
from .logger import DataLogger
from .models import SolarData


class SolarMonitor:
    """Hauptklasse für den Solar Monitor"""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialisiert den SolarMonitor.

        Args:
            config: Konfigurationsobjekt (optional)
        """
        self.config = config or Config()
        self.config.validate()

        # Komponenten initialisieren
        self.api = FroniusAPI(self.config.FRONIUS_IP, self.config.REQUEST_TIMEOUT)
        self.display = DisplayFormatter(self.config)
        self.logger = logging.getLogger(__name__)

        # Data Logger nur wenn aktiviert
        self.data_logger = None
        if self.config.ENABLE_DATA_LOGGING:
            self.data_logger = DataLogger(self.config.DATA_LOG_FILE)

        self.running = False
        self._setup_logging()

        # Statistiken
        self.stats = {
            'updates': 0,
            'errors': 0,
            'start_time': None,
            'last_update': None
        }

    def _setup_logging(self) -> None:
        """Konfiguriert das System-Logging"""
        # Root Logger konfigurieren
        root_logger = logging.getLogger()
        root_logger.setLevel(self.config.LOG_LEVEL)

        # Entferne alle bestehenden Handler
        root_logger.handlers = []

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(self.config.LOG_LEVEL)
        root_logger.addHandler(console_handler)

        # File Handler
        if self.config.LOG_FILE:
            try:
                file_handler = logging.FileHandler(self.config.LOG_FILE)
                file_handler.setFormatter(formatter)
                file_handler.setLevel(self.config.LOG_LEVEL)
                root_logger.addHandler(file_handler)
            except IOError as e:
                print(f"Warnung: Konnte Log-Datei nicht erstellen: {e}")

    def start(self) -> None:
        """Startet den Monitor"""
        self.logger.info("Fronius Solar Monitor wird gestartet...")
        self.logger.info(f"Konfiguration: IP={self.config.FRONIUS_IP}, "
                         f"Intervall={self.config.UPDATE_INTERVAL}s")

        # Teste Verbindung
        self.logger.info("Teste Verbindung zum Wechselrichter...")
        if self.api.test_connection():
            self.logger.info("Verbindung erfolgreich!")
        else:
            self.logger.warning("Verbindungstest fehlgeschlagen, versuche trotzdem fortzufahren...")

        # Versuche API-Version zu ermitteln
        api_version = self.api.get_api_version()
        if api_version:
            self.logger.info(f"Fronius API Version: {api_version}")

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
            self.logger.info(f"Monitor gestoppt. Laufzeit: {runtime:.0f}s, "
                             f"Updates: {self.stats['updates']}, "
                             f"Fehler: {self.stats['errors']}")

    def run(self) -> None:
        """Hauptschleife des Monitors"""
        self.logger.info("Monitor gestartet. Drücke Ctrl+C zum Beenden.")

        consecutive_errors = 0
        max_consecutive_errors = 5

        try:
            while self.running:
                try:
                    # Daten abrufen
                    data = self.api.get_power_flow_data()

                    if data:
                        # Erfolg - Error Counter zurücksetzen
                        consecutive_errors = 0

                        # Statistiken aktualisieren
                        self.stats['updates'] += 1
                        self.stats['last_update'] = time.time()

                        # Daten anzeigen
                        self.display.display_data(data)

                        # Daten loggen
                        if self.data_logger:
                            self.data_logger.log_data(data)
                            # Rotiere Log-Datei wenn nötig
                            if self.stats['updates'] % 100 == 0:
                                self.data_logger.rotate_if_needed()
                    else:
                        consecutive_errors += 1
                        self.stats['errors'] += 1
                        self.logger.warning(
                            f"Keine Daten empfangen (Fehler {consecutive_errors}/{max_consecutive_errors})")

                        if consecutive_errors >= max_consecutive_errors:
                            self.logger.error("Zu viele aufeinanderfolgende Fehler. Beende Monitor.")
                            break

                    # Warte bis zum nächsten Update
                    time.sleep(self.config.UPDATE_INTERVAL)

                except KeyboardInterrupt:
                    raise  # Weiterleiten für sauberes Beenden
                except Exception as e:
                    self.stats['errors'] += 1
                    self.logger.error(f"Fehler in der Hauptschleife: {e}", exc_info=True)
                    time.sleep(self.config.UPDATE_INTERVAL)

        except KeyboardInterrupt:
            print("\n\nBeende Programm...")
            self.stop()

    def get_current_data(self) -> Optional[SolarData]:
        """
        Holt die aktuellen Daten (für externe Verwendung).

        Returns:
            Aktuelle Solardaten oder None
        """
        return self.api.get_power_flow_data()

    def display_stats(self) -> None:
        """Zeigt Statistiken an"""
        if self.stats['start_time']:
            runtime = time.time() - self.stats['start_time']
            print(f"\nStatistiken:")
            print(f"  Laufzeit: {runtime:.0f}s")
            print(f"  Updates: {self.stats['updates']}")
            print(f"  Fehler: {self.stats['errors']}")
            print(f"  Fehlerrate: {self.stats['errors'] / max(1, self.stats['updates']) * 100:.1f}%")