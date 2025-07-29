"""
Device Logger - Orchestriert das Logging von Geräte-Daten.
"""

import logging
from typing import Any, List, Dict
from datetime import datetime
from ..core.log_manager import LogManager
from ..core.log_entry import DeviceEventEntry, DeviceStatusEntry


class DeviceLogger:
    """Logger für Geräte-Events und Status"""

    def __init__(self, log_manager: LogManager):
        """
        Initialisiert den DeviceLogger.

        Args:
            log_manager: Zentraler LogManager
        """
        self.log_manager = log_manager
        self.logger = logging.getLogger(__name__)

        # Cache für letzte Zustände
        self.last_device_states: Dict[str, Any] = {}

    def log_event(self, device: Any, action: str, reason: str,
                  surplus_power: float, old_state: Any) -> bool:
        """
        Loggt ein Geräte-Event.

        Args:
            device: Betroffenes Gerät
            action: Durchgeführte Aktion
            reason: Grund für die Aktion
            surplus_power: Aktueller Überschuss
            old_state: Vorheriger Status

        Returns:
            True bei Erfolg
        """
        try:
            # Erstelle Log-Entry
            entry = DeviceEventEntry(device, action, reason, surplus_power, old_state)

            # Aktualisiere Cache
            self.last_device_states[device.name] = device.state

            # Delegiere an LogManager
            return self.log_manager.log(entry)

        except Exception as e:
            self.logger.error(f"Fehler beim Logging von Geräte-Event: {e}")
            return False

    def log_status(self, devices: List[Any], surplus_power: float) -> bool:
        """
        Loggt den aktuellen Status aller Geräte.

        Args:
            devices: Liste von Geräten
            surplus_power: Aktueller Überschuss

        Returns:
            True bei Erfolg
        """
        try:
            # Erstelle Log-Entry
            entry = DeviceStatusEntry(devices, surplus_power)

            # Delegiere an LogManager
            return self.log_manager.log(entry)

        except Exception as e:
            self.logger.error(f"Fehler beim Logging von Geräte-Status: {e}")
            return False

    def log_changes(self, changes: Dict[str, str], surplus_power: float,
                    device_manager: Any) -> None:
        """
        Loggt Änderungen vom EnergyController.

        Args:
            changes: Dict mit Geräteänderungen {Name: Aktion}
            surplus_power: Aktueller Überschuss
            device_manager: DeviceManager für Gerätezugriff
        """
        for device_name, action in changes.items():
            device = device_manager.get_device(device_name)
            if device:
                # Bestimme alten Status
                old_state = self.last_device_states.get(device_name)

                # Falls kein Cache-Eintrag vorhanden, verwende DeviceState.OFF
                if old_state is None:
                    # Importiere DeviceState direkt
                    from device_management import DeviceState
                    old_state = DeviceState.OFF

                # Bestimme Grund basierend auf Aktion
                reason = self._determine_reason(device, action)

                # Event loggen
                self.log_event(device, action, reason, surplus_power, old_state)

    def _determine_reason(self, device: Any, action: str) -> str:
        """
        Bestimmt den Grund für eine Aktion.

        Args:
            device: Gerät
            action: Aktion

        Returns:
            Grund-String
        """
        if "eingeschaltet" in action:
            return f"Überschuss > {device.switch_on_threshold}W"
        elif "ausgeschaltet" in action:
            if "Überschuss" in action:
                return f"Überschuss < {device.switch_off_threshold}W"
            elif "Zeit" in action:
                return "Außerhalb erlaubter Zeit"
            elif "Maximale" in action:
                return "Maximale Tageslaufzeit erreicht"
            else:
                return "Manuell/System"
        else:
            return action

    def create_daily_summary(self, devices: List[Any], output_dir: Any) -> bool:
        """
        Erstellt eine Tageszusammenfassung.

        Args:
            devices: Liste von Geräten
            output_dir: Ausgabeverzeichnis

        Returns:
            True bei Erfolg
        """
        try:
            summary_file = output_dir / f"device_summary_{datetime.now().strftime('%Y%m%d')}.txt"
            current_time = datetime.now()

            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(f"Geräte-Tageszusammenfassung - {current_time.strftime('%d.%m.%Y %H:%M:%S')}\n")
                f.write("=" * 60 + "\n\n")

                total_energy = 0.0

                for device in sorted(devices,
                                     key=lambda d: d.priority.value if hasattr(d.priority, 'value') else d.priority):
                    # Verwende get_current_runtime() um auch laufende Sessions zu berücksichtigen
                    current_runtime = device.get_current_runtime(current_time)
                    energy = current_runtime * device.power_consumption / 60000
                    total_energy += energy

                    f.write(f"{device.name}:\n")
                    f.write(
                        f"  Priorität: {device.priority.value if hasattr(device.priority, 'value') else device.priority}")
                    if hasattr(device.priority, 'label'):
                        f.write(f" ({device.priority.label()})")
                    f.write("\n")
                    f.write(f"  Leistung: {device.power_consumption}W\n")
                    f.write(f"  Laufzeit heute: {current_runtime} Minuten")

                    # Zeige aktuelle Session-Dauer wenn Gerät läuft
                    if device.state.value == 'on' and device.last_state_change:
                        session_minutes = int((current_time - device.last_state_change).total_seconds() / 60)
                        f.write(f" (davon aktuelle Session: {session_minutes} Minuten)")

                    f.write("\n")
                    f.write(f"  Energieverbrauch: {energy:.2f} kWh\n")
                    f.write(f"  Status: {device.state.value if hasattr(device.state, 'value') else device.state}\n")
                    f.write("\n")

                f.write(f"\nGesamt-Energieverbrauch gesteuerte Geräte: {total_energy:.2f} kWh\n")

            self.logger.info(f"Tageszusammenfassung erstellt: {summary_file.name}")
            return True

        except Exception as e:
            self.logger.error(f"Fehler beim Erstellen der Zusammenfassung: {e}")
            return False