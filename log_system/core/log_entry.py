"""
Datenmodelle für Log-Einträge.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, List
from enum import Enum


class LogType(Enum):
    """Verfügbare Log-Typen"""
    SOLAR = "solar"
    STATS = "stats"
    DEVICE_EVENT = "device_event"
    DEVICE_STATUS = "device_status"


@dataclass
class LogEntry:
    """Basis-Klasse für alle Log-Einträge"""
    log_type: LogType
    timestamp: datetime = field(default_factory=datetime.now)
    data: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SolarLogEntry(LogEntry):
    """Log-Eintrag für Solar-Daten"""

    def __init__(self, solar_data: Any):
        super().__init__(
            log_type=LogType.SOLAR,
            data=solar_data
        )


@dataclass
class StatsLogEntry(LogEntry):
    """Log-Eintrag für Tagesstatistiken"""

    def __init__(self, daily_stats: Any):
        super().__init__(
            log_type=LogType.STATS,
            data=daily_stats
        )


@dataclass
class DeviceEventEntry(LogEntry):
    """Log-Eintrag für Geräte-Events"""
    device_name: str = ""
    action: str = ""
    old_state: str = ""
    new_state: str = ""
    reason: str = ""
    surplus_power: float = 0.0

    def __init__(self, device: Any, action: str, reason: str,
                 surplus_power: float, old_state: Any):
        super().__init__(
            log_type=LogType.DEVICE_EVENT,
            data={
                'device': device,
                'action': action,
                'reason': reason,
                'surplus_power': surplus_power,
                'old_state': old_state
            }
        )
        self.device_name = device.name
        self.action = action
        self.reason = reason
        self.surplus_power = surplus_power
        self.old_state = old_state.value if hasattr(old_state, 'value') else str(old_state)
        self.new_state = device.state.value if hasattr(device.state, 'value') else str(device.state)


@dataclass
class DeviceStatusEntry(LogEntry):
    """Log-Eintrag für Geräte-Status"""
    devices: List[Any] = field(default_factory=list)
    surplus_power: float = 0.0
    total_consumption: float = 0.0

    def __init__(self, devices: List[Any], surplus_power: float):
        super().__init__(
            log_type=LogType.DEVICE_STATUS,
            data={
                'devices': devices,
                'surplus_power': surplus_power
            }
        )
        self.devices = devices
        self.surplus_power = surplus_power
        self.total_consumption = sum(
            d.power_consumption for d in devices
            if hasattr(d, 'state') and d.state.value == 'on'
        )