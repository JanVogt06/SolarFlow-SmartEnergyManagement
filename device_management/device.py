"""
Geräteverwaltung für den Smart Energy Manager.
"""

from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Optional, List, Tuple
from enum import Enum


class DeviceState(Enum):
    """Gerätezustände"""
    OFF = "off"
    ON = "on"
    BLOCKED = "blocked"  # Blockiert durch Zeitbeschränkung oder Maximallaufzeit


@dataclass
class Device:
    """Repräsentiert ein steuerbares Gerät"""

    # Basis-Eigenschaften
    name: str
    description: str = ""
    power_consumption: float = 0.0  # Watt
    priority: int = 5  # 1-10, wobei 1 höchste Priorität

    # Laufzeit-Beschränkungen
    min_runtime: int = 0  # Minuten - Mindestlaufzeit wenn eingeschaltet
    max_runtime_per_day: int = 0  # Minuten - 0 = unbegrenzt

    # Schwellwerte
    switch_on_threshold: float = 0.0  # Watt - Minimaler Überschuss zum Einschalten
    switch_off_threshold: float = 0.0  # Watt - Überschuss unter dem ausgeschaltet wird

    # Zeitbeschränkungen
    allowed_time_ranges: List[Tuple[time, time]] = field(default_factory=list)

    # Aktueller Status
    state: DeviceState = DeviceState.OFF
    last_state_change: Optional[datetime] = None
    runtime_today: int = 0  # Minuten

    def __post_init__(self):
        """Validierung nach Initialisierung"""
        # Priorität zwischen 1-10
        if not 1 <= self.priority <= 10:
            raise ValueError(f"Priorität muss zwischen 1-10 liegen, ist aber {self.priority}")

        # Schwellwerte validieren
        if self.switch_off_threshold > self.switch_on_threshold:
            raise ValueError("Ausschalt-Schwellwert darf nicht höher als Einschalt-Schwellwert sein")

        # Leistung muss positiv sein
        if self.power_consumption < 0:
            raise ValueError("Leistungsaufnahme muss positiv sein")

    def is_time_allowed(self, current_time: datetime) -> bool:
        """Prüft ob Gerät zur aktuellen Zeit laufen darf"""
        if not self.allowed_time_ranges:
            return True  # Keine Zeitbeschränkung

        current = current_time.time()
        for start, end in self.allowed_time_ranges:
            if start <= current <= end:
                return True
        return False

    def can_run_today(self) -> bool:
        """Prüft ob Gerät heute noch laufen darf (Maximallaufzeit)"""
        if self.max_runtime_per_day == 0:
            return True  # Keine Beschränkung
        return self.runtime_today < self.max_runtime_per_day

    def get_remaining_runtime(self) -> int:
        """Gibt verbleibende Laufzeit heute in Minuten zurück"""
        if self.max_runtime_per_day == 0:
            return 999999  # "Unbegrenzt"
        return max(0, self.max_runtime_per_day - self.runtime_today)