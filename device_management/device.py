"""
Geräteverwaltung für den Smart Energy Manager - KORRIGIERT.
"""

from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Optional, List, Tuple
from enum import Enum, IntEnum


class DeviceState(Enum):
    """Gerätezustände"""
    OFF = "off"
    ON = "on"
    BLOCKED = "blocked"  # Blockiert durch Zeitbeschränkung oder Maximallaufzeit


class DevicePriority(IntEnum):
    """
    Geräteprioritäten - niedrigere Werte = höhere Priorität
    """
    CRITICAL = 1      # Kritische Geräte (z.B. Kühlschrank)
    VERY_HIGH = 2     # Sehr hohe Priorität
    HIGH = 3          # Hohe Priorität (z.B. Waschmaschine)
    MEDIUM_HIGH = 4   # Mittel-Hoch
    MEDIUM = 5        # Mittlere Priorität (Standard)
    MEDIUM_LOW = 6    # Mittel-Niedrig
    LOW = 7           # Niedrige Priorität
    VERY_LOW = 8      # Sehr niedrige Priorität
    MINIMAL = 9       # Minimale Priorität
    OPTIONAL = 10     # Optional (z.B. Pool-Heizung)

    def label(self) -> str:
        labels = {
            DevicePriority.CRITICAL: "Kritisch",
            DevicePriority.VERY_HIGH: "Sehr hoch",
            DevicePriority.HIGH: "Hoch",
            DevicePriority.MEDIUM_HIGH: "Mittel-Hoch",
            DevicePriority.MEDIUM: "Mittel",
            DevicePriority.MEDIUM_LOW: "Mittel-Niedrig",
            DevicePriority.LOW: "Niedrig",
            DevicePriority.VERY_LOW: "Sehr niedrig",
            DevicePriority.MINIMAL: "Minimal",
            DevicePriority.OPTIONAL: "Optional"
        }
        return labels.get(self, f"Priorität {self.value}")


@dataclass
class Device:
    """Repräsentiert ein steuerbares Gerät"""

    # Basis-Eigenschaften
    name: str
    description: str = ""
    power_consumption: float = 0.0  # Watt
    priority: DevicePriority = DevicePriority.MEDIUM

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
    runtime_today: int = 0  # Minuten - Gesamtlaufzeit heute (gespeichert)

    # Hysterese-Tracking für beide Richtungen
    last_switch_off: Optional[datetime] = None  # Letztes Ausschalten für Hysterese

    def __post_init__(self):
        """Validierung nach Initialisierung"""
        if not isinstance(self.priority, DevicePriority):
            try:
                self.priority = DevicePriority(self.priority)
            except ValueError:
                raise ValueError(f"Ungültige Priorität: {self.priority}")

        if self.switch_off_threshold > self.switch_on_threshold:
            raise ValueError("Ausschalt-Schwellwert darf nicht höher als Einschalt-Schwellwert sein")

        if self.power_consumption < 0:
            raise ValueError("Leistungsaufnahme muss positiv sein")

    def is_time_allowed(self, current_time: datetime) -> bool:
        """Prüft ob Gerät zur aktuellen Zeit laufen darf"""
        if not self.allowed_time_ranges:
            return True

        current = current_time.time()
        for start, end in self.allowed_time_ranges:
            if start <= current <= end:
                return True
        return False

    def can_run_today(self) -> bool:
        """Prüft ob Gerät heute noch laufen darf (Maximallaufzeit)"""
        if self.max_runtime_per_day == 0:
            return True
        return self.runtime_today < self.max_runtime_per_day

    def get_remaining_runtime(self) -> int:
        """Gibt verbleibende Laufzeit heute in Minuten zurück"""
        if self.max_runtime_per_day == 0:
            return 999999  # unbegrenzt
        return max(0, self.max_runtime_per_day - self.runtime_today)

    def get_current_runtime(self, current_time: datetime) -> int:
        """Berechnet die aktuelle Gesamtlaufzeit heute in Minuten"""
        total_runtime = self.runtime_today
        if self.state == DeviceState.ON and self.last_state_change:
            current_session = int((current_time - self.last_state_change).total_seconds() / 60)
            total_runtime += current_session
        return total_runtime

    def get_priority_name(self) -> str:
        return self.priority.label()

    def __repr__(self) -> str:
        return (f"Device(name='{self.name}', power={self.power_consumption}W, "
                f"priority={self.priority} ({self.get_priority_name()}), "
                f"state={self.state.value}, runtime_today={self.runtime_today}min)")