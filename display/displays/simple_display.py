"""Einfache, kompakte Display-Variante."""

from typing import Any, Optional
from ..core import BaseDisplay, Colors


class SimpleDisplay(BaseDisplay):
    """Zeigt Daten in kompakter Form an"""

    def __init__(self, config: Any):
        """
        Initialisiert SimpleDisplay.

        Args:
            config: Konfigurationsobjekt
        """
        super().__init__(config)

    def display(self, data: Any, **kwargs: Any) -> None:
        """
        Zeigt eine einzeilige Zusammenfassung.

        Args:
            data: SolarData-Objekt
        """
        timestamp = data.timestamp.strftime('%H:%M:%S') if data.timestamp else "N/A"

        # Basis-Werte
        output = f"\r{timestamp} | "
        output += f"PV: {self._format_power(data.pv_power)} | "
        output += f"Last: {self._format_power(data.load_power)} | "
        output += f"Netz: {self._format_power_signed(data.grid_power)} | "

        # Batterie wenn vorhanden
        if data.has_battery and data.battery_soc is not None:
            output += f"Bat: {data.battery_soc:.0f}% | "

        # Autarkie
        autarky_str = f"{data.autarky_rate:.0f}%"
        if self.config.display.enable_colors:
            autarky_color = self.color_manager.get_threshold_color(data.autarky_rate, 'autarky')
            autarky_str = self.color_manager.colorize(autarky_str, autarky_color)
        output += f"Autarkie: {autarky_str}"

        # Ausgabe ohne Zeilenumbruch für Überschreibung
        print(output, end='', flush=True)

    def display_multiline(self, data: Any) -> None:
        """
        Zeigt kompakte mehrzeilige Ansicht.

        Args:
            data: SolarData-Objekt
        """
        # Clear screen (optional)
        print("\033[2J\033[H")  # ANSI clear screen

        # Header
        timestamp = data.timestamp.strftime('%Y-%m-%d %H:%M:%S') if data.timestamp else "N/A"
        print(f"=== SOLAR MONITOR - {timestamp} ===\n")

        # Hauptwerte in zwei Spalten
        self._print_two_column("PV:", f"{data.pv_power:.0f}W",
                               "Verbrauch:", f"{data.load_power:.0f}W")

        # Netz/Einspeisung
        if data.is_feeding_in:
            self._print_two_column("Einspeisung:", f"{data.feed_in_power:.0f}W",
                                   "Überschuss:", f"{data.surplus_power:.0f}W",
                                   Colors.GREEN)
        else:
            self._print_two_column("Netzbezug:", f"{data.grid_consumption:.0f}W",
                                   "", "", Colors.RED)

        # Batterie
        if data.has_battery:
            battery_status = self._get_battery_status(data)
            soc_str = f"{data.battery_soc:.0f}%" if data.battery_soc else "N/A"
            self._print_two_column("Batterie:", battery_status,
                                   "Ladestand:", soc_str)

        # Kennzahlen
        print("\n" + "-" * 30)
        autarky_color = self.color_manager.get_threshold_color(data.autarky_rate, 'autarky')
        print(f"Autarkie: {self.color_manager.colorize(f'{data.autarky_rate:.1f}%', autarky_color)}")
        print(f"Eigenverbrauch: {data.self_consumption:.0f}W")

    def display_devices_compact(self, data: Any, device_manager: Any) -> None:
        """
        Zeigt kompakte Ansicht mit Geräten.

        Args:
            data: SolarData-Objekt
            device_manager: DeviceManager
        """
        self.display_multiline(data)

        # Geräte-Sektion
        if device_manager and device_manager.devices:
            print("\n" + "-" * 30)
            print("GERÄTE:")

            active = device_manager.get_active_devices()
            if active:
                for device in active:
                    status = self.color_manager.success("EIN")
                    print(f"  {device.name}: {status} ({device.power_consumption}W)")
            else:
                print("  Keine Geräte aktiv")

            total = device_manager.get_total_consumption()
            if total > 0:
                print(f"\nGesamt: {total:.0f}W")

    def _format_power(self, value: float) -> str:
        """Formatiert Leistungswert kompakt."""
        if value >= 1000:
            return f"{value / 1000:.1f}kW"
        else:
            return f"{value:.0f}W"

    def _format_power_signed(self, value: float) -> str:
        """Formatiert Leistungswert mit Vorzeichen."""
        formatted = self._format_power(abs(value))
        if value > 0:
            return f"+{formatted}"
        elif value < 0:
            return f"-{formatted}"
        else:
            return formatted

    def _get_battery_status(self, data: Any) -> str:
        """Gibt kompakten Batterie-Status zurück."""
        if abs(data.battery_power) < self.config.battery.idle_threshold:
            return "Standby"
        elif data.battery_charging:
            return f"↓ {data.battery_charge_power:.0f}W"
        else:
            return f"↑ {data.battery_discharge_power:.0f}W"

    def _print_two_column(self, label1: str, value1: str,
                          label2: str, value2: str,
                          color: Optional[str] = None) -> None:
        """Druckt zwei Werte nebeneinander."""
        col_width = 15

        if color and self.config.display.enable_colors:
            value1 = self.color_manager.colorize(value1, color)
            if value2:
                value2 = self.color_manager.colorize(value2, color)

        line = f"{label1:<{col_width}} {value1:<{col_width}}"
        if label2:
            line += f"    {label2:<{col_width}} {value2}"

        print(line)