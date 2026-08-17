"""
Geräteverwaltung für den Smart Energy Manager
"""

from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Optional, List, Tuple
from enum import Enum, IntEnum
import logging


class DeviceState(Enum):
    """Gerätezustände"""
    OFF = "off"
    ON = "on"
    BLOCKED = "blocked"  # Blockiert durch Zeitbeschränkung oder Maximallaufzeit
    UNREACHABLE = "unreachable"  # Hardware antwortet nicht (z.B. nicht eingesteckt)


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

    name: str
    description: str = ""
    power_consumption: float = 0.0  # Watt
    priority: DevicePriority = DevicePriority.MEDIUM

    min_runtime: int = 0  # Minuten - Mindestlaufzeit wenn eingeschaltet
    max_runtime_per_day: int = 0  # Minuten - 0 = unbegrenzt

    switch_on_threshold: float = 0.0  # Watt - Minimaler Überschuss zum Einschalten
    switch_off_threshold: float = 0.0  # Watt - Überschuss unter dem ausgeschaltet wird

    allowed_time_ranges: List[Tuple[time, time]] = field(default_factory=list)

    state: DeviceState = DeviceState.OFF
    last_state_change: Optional[datetime] = None
    runtime_today: int = 0  # Minuten - Gesamtlaufzeit heute (gespeichert)

    last_switch_off: Optional[datetime] = None  # Letztes Ausschalten für Hysterese

    # Zeitpunkt, bis zu dem die Automatik durch manuelles Schalten pausiert ist
    manual_until: Optional[datetime] = None

    def __post_init__(self):
        """Validierung nach Initialisierung"""
        self.logger = logging.getLogger(f"{__name__}.{self.name}")

        if not isinstance(self.priority, DevicePriority):
            try:
                self.priority = DevicePriority(self.priority)
            except ValueError:
                raise ValueError(f"Ungültige Priorität: {self.priority}")

        if self.switch_off_threshold > self.switch_on_threshold:
            raise ValueError("Ausschalt-Schwellwert darf nicht höher als Einschalt-Schwellwert sein")

        if self.power_consumption < 0:
            raise ValueError("Leistungsaufnahme muss positiv sein")

        self._validate_time_ranges()

    def _validate_time_ranges(self) -> None:
        """
        Validiert die konfigurierten Zeitbereiche.
        Prüft auf ungültige Formate und Überlappungen.
        """
        if not self.allowed_time_ranges:
            return

        for i, (start, end) in enumerate(self.allowed_time_ranges):
            if not isinstance(start, time) or not isinstance(end, time):
                raise ValueError(f"Zeitbereich {i+1}: Start und Ende müssen time-Objekte sein")

        if len(self.allowed_time_ranges) > 1:
            overlaps = self._find_time_range_overlaps()
            if overlaps:
                self.logger.warning(
                    f"Überlappende Zeitbereiche gefunden für Gerät '{self.name}': {overlaps}"
                )

    def _find_time_range_overlaps(self) -> List[Tuple[int, int]]:
        """
        Findet überlappende Zeitbereiche.

        Returns:
            Liste von Tupeln mit den Indizes überlappender Bereiche
        """
        overlaps = []

        intervals = []
        for start, end in self.allowed_time_ranges:
            start_minutes = start.hour * 60 + start.minute
            end_minutes = end.hour * 60 + end.minute

            if start <= end:
                intervals.append([(start_minutes, end_minutes)])
            else:
                intervals.append([
                    (start_minutes, 24 * 60),
                    (0, end_minutes)
                ])

        for i in range(len(intervals)):
            for j in range(i + 1, len(intervals)):
                for interval_i in intervals[i]:
                    for interval_j in intervals[j]:
                        if self._check_interval_overlap(interval_i, interval_j):
                            overlaps.append((i, j))
                            break
                    if (i, j) in overlaps:
                        break

        return overlaps

    @staticmethod
    def _check_interval_overlap(interval1: Tuple[int, int], interval2: Tuple[int, int]) -> bool:
        """
        Prüft ob zwei Zeitintervalle überlappen.

        Diese Methode ist statisch und kann von anderen Klassen verwendet werden.

        Args:
            interval1: Erstes Intervall (start_minuten, end_minuten)
            interval2: Zweites Intervall (start_minuten, end_minuten)

        Returns:
            True wenn Überlappung vorhanden
        """
        start1, end1 = interval1
        start2, end2 = interval2

        return not (end1 <= start2 or end2 <= start1)

    def is_time_allowed(self, current_time: datetime) -> bool:
        """
        Prüft ob Gerät zur aktuellen Zeit laufen darf.
        Unterstützt auch Zeitbereiche über Mitternacht (z.B. 22:00 - 02:00).

        Args:
            current_time: Aktuelle Zeit als datetime

        Returns:
            True wenn Gerät jetzt laufen darf
        """
        if not self.allowed_time_ranges:
            return True

        current = current_time.time()

        for start, end in self.allowed_time_ranges:
            if start <= end:
                if start <= current <= end:
                    return True

            else:
                if current >= start or current <= end:
                    return True

        return False

    def is_manual(self, current_time: datetime) -> bool:
        """
        Prüft ob die Automatik gerade durch manuelles Schalten pausiert ist.

        Args:
            current_time: Aktuelle Zeit

        Returns:
            True wenn das Gerät manuell übersteuert wird
        """
        return self.manual_until is not None and current_time < self.manual_until

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
        """
        Berechnet die aktuelle Gesamtlaufzeit heute in Minuten.

        Args:
            current_time: Aktuelle Zeit

        Returns:
            Gesamtlaufzeit heute in Minuten
        """
        total_runtime = self.runtime_today

        if self.state == DeviceState.ON and self.last_state_change:
            current_session = int((current_time - self.last_state_change).total_seconds() / 60)
            total_runtime += current_session

        return total_runtime

    def format_time_ranges(self) -> str:
        """
        Formatiert die erlaubten Zeitbereiche als String.

        Returns:
            Formatierter String der Zeitbereiche
        """
        if not self.allowed_time_ranges:
            return "Immer"

        ranges = []
        for start, end in self.allowed_time_ranges:
            ranges.append(f"{start.strftime('%H:%M')}-{end.strftime('%H:%M')}")

        return ", ".join(ranges)

    def get_priority_name(self) -> str:
        """Gibt den Namen der Priorität zurück"""
        return self.priority.label()

    def __repr__(self) -> str:
        return (f"Device(name='{self.name}', power={self.power_consumption}W, "
                f"priority={self.priority} ({self.get_priority_name()}), "
                f"state={self.state.value}, runtime_today={self.runtime_today}min, "
                f"time_ranges={self.format_time_ranges()})")