"""
Tagesstatistiken für die Solaranlage mit Kostenberechnung
"""

from dataclasses import dataclass, field
from datetime import datetime, date, time
from typing import Optional, Any

from .models import SolarData


@dataclass
class DailyStats:
    """Tagesstatistiken für die Solaranlage mit Kostenberechnung"""

    date: date = field(default_factory=date.today)

    pv_energy: float = 0.0  # Gesamte PV-Produktion
    consumption_energy: float = 0.0  # Gesamtverbrauch
    feed_in_energy: float = 0.0  # Eingespeiste Energie
    grid_energy: float = 0.0  # Netzbezug
    battery_charge_energy: float = 0.0  # Batterie geladen
    battery_discharge_energy: float = 0.0  # Batterie entladen
    self_consumption_energy: float = 0.0  # Eigenverbrauch

    grid_energy_day: float = 0.0  # Netzbezug Tagtarif
    grid_energy_night: float = 0.0  # Netzbezug Nachttarif

    pv_power_max: float = 0.0
    consumption_power_max: float = 0.0
    feed_in_power_max: float = 0.0
    grid_power_max: float = 0.0
    surplus_power_max: float = 0.0

    battery_soc_min: Optional[float] = None
    battery_soc_max: Optional[float] = None

    autarky_avg: float = 0.0

    cost_grid_consumption: float = 0.0  # Kosten für Netzbezug
    cost_saved: float = 0.0  # Eingesparte Kosten durch Eigenverbrauch
    revenue_feed_in: float = 0.0  # Einnahmen durch Einspeisung
    total_benefit: float = 0.0  # Gesamtnutzen (Ersparnis + Einnahmen)

    cost_without_solar: float = 0.0  # Was hätte der Strom ohne PV gekostet

    _sample_count: int = 0
    _autarky_sum: float = 0.0

    first_update: Optional[datetime] = None
    last_update: Optional[datetime] = None

    _config: Optional[Any] = None

    def set_config(self, config: Any) -> None:
        """
        Setzt die Konfiguration für Kostenberechnungen.

        Args:
            config: Konfigurationsobjekt
        """
        self._config = config

    def _is_night_tariff(self, timestamp: datetime) -> bool:
        """
        Prüft ob Nachttarif gilt.

        Args:
            timestamp: Zeitpunkt zur Prüfung

        Returns:
            True wenn Nachttarif gilt
        """
        if not self._config:
            return False

        current_time = timestamp.time()
        night_start = time.fromisoformat(self._config.costs.night_tariff_start)
        night_end = time.fromisoformat(self._config.costs.night_tariff_end)

        if night_start > night_end:
            return current_time >= night_start or current_time < night_end
        else:
            return night_start <= current_time < night_end

    def update(self, data: SolarData, interval_seconds: int) -> None:
        """
        Aktualisiert die Statistiken mit neuen Daten inklusive Kostenberechnung.

        Args:
            data: Aktuelle Solardaten
            interval_seconds: Update-Intervall in Sekunden
        """
        if self.first_update is None:
            self.first_update = data.timestamp
        self.last_update = data.timestamp

        if data.timestamp and data.timestamp.date() != self.date:
            self.reset()
            self.date = data.timestamp.date()
            self.first_update = data.timestamp

        hours = interval_seconds / 3600.0

        self.pv_energy += data.pv_power * hours / 1000
        self.consumption_energy += data.load_power * hours / 1000
        self.feed_in_energy += data.feed_in_power * hours / 1000
        self.self_consumption_energy += data.self_consumption * hours / 1000

        grid_energy_interval = data.grid_consumption * hours / 1000
        if data.timestamp and self._is_night_tariff(data.timestamp):
            self.grid_energy_night += grid_energy_interval
        else:
            self.grid_energy_day += grid_energy_interval
        self.grid_energy += grid_energy_interval

        if data.battery_charging:
            self.battery_charge_energy += data.battery_charge_power * hours / 1000
        else:
            self.battery_discharge_energy += data.battery_discharge_power * hours / 1000

        self.pv_power_max = max(self.pv_power_max, data.pv_power)
        self.consumption_power_max = max(self.consumption_power_max, data.load_power)
        self.feed_in_power_max = max(self.feed_in_power_max, data.feed_in_power)
        self.grid_power_max = max(self.grid_power_max, data.grid_consumption)
        self.surplus_power_max = max(self.surplus_power_max, data.surplus_power)

        if data.battery_soc is not None:
            if self.battery_soc_min is None:
                self.battery_soc_min = data.battery_soc
            else:
                self.battery_soc_min = min(self.battery_soc_min, data.battery_soc)

            if self.battery_soc_max is None:
                self.battery_soc_max = data.battery_soc
            else:
                self.battery_soc_max = max(self.battery_soc_max, data.battery_soc)

        self._sample_count += 1
        self._autarky_sum += data.autarky_rate
        self.autarky_avg = self._autarky_sum / self._sample_count

        self._calculate_costs()

    def _calculate_costs(self) -> None:
        """Berechnet die Kosten und Einsparungen"""
        if not self._config:
            return

        cost_day = self.grid_energy_day * self._config.costs.electricity_price
        cost_night = self.grid_energy_night * self._config.costs.electricity_price_night
        self.cost_grid_consumption = cost_day + cost_night

        self.revenue_feed_in = self.feed_in_energy * self._config.costs.feed_in_tariff

        avg_price = 0.7 * self._config.costs.electricity_price + 0.3 * self._config.costs.electricity_price_night
        self.cost_without_solar = self.consumption_energy * avg_price

        self.cost_saved = self.cost_without_solar - self.cost_grid_consumption

        self.total_benefit = self.cost_saved + self.revenue_feed_in

    def reset(self) -> None:
        """Setzt alle Statistiken zurück"""
        self.date = date.today()

        self.pv_energy = 0.0
        self.consumption_energy = 0.0
        self.feed_in_energy = 0.0
        self.grid_energy = 0.0
        self.grid_energy_day = 0.0
        self.grid_energy_night = 0.0
        self.battery_charge_energy = 0.0
        self.battery_discharge_energy = 0.0
        self.self_consumption_energy = 0.0

        self.pv_power_max = 0.0
        self.consumption_power_max = 0.0
        self.feed_in_power_max = 0.0
        self.grid_power_max = 0.0
        self.surplus_power_max = 0.0

        self.battery_soc_min = None
        self.battery_soc_max = None

        self.autarky_avg = 0.0
        self._sample_count = 0
        self._autarky_sum = 0.0

        self.cost_grid_consumption = 0.0
        self.cost_saved = 0.0
        self.revenue_feed_in = 0.0
        self.total_benefit = 0.0
        self.cost_without_solar = 0.0

        self.first_update = None
        self.last_update = None

    @property
    def runtime_hours(self) -> float:
        """
        Gibt die Laufzeit in Stunden zurück.

        Returns:
            Laufzeit in Stunden
        """
        if self.first_update and self.last_update:
            delta = self.last_update - self.first_update
            return delta.total_seconds() / 3600.0
        return 0.0

    @property
    def self_sufficiency_rate(self) -> float:
        """
        Autarkiegrad basierend auf Energiewerten.

        Returns:
            Autarkiegrad in Prozent
        """
        if self.consumption_energy > 0:
            return (self.self_consumption_energy / self.consumption_energy) * 100
        return 0.0