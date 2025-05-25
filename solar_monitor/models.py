"""
Datenmodelle für den Fronius Solar Monitor.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class SolarData:
    """Datenklasse für Solardaten"""

    pv_power: float = 0.0  # Watt - Photovoltaik Erzeugung
    grid_power: float = 0.0  # Watt - Netz (negativ = Einspeisung, positiv = Bezug)
    battery_power: float = 0.0  # Watt - Batterie (negativ = Laden, positiv = Entladen)
    load_power: float = 0.0  # Watt - Hausverbrauch
    battery_soc: Optional[float] = None  # Prozent - Batterieladestand
    timestamp: datetime = None

    def __post_init__(self):
        """Initialisierung nach der Erstellung"""
        if self.timestamp is None:
            self.timestamp = datetime.now()

    # === Netz-Properties ===
    @property
    def is_feeding_in(self) -> bool:
        """Prüft ob ins Netz eingespeist wird"""
        return self.grid_power < 0

    @property
    def feed_in_power(self) -> float:
        """Gibt die Einspeiseleistung zurück (positiv)"""
        return abs(self.grid_power) if self.is_feeding_in else 0

    @property
    def grid_consumption(self) -> float:
        """Gibt den Netzbezug zurück (positiv)"""
        return self.grid_power if self.grid_power > 0 else 0

    # === Batterie-Properties ===
    @property
    def battery_charging(self) -> bool:
        """Prüft ob die Batterie lädt"""
        return self.battery_power < 0

    @property
    def battery_charge_power(self) -> float:
        """Gibt die Ladeleistung zurück (positiv)"""
        return abs(self.battery_power) if self.battery_charging else 0

    @property
    def battery_discharge_power(self) -> float:
        """Gibt die Entladeleistung zurück (positiv)"""
        return self.battery_power if self.battery_power > 0 else 0

    @property
    def has_battery(self) -> bool:
        """Prüft ob eine Batterie vorhanden ist"""
        return self.battery_soc is not None

    # === Berechnete Werte ===
    @property
    def self_consumption(self) -> float:
        """Berechnet den Eigenverbrauch (Hausverbrauch - Netzbezug)"""
        return self.load_power - self.grid_consumption

    @property
    def autarky_rate(self) -> float:
        """Berechnet den Autarkiegrad in Prozent"""
        if self.load_power > 0:
            return (self.self_consumption / self.load_power) * 100
        return 0.0

    @property
    def self_sufficiency_rate(self) -> float:
        """Alias für autarky_rate"""
        return self.autarky_rate

    @property
    def total_production(self) -> float:
        """Gesamte Energieproduktion (PV + Batterieentladung)"""
        return self.pv_power + self.battery_discharge_power

    @property
    def surplus_power(self) -> float:
        """Überschussleistung (kann für Gerätesteuerung verwendet werden)"""
        return self.feed_in_power

    def to_dict(self) -> dict:
        """Konvertiert die Daten in ein Dictionary"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'pv_power': self.pv_power,
            'grid_power': self.grid_power,
            'battery_power': self.battery_power,
            'load_power': self.load_power,
            'battery_soc': self.battery_soc,
            'feed_in_power': self.feed_in_power,
            'grid_consumption': self.grid_consumption,
            'self_consumption': self.self_consumption,
            'autarky_rate': self.autarky_rate,
            'surplus_power': self.surplus_power
        }