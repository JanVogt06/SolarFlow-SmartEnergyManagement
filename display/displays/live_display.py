"""
Verbessertes Live Update Display für Solar Monitor
"""

import os
import sys
from typing import Any, Optional
from datetime import datetime

# Windows ANSI Support aktivieren
if sys.platform == "win32":
    os.system("")  # Aktiviert ANSI auf Windows


class LiveDisplay:
    """Display mit Live-Update Funktionalität"""

    def __init__(self, config: Any):
        """
        Initialisiert das LiveDisplay.

        Args:
            config: Konfigurationsobjekt
        """
        self.config = config
        self.is_initialized = False
        self.last_device_count = 0
        self.line_count = 0  # Anzahl der geschriebenen Zeilen

        # ANSI Escape Codes
        self.CLEAR_SCREEN = '\033[2J'
        self.CURSOR_HOME = '\033[H'
        self.CURSOR_UP = '\033[{}A'
        self.CLEAR_LINE = '\033[2K'
        self.HIDE_CURSOR = '\033[?25l'
        self.SHOW_CURSOR = '\033[?25h'

        # Farben (wenn aktiviert)
        self.colors = {
            'green': '\033[92m' if config.display.enable_colors else '',
            'yellow': '\033[93m' if config.display.enable_colors else '',
            'red': '\033[91m' if config.display.enable_colors else '',
            'blue': '\033[94m' if config.display.enable_colors else '',
            'cyan': '\033[96m' if config.display.enable_colors else '',
            'reset': '\033[0m' if config.display.enable_colors else ''
        }

    def initialize(self):
        """Initialisiert das Display"""
        # Cursor verstecken
        print(self.HIDE_CURSOR, end='', flush=True)

        # Bildschirm löschen und Cursor nach oben
        print(self.CLEAR_SCREEN + self.CURSOR_HOME, end='', flush=True)

        self.is_initialized = True

    def cleanup(self):
        """Räumt das Display auf"""
        # Cursor wieder anzeigen
        print(self.SHOW_CURSOR, end='', flush=True)

        # Eine Zeile nach unten für sauberen Abschluss
        print()

    def display(self, data: Any, device_manager: Optional[Any] = None):
        """
        Zeigt die Daten mit Live-Update an.

        Args:
            data: SolarData-Objekt
            device_manager: Optionaler DeviceManager
        """
        if not self.is_initialized:
            self.initialize()

        # Cursor zum Anfang bewegen
        print(self.CURSOR_HOME, end='', flush=True)

        # Buffer für die gesamte Ausgabe
        output_lines = []

        # Header
        output_lines.extend(self._format_header(data))

        # Solar-Daten
        output_lines.extend(self._format_solar_data(data))

        # Geräte wenn vorhanden
        if device_manager and device_manager.devices:
            output_lines.extend(self._format_devices(data, device_manager))

        # Ausgabe mit Zeilenlöschung
        for i, line in enumerate(output_lines):
            # Zeile löschen und neu schreiben
            print(f"{self.CLEAR_LINE}{line}")

        # Übrige alte Zeilen löschen wenn weniger Zeilen als vorher
        if self.line_count > len(output_lines):
            for _ in range(self.line_count - len(output_lines)):
                print(self.CLEAR_LINE)

        # Anzahl Zeilen merken
        self.line_count = len(output_lines)

        # Flush output
        sys.stdout.flush()

    def _format_header(self, data: Any):
        """Formatiert den Header"""
        timestamp = data.timestamp.strftime('%Y-%m-%d %H:%M:%S') if data.timestamp else "N/A"

        return [
            "=" * 60,
            f"SOLAR MONITOR        {timestamp}",
            "=" * 60,
            ""
        ]

    def _format_solar_data(self, data: Any):
        """Formatiert die Solar-Daten"""
        lines = []

        # PV und Verbrauch
        pv_str = self._format_power_colored(data.pv_power, 'pv')
        lines.append(f"PV-Erzeugung:               {pv_str:>20}")
        lines.append(f"Hausverbrauch:        {data.load_power:>15.1f} W")
        lines.append(f"Gesamtproduktion:     {data.total_production:>15.0f} W")
        lines.append("")

        # Netz
        if data.is_feeding_in:
            feed_str = self._colorize(f"{data.feed_in_power:>15.0f} W", 'green')
            lines.append(f"Einspeisung:          {feed_str}")
        else:
            grid_str = self._colorize(f"{data.grid_consumption:>15.0f} W", 'red')
            lines.append(f"Netzbezug:            {grid_str}")

        lines.append("")

        # Batterie
        if data.has_battery:
            lines.extend(self._format_battery(data))

        # Kennzahlen
        lines.append("-" * 60)
        lines.append(f"Eigenverbrauch:       {data.self_consumption:>15.1f} W")

        autarky_str = self._colorize(f"{data.autarky_rate:>15.1f} %",
                                     self._get_autarky_color(data.autarky_rate))
        lines.append(f"Autarkiegrad:         {autarky_str}")

        if data.surplus_power > 0:
            surplus_str = self._colorize(f"{data.surplus_power:>15.0f} W", 'green')
            lines.append(f"Überschuss:           {surplus_str}")

        lines.append("=" * 60)
        lines.append("")

        return lines

    def _format_battery(self, data: Any):
        """Formatiert Batterie-Informationen"""
        lines = []

        # Status
        if abs(data.battery_power) < self.config.battery.idle_threshold:
            status = "Standby"
            power = abs(data.battery_power)
            color = 'blue'
        elif data.battery_charging:
            status = "Ladung"
            power = data.battery_charge_power
            color = 'yellow'
        else:
            status = "Entladung"
            power = data.battery_discharge_power
            color = 'green'

        power_str = self._colorize(f"{power:>15.1f} W", color)
        lines.append(f"Batterie ({status}):   {power_str}")

        # SOC Bar
        if data.battery_soc is not None:
            bar = self._create_progress_bar(data.battery_soc)
            bar_colored = self._colorize(bar, self._get_battery_color(data.battery_soc))
            lines.append(f"Ladestand:   {bar_colored} {data.battery_soc:>5.1f}%")

        lines.append("")
        return lines

    def _format_devices(self, data: Any, device_manager: Any):
        """Formatiert Geräte-Informationen"""
        lines = ["GERÄTESTEUERUNG", "=" * 60, ""]

        # Zusammenfassung
        controlled = device_manager.get_total_consumption()
        lines.append(f"Gesteuerter Verbrauch: {controlled:>14.0f} W")
        lines.append(f"Aktueller Überschuss:  {data.surplus_power:>14.0f} W")

        if controlled > 0:
            theoretical = data.surplus_power + controlled
            lines.append(f"Theoretischer Überschuss: {theoretical:>11.0f} W")

        lines.append("")

        # Geräteliste
        lines.append(f"{'Gerät':<20} {'Prior.':<8} {'Leistung':<10} {'Status':<12} {'Laufzeit':<10}")
        lines.append("-" * 60)

        for device in device_manager.get_devices_by_priority():
            # Status
            if device.state.value == "on":
                status = self._colorize("EIN", 'green')
            elif device.state.value == "blocked":
                status = self._colorize("BLOCKIERT", 'yellow')
            else:
                status = self._colorize("AUS", 'red')

            # Laufzeit
            runtime = device.get_current_runtime(data.timestamp)
            hours = runtime // 60
            mins = runtime % 60
            runtime_str = f"{hours}h {mins}m"

            lines.append(
                f"{device.name:<20} {device.priority.value:>7} "
                f"{device.power_consumption:>9.0f}W {status:<20} {runtime_str:<10}"
            )

        lines.append("=" * 60)
        return lines

    def _format_power_colored(self, value: float, power_type: str) -> str:
        """Formatiert Leistungswerte mit Farbe"""
        formatted = f"{value:.0f} W"

        if power_type == 'pv':
            color = self._get_pv_color(value)
            return self._colorize(formatted, color)

        return formatted

    def _colorize(self, text: str, color: str) -> str:
        """Färbt Text ein"""
        if not self.config.display.enable_colors:
            return text

        color_code = self.colors.get(color, '')
        reset = self.colors['reset']

        # Bei farbigem Text müssen wir die Länge anpassen
        return f"{color_code}{text}{reset}"

    def _get_pv_color(self, power: float) -> str:
        """Bestimmt Farbe für PV-Leistung"""
        if power >= 3000:
            return 'green'
        elif power >= 1000:
            return 'yellow'
        else:
            return 'blue'

    def _get_battery_color(self, soc: float) -> str:
        """Bestimmt Farbe für Batterie-SOC"""
        if soc >= 80:
            return 'green'
        elif soc >= 30:
            return 'yellow'
        else:
            return 'red'

    def _get_autarky_color(self, rate: float) -> str:
        """Bestimmt Farbe für Autarkiegrad"""
        if rate >= 75:
            return 'green'
        elif rate >= 50:
            return 'yellow'
        else:
            return 'red'

    def _create_progress_bar(self, percentage: float, width: int = 20) -> str:
        """Erstellt eine Progress Bar"""
        filled = int(percentage / 100 * width)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}]"