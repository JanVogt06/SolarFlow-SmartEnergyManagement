"""
Persistente Laufzeit-Einstellungen für den Solar Monitor.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from utils import read_json, write_json


class SettingsStore:
    """Liest und schreibt die über die Weboberfläche änderbaren Einstellungen.

    Gespeicherte Werte haben Vorrang vor den Umgebungsvariablen; nicht
    gespeicherte Einstellungen bleiben weiterhin über die Umgebung steuerbar.
    """

    FIELDS: Dict[str, str] = {
        'fronius_ip': 'connection.fronius_ip',
        'update_interval': 'timing.update_interval',
        'electricity_price': 'costs.electricity_price',
        'electricity_price_night': 'costs.electricity_price_night',
        'feed_in_tariff': 'costs.feed_in_tariff',
        'enable_hue': 'devices.enable_hue',
        'hue_bridge_ip': 'devices.hue_bridge_ip',
        'hysteresis_minutes': 'devices.hysteresis_minutes',
        'manual_override_minutes': 'devices.manual_override_minutes',
        'min_battery_soc_on': 'devices.min_battery_soc_on',
        'min_battery_soc_off': 'devices.min_battery_soc_off'
    }

    def __init__(self, config: Any, path: Optional[Path] = None):
        """
        Initialisiert den SettingsStore.

        Args:
            config: Konfigurationsobjekt
            path: Pfad zur Einstellungsdatei (Standard: aus SETTINGS_FILE)
        """
        self.config = config
        self.path = Path(path or os.getenv("SETTINGS_FILE", "settings.json"))
        self.logger = logging.getLogger(__name__)

    def load(self) -> None:
        """Wendet die gespeicherten Einstellungen auf die Konfiguration an."""
        try:
            stored = read_json(self.path, {})
        except ValueError as e:
            self.logger.error(f"Einstellungsdatei {self.path} ist kein gültiges JSON: {e}")
            return

        if not isinstance(stored, dict) or not stored:
            return

        applied = self._apply(stored)
        self.logger.info(f"{len(applied)} gespeicherte Einstellungen aus {self.path} übernommen")

    def current(self) -> Dict[str, Any]:
        """
        Gibt die aktuell wirksamen Einstellungen zurück.

        Returns:
            Dict mit allen bekannten Einstellungen
        """
        return {name: self._get(path) for name, path in self.FIELDS.items()}

    def save(self, changes: Dict[str, Any]) -> bool:
        """
        Übernimmt Änderungen in die Konfiguration und schreibt sie in die Datei.

        Args:
            changes: Zu ändernde Einstellungen

        Returns:
            True wenn die Datei geschrieben werden konnte
        """
        applied = self._apply(changes)
        if not applied:
            return True

        stored = read_json(self.path, {})
        if not isinstance(stored, dict):
            stored = {}
        stored.update(applied)

        if not write_json(self.path, stored):
            self.logger.error(f"Einstellungen konnten nicht nach {self.path} geschrieben werden")
            return False

        self.logger.info(f"Einstellungen gespeichert: {', '.join(sorted(applied))}")
        return True

    def _apply(self, values: Dict[str, Any]) -> Dict[str, Any]:
        """Setzt bekannte Einstellungen in der Config und gibt sie zurück."""
        applied: Dict[str, Any] = {}

        for name, value in values.items():
            path = self.FIELDS.get(name)
            if path is None or value is None:
                continue
            self._set(path, value)
            applied[name] = value

        return applied

    def _get(self, path: str) -> Any:
        """Liest einen Wert über seinen Config-Pfad."""
        group, attribute = path.split('.')
        return getattr(getattr(self.config, group), attribute)

    def _set(self, path: str, value: Any) -> None:
        """Schreibt einen Wert über seinen Config-Pfad."""
        group, attribute = path.split('.')
        setattr(getattr(self.config, group), attribute, value)
