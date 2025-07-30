"""
Verwaltung der Tagesstatistiken.
"""

import logging
import time
from datetime import date as DateType
from typing import Optional, Any
from ..daily_stats import DailyStats
from ..models import SolarData


class StatsManager:
    """Verwaltet Tagesstatistiken und deren Anzeige"""

    def __init__(self, config: Any, display_manager: Any, stats_logger: Any):
        """
        Initialisiert den StatsManager.

        Args:
            config: Konfigurationsobjekt
            display_manager: Display Manager für Anzeige
            stats_logger: Logger für Statistiken
        """
        self.config = config
        self.display = display_manager
        self.stats_logger = stats_logger
        self.logger = logging.getLogger(__name__)

        # Tagesstatistiken mit Config initialisieren
        self.daily_stats = DailyStats()
        self.daily_stats.set_config(config)
        self.last_stats_display: Optional[float] = None

    def update(self, data: SolarData) -> None:
        """
        Aktualisiert die Tagesstatistiken.

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
        if self._should_display_stats():
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

    def _should_display_stats(self) -> bool:
        """Prüft ob Tagesstatistiken angezeigt werden sollen"""
        if not self.config.display.show_daily_stats:
            return False

        if self.last_stats_display is None:
            self.last_stats_display = time.time()
            return False

        return time.time() - self.last_stats_display >= self.config.timing.daily_stats_interval

    def save_current_stats(self) -> None:
        """Speichert die aktuellen Statistiken"""
        if self.daily_stats.runtime_hours > 0:
            self.stats_logger.log(self.daily_stats)

    def show_final_stats(self) -> None:
        """Zeigt Abschluss-Statistiken"""
        if self.config.display.show_daily_stats and self.daily_stats.first_update:
            print("\n" + "=" * 60)
            print("ABSCHLUSS-STATISTIK")
            print("=" * 60)
            self.display.show_daily_stats(self.daily_stats)

    def get_current_stats(self) -> DailyStats:
        """Gibt die aktuellen Tagesstatistiken zurück"""
        return self.daily_stats

    def check_date_change(self, current_date: DateType) -> bool:
        """
        Prüft auf Datumswechsel.

        Args:
            current_date: Zu prüfendes Datum

        Returns:
            True wenn Datum gewechselt hat
        """
        return self.daily_stats.date != current_date