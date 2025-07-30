"""
Datenverarbeitung für den Solar Monitor.
"""

import logging
from typing import Optional, Dict, Any
from ..models import SolarData


class DataProcessor:
    """Verarbeitet und validiert Solar-Daten"""

    def __init__(self, config: Any):
        """
        Initialisiert den DataProcessor.

        Args:
            config: Konfigurationsobjekt
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Statistiken
        self.stats: Dict[str, Any] = {
            'updates': 0,
            'errors': 0,
            'last_update': None
        }

    def process_data(self, data: Optional[SolarData]) -> bool:
        """
        Verarbeitet empfangene Daten.

        Args:
            data: Solar-Daten oder None bei Fehler

        Returns:
            True bei erfolgreicher Verarbeitung
        """
        if data:
            self.stats['updates'] += 1
            return True
        else:
            self.stats['errors'] += 1
            return False

    def validate_data(self, data: SolarData) -> bool:
        """
        Validiert Solar-Daten auf Plausibilität.

        Args:
            data: Zu validierende Daten

        Returns:
            True wenn Daten plausibel
        """
        # Basis-Validierung
        if data.pv_power < 0:
            self.logger.warning("PV-Leistung negativ")
            return False

        if data.load_power < 0:
            self.logger.warning("Verbrauch negativ")
            return False

        # Plausibilitätsprüfungen
        max_pv_power = 20000  # 20kW Max
        if data.pv_power > max_pv_power:
            self.logger.warning(f"PV-Leistung unplausibel hoch: {data.pv_power}W")

        return True

    def get_statistics(self) -> Dict[str, Any]:
        """Gibt Verarbeitungsstatistiken zurück"""
        return self.stats.copy()