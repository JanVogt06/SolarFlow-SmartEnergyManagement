"""Geräte-Display für Smart Energy Manager."""

from typing import Any, List, Tuple
from datetime import datetime
from ..core import BaseDisplay, Colors
from ..components import Header, Table, Separator


class DeviceDisplay(BaseDisplay):
    """Zeigt Geräte-Informationen formatiert an"""

    def __init__(self, config: Any):
        """
        Initialisiert DeviceDisplay.

        Args:
            config: Konfigurationsobjekt
        """
        super().__init__(config)
        self.header = Header()
        self.table = Table(self.color_manager)
        self.separator = Separator()

    def display(self, data: Any, device_manager: Any) -> None:
        """
        Zeigt die Gerätesteuerung an.

        Args:
            data: SolarData-Objekt
            device_manager: DeviceManager-Instanz
        """
        self.separator.section("GERÄTESTEUERUNG")
        self._display_summary(data, device_manager)
        self._display_device_list(data, device_manager)
        self.separator.line()

    def _display_summary(self, data: Any, device_manager: Any) -> None:
        """Zeigt Zusammenfassung der Gerätesteuerung."""
        controlled_consumption = device_manager.get_total_consumption()

        summary_data = {
            "Gesteuerter Verbrauch:": (controlled_consumption, "W"),
            "Aktueller Überschuss:": (data.surplus_power, "W")
        }

        self.table.display_key_value(summary_data)

        # Theoretischer Überschuss
        if controlled_consumption > 0:
            theoretical = data.surplus_power + controlled_consumption
            print(f"{'Theoretischer Überschuss:':<25} {theoretical:>10.0f} W (wenn alle Geräte aus)")

        self.separator.empty_line()

    def _display_device_list(self, data: Any, device_manager: Any) -> None:
        """Zeigt Liste der Geräte."""
        devices = device_manager.get_devices_by_priority()

        if not devices:
            print("Keine Geräte konfiguriert")
            return

        # Tabellen-Header
        headers = ["Gerät", "Priorität", "Leistung", "Status", "Laufzeit heute"]
        rows = []

        for device in devices:
            # Status und Farbe
            status_text, status_color = self._get_device_status(device)

            # Laufzeit
            total_runtime = device.get_current_runtime(data.timestamp)
            runtime_str = self._format_runtime(total_runtime)

            # Zeile erstellen
            row = [
                device.name,
                str(device.priority.value),
                f"{device.power_consumption:.0f}W",
                self.color_manager.colorize(status_text, status_color),
                runtime_str
            ]
            rows.append(row)

            # Zusatz-Info bei Blockierung
            if device.state.value == "blocked":
                self._add_block_reason(device, data, rows)

        # Tabelle anzeigen
        self.table.display(headers, rows, alignments=['l', 'r', 'r', 'l', 'r'])

    def _get_device_status(self, device: Any) -> Tuple[str, str]:
        """
        Gibt Status-Text und Farbe zurück.

        Args:
            device: Gerät

        Returns:
            Tuple aus (Status-Text, Farbcode)
        """
        if device.state.value == "on":
            return "EIN", Colors.GREEN
        elif device.state.value == "blocked":
            return "BLOCKIERT", Colors.YELLOW
        else:
            return "AUS", Colors.RED

    def _format_runtime(self, minutes: int) -> str:
        """Formatiert Laufzeit."""
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours}h {mins}m"

    def _add_block_reason(self, device: Any, data: Any, rows: List[List[str]]) -> None:
        """Fügt Blockierungsgrund zur Tabelle hinzu."""
        reason = ""
        if not device.can_run_today():
            reason = "→ Maximale Tageslaufzeit erreicht"
        elif not device.is_time_allowed(data.timestamp):
            reason = "→ Außerhalb erlaubter Zeiten"

        if reason:
            rows.append(["", "", "", reason, ""])

    def display_compact(self, device_manager: Any, surplus: float) -> None:
        """
        Kompakte Anzeige für Integration in andere Displays.

        Args:
            device_manager: DeviceManager
            surplus: Aktueller Überschuss
        """
        active_devices = device_manager.get_active_devices()
        total_power = device_manager.get_total_consumption()

        if not device_manager.devices:
            return

        # Zeige nur aktive Geräte und Zusammenfassung
        if active_devices:
            device_names = ", ".join(d.name for d in active_devices)
            print(f"Aktive Geräte: {self.color_manager.success(device_names)}")
            print(f"Gesteuerter Verbrauch: {total_power:.0f}W")
        else:
            print("Keine Geräte aktiv")

        # Zeige verfügbaren Überschuss
        remaining = surplus - total_power
        if remaining > 100:
            print(f"Verfügbar für weitere Geräte: {self.color_manager.info(f'{remaining:.0f}W')}")

    def display_timeline(self, devices: List[Any], hours: int = 24) -> None:
        """
        Zeigt Timeline der Gerätelaufzeiten.

        Args:
            devices: Liste von Geräten
            hours: Anzahl Stunden für Timeline
        """
        self.header.display_section("Geräte-Timeline (letzte 24h)")

        # Hier könnte eine ASCII-Timeline implementiert werden
        # Für jetzt nur eine einfache Liste
        for device in devices:
            if device.runtime_today > 0:
                bar_width = min(int(device.runtime_today / 60), 24)
                bar = "█" * bar_width

                color = Colors.GREEN if device.state.value == "on" else Colors.BLUE
                colored_bar = self.color_manager.colorize(bar, color)

                print(f"{device.name:<20} {colored_bar} {self._format_runtime(device.runtime_today)}")