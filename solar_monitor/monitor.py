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
from .daily_stats import DailyStats
from .daily_stats_logger import DailyStatsLogger


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
            self.data_logger = DataLogger(self.config)

        # Daily Stats Logger
        self.daily_stats_logger = None
        if self.config.ENABLE_DAILY_STATS_LOGGING:
            self.daily_stats_logger = DailyStatsLogger(self.config)

        self.running = False
        self._setup_logging()

        # Statistiken
        self.stats = {
            'updates': 0,
            'errors': 0,
            'start_time': None,
            'last_update': None
        }

        # Tagesstatistiken
        self.daily_stats = DailyStats()
        self.last_stats_display = None  # Zeitpunkt der letzten Statistik-Anzeige

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

        # Tagesstatistiken beim Beenden anzeigen
        if self.config.SHOW_DAILY_STATS and self.daily_stats.first_update:
            print("\n" + "="*60)
            print("ABSCHLUSS-STATISTIK")
            print("="*60)
            self.display.display_daily_stats(self.daily_stats)

        # Tagesstatistiken beim Beenden speichern
        if self.daily_stats_logger and self.daily_stats.runtime_hours > 0:
            self.daily_stats_logger.log_daily_stats(self.daily_stats)

    def _handle_consecutive_errors(self, consecutive_errors: int, max_errors: int = 5) -> bool:
        """
        Behandelt aufeinanderfolgende Fehler.

        Args:
            consecutive_errors: Anzahl der aufeinanderfolgenden Fehler
            max_errors: Maximale Anzahl erlaubter Fehler

        Returns:
            True wenn fortfahren, False wenn abbrechen
        """
        self.stats['errors'] += 1
        self.logger.warning(
            f"Keine Daten empfangen (Fehler {consecutive_errors}/{max_errors})")

        if consecutive_errors >= max_errors:
            self.logger.error("Zu viele aufeinanderfolgende Fehler. Beende Monitor.")
            return False
        return True

    def run(self) -> None:
        """Hauptschleife des Monitors"""
        self.logger.info("Monitor gestartet. Drücke Ctrl+C zum Beenden.")
        if self.config.SHOW_DAILY_STATS:
            interval_min = self.config.DAILY_STATS_INTERVAL / 60
            self.logger.info(f"Tagesstatistiken werden alle {interval_min:.0f} Minuten angezeigt.")

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

                        # Prüfe auf Tageswechsel
                        current_date = data.timestamp.date()
                        if self.daily_stats.date != current_date:
                            # Neuer Tag - speichere die gestrigen Statistiken
                            if self.daily_stats_logger and self.daily_stats.runtime_hours > 0:
                                self.daily_stats_logger.log_daily_stats(self.daily_stats)
                                self.logger.info(f"Tagesstatistik für {self.daily_stats.date} gespeichert")

                            # Reset für neuen Tag
                            self.daily_stats.reset()
                            self.daily_stats.date = current_date
                            self.daily_stats.first_update = data.timestamp

                        # Tagesstatistiken aktualisieren
                        self.daily_stats.update(data, self.config.UPDATE_INTERVAL)

                        # Tagesstatistiken periodisch anzeigen
                        if self.config.SHOW_DAILY_STATS:
                            if self.last_stats_display is None:
                                self.last_stats_display = time.time()
                            elif time.time() - self.last_stats_display >= self.config.DAILY_STATS_INTERVAL:
                                self.display.display_daily_stats(self.daily_stats)
                                self.last_stats_display = time.time()
                    else:
                        consecutive_errors += 1

                        # Fehlerbehandlung in eigener Methode
                        if not self._handle_consecutive_errors(consecutive_errors, max_consecutive_errors):
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

    def get_daily_stats(self) -> DailyStats:
        """
        Gibt die aktuellen Tagesstatistiken zurück.

        Returns:
            Tagesstatistiken
        """
        return self.daily_stats