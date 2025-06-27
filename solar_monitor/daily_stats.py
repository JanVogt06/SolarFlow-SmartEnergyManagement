"""
Tagesstatistiken für den Fronius Solar Monitor.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional

from .models import SolarData


@dataclass
class DailyStats:
    """Tagesstatistiken für die Solaranlage"""

    date: date = field(default_factory=date.today)

    # Energiewerte in kWh
    pv_energy: float = 0.0  # Gesamte PV-Produktion
    consumption_energy: float = 0.0  # Gesamtverbrauch
    feed_in_energy: float = 0.0  # Eingespeiste Energie
    grid_energy: float = 0.0  # Netzbezug
    battery_charge_energy: float = 0.0  # Batterie geladen
    battery_discharge_energy: float = 0.0  # Batterie entladen
    self_consumption_energy: float = 0.0  # Eigenverbrauch

    # Max Leistungswerte in W
    pv_power_max: float = 0.0
    consumption_power_max: float = 0.0
    feed_in_power_max: float = 0.0
    grid_power_max: float = 0.0
    surplus_power_max: float = 0.0

    # Batterie
    battery_soc_min: Optional[float] = None
    battery_soc_max: Optional[float] = None

    # Durchschnitte
    autarky_avg: float = 0.0

    # Zähler für Durchschnittsberechnung
    _sample_count: int = 0
    _autarky_sum: float = 0.0

    # Zeitstempel
    first_update: Optional[datetime] = None
    last_update: Optional[datetime] = None

    def update(self, data: SolarData, interval_seconds: int) -> None:
        """
        Aktualisiert die Statistiken mit neuen Daten.

        Args:
            data: Aktuelle Solardaten
            interval_seconds: Update-Intervall in Sekunden
        """
        # Timestamps
        if self.first_update is None:
            self.first_update = data.timestamp
        self.last_update = data.timestamp

        # Prüfe ob neuer Tag
        if data.timestamp.date() != self.date:
            self.reset()
            self.date = data.timestamp.date()
            self.first_update = data.timestamp

        # Energie = Leistung * Zeit (in kWh)
        hours = interval_seconds / 3600.0

        # Energiewerte akkumulieren
        self.pv_energy += data.pv_power * hours / 1000
        self.consumption_energy += data.load_power * hours / 1000
        self.feed_in_energy += data.feed_in_power * hours / 1000
        self.grid_energy += data.grid_consumption * hours / 1000
        self.self_consumption_energy += data.self_consumption * hours / 1000

        # Batterie-Energie
        if data.battery_charging:
            self.battery_charge_energy += data.battery_charge_power * hours / 1000
        else:
            self.battery_discharge_energy += data.battery_discharge_power * hours / 1000

        # Max Werte aktualisieren
        self.pv_power_max = max(self.pv_power_max, data.pv_power)
        self.consumption_power_max = max(self.consumption_power_max, data.load_power)
        self.feed_in_power_max = max(self.feed_in_power_max, data.feed_in_power)
        self.grid_power_max = max(self.grid_power_max, data.grid_consumption)
        self.surplus_power_max = max(self.surplus_power_max, data.surplus_power)

        # Batterie Min/Max
        if data.battery_soc is not None:
            if self.battery_soc_min is None:
                self.battery_soc_min = data.battery_soc
            else:
                self.battery_soc_min = min(self.battery_soc_min, data.battery_soc)

            if self.battery_soc_max is None:
                self.battery_soc_max = data.battery_soc
            else:
                self.battery_soc_max = max(self.battery_soc_max, data.battery_soc)

        # Durchschnitt Autarkie
        self._sample_count += 1
        self._autarky_sum += data.autarky_rate
        self.autarky_avg = self._autarky_sum / self._sample_count

    def reset(self) -> None:
        """Setzt alle Statistiken zurück"""
        self.date = date.today()

        # Energiewerte
        self.pv_energy = 0.0
        self.consumption_energy = 0.0
        self.feed_in_energy = 0.0
        self.grid_energy = 0.0
        self.battery_charge_energy = 0.0
        self.battery_discharge_energy = 0.0
        self.self_consumption_energy = 0.0

        # Max Werte
        self.pv_power_max = 0.0
        self.consumption_power_max = 0.0
        self.feed_in_power_max = 0.0
        self.grid_power_max = 0.0
        self.surplus_power_max = 0.0

        # Batterie
        self.battery_soc_min = None
        self.battery_soc_max = None

        # Durchschnitte
        self.autarky_avg = 0.0
        self._sample_count = 0
        self._autarky_sum = 0.0

        # Zeitstempel
        self.first_update = None
        self.last_update = None

    @property
    def runtime_hours(self) -> float:
        """Gibt die Laufzeit in Stunden zurück"""
        if self.first_update and self.last_update:
            delta = self.last_update - self.first_update
            return delta.total_seconds() / 3600.0
        return 0.0

    @property
    def self_sufficiency_rate(self) -> float:
        """Autarkiegrad basierend auf Energiewerten"""
        if self.consumption_energy > 0:
            return (self.self_consumption_energy / self.consumption_energy) * 100
        return 0.0