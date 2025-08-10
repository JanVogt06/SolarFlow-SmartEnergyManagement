"""
Live Display mit Rich Library für Solar Monitor
"""

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.align import Align
from rich.console import Group
from typing import Any, Optional
from datetime import datetime
import logging
import sys


class RichLiveDisplay:
    """Live Display mit Rich Library"""

    def __init__(self, config: Any):
        """
        Initialisiert das RichLiveDisplay.

        Args:
            config: Konfigurationsobjekt
        """
        self.config = config
        # Console explizit auf stdout setzen
        self.console = Console(file=sys.stdout, force_terminal=True)
        self.live = None
        self.logger = logging.getLogger(__name__)
        self._display_active = False

    def initialize(self):
        """Initialisiert das Live Display"""
        if not self.live:
            self.live = Live(
                console=self.console,
                refresh_per_second=1,
                transient=False,
                screen=True  # Vollbild-Modus
            )
            self.live.start()
            self._display_active = True
            self.logger.debug("Rich Live Display initialisiert")

    def cleanup(self):
        """Räumt das Display auf"""
        if self.live and self._display_active:
            self.live.stop()
            self.live = None
            self._display_active = False
            # Clear screen nach Beenden
            self.console.clear()
            self.logger.debug("Rich Live Display aufgeräumt")

    def display(self, data: Any, device_manager: Optional[Any] = None):
        """
        Zeigt die Daten mit Live-Update an.

        Args:
            data: SolarData-Objekt
            device_manager: Optionaler DeviceManager
        """
        if not self.live or not self._display_active:
            self.logger.warning("Live Display nicht initialisiert!")
            return

        try:
            # Erstelle das komplette Display
            display = self._create_display(data, device_manager)

            # Update anzeigen
            self.live.update(display)
        except Exception as e:
            self.logger.error(f"Fehler beim Display-Update: {e}")

    def _create_display(self, data: Any, device_manager: Optional[Any]) -> Panel:
        """Erstellt das komplette Display"""
        # Hauptkomponenten
        header = self._create_header(data)
        solar_section = self._create_solar_section(data)
        stats_section = self._create_stats_section(data)

        # Kombiniere Hauptbereich
        main_content = Group(
            solar_section,
            Text(""),  # Leerzeile
            stats_section
        )

        # Füge Geräte hinzu wenn vorhanden
        if device_manager and device_manager.devices:
            device_section = self._create_devices_section(data, device_manager)
            content = Group(main_content, Text(""), device_section)
        else:
            content = main_content

        # Erstelle Haupt-Panel
        return Panel(
            content,
            title=header,
            border_style="bright_blue",
            padding=(1, 2)
        )

    def _create_header(self, data: Any) -> str:
        """Erstellt den Header"""
        timestamp = data.timestamp.strftime('%Y-%m-%d %H:%M:%S') if data.timestamp else "N/A"
        return f"[bold blue]SOLAR MONITOR[/bold blue] - [dim]{timestamp}[/dim]"

    def _create_solar_section(self, data: Any) -> Panel:
        """Erstellt die Solar-Daten Sektion"""
        table = Table(show_header=False, box=None, padding=0)
        table.add_column("Label", style="cyan", no_wrap=True, width=25)
        table.add_column("Value", justify="right", style="white", width=12)
        table.add_column("Unit", style="dim", width=5)

        # PV-Erzeugung
        pv_style = self._get_pv_style(data.pv_power)
        table.add_row(
            "PV-Erzeugung:",
            f"[{pv_style}]{data.pv_power:.0f}[/{pv_style}]",
            "W"
        )

        # Hausverbrauch
        table.add_row("Hausverbrauch:", f"{data.load_power:.1f}", "W")

        # Gesamtproduktion
        if data.has_battery:
            table.add_row("Gesamtproduktion:", f"{data.total_production:.0f}", "W")

        table.add_section()  # Trennlinie

        # Netz
        if data.is_feeding_in:
            table.add_row(
                "Einspeisung:",
                f"[green]{data.feed_in_power:.0f}[/green]",
                "W"
            )
        else:
            table.add_row(
                "Netzbezug:",
                f"[red]{data.grid_consumption:.0f}[/red]",
                "W"
            )

        # Batterie
        if data.has_battery:
            table.add_section()

            # Batterie Status
            battery_text, battery_style = self._get_battery_status(data)
            battery_power = abs(data.battery_power)
            table.add_row(
                battery_text,
                f"[{battery_style}]{battery_power:.1f}[/{battery_style}]",
                "W"
            )

            # SOC mit grafischer Anzeige
            if data.battery_soc is not None:
                soc_bar = self._create_battery_bar(data.battery_soc)
                table.add_row("Ladestand:", soc_bar, f"{data.battery_soc:.1f}%")

        return Panel(table, title="⚡ Leistungsdaten", border_style="blue")

    def _create_stats_section(self, data: Any) -> Panel:
        """Erstellt die Statistik-Sektion"""
        table = Table(show_header=False, box=None, padding=0)
        table.add_column("Label", style="cyan", no_wrap=True, width=25)
        table.add_column("Value", justify="right", style="white", width=12)
        table.add_column("Unit", style="dim", width=5)

        # Eigenverbrauch
        table.add_row("Eigenverbrauch:", f"{data.self_consumption:.1f}", "W")

        # Autarkie
        autarky_style = self._get_autarky_style(data.autarky_rate)
        table.add_row(
            "Autarkiegrad:",
            f"[{autarky_style}]{data.autarky_rate:.1f}[/{autarky_style}]",
            "%"
        )

        # Überschuss
        if data.surplus_power >= self.config.display.surplus_display_threshold:
            surplus_style = self._get_surplus_style(data.surplus_power)
            table.add_row(
                "Verfügbarer Überschuss:",
                f"[{surplus_style}]{data.surplus_power:.0f}[/{surplus_style}]",
                "W"
            )

        return Panel(table, title="📊 Kennzahlen", border_style="green")

    def _create_devices_section(self, data: Any, device_manager: Any) -> Panel:
        """Erstellt die Geräte-Sektion"""
        # Zusammenfassung
        controlled = device_manager.get_total_consumption()
        active_count = len(device_manager.get_active_devices())

        # Info-Text
        info_lines = []
        info_lines.append(f"Gesteuerter Verbrauch: [yellow]{controlled:.0f} W[/yellow]")
        info_lines.append(f"Aktueller Überschuss: [cyan]{data.surplus_power:.0f} W[/cyan]")

        if controlled > 0:
            theoretical = data.surplus_power + controlled
            info_lines.append(f"Theoretischer Überschuss: [dim]{theoretical:.0f} W[/dim]")

        info_text = "\n".join(info_lines)

        # Geräte-Tabelle
        table = Table(box=None, padding=0, show_header=True)
        table.add_column("Gerät", style="white", no_wrap=True)
        table.add_column("Prio", justify="center", style="dim", width=4)
        table.add_column("Leistung", justify="right", style="yellow")
        table.add_column("Status", justify="center", width=10)
        table.add_column("Laufzeit", justify="right", style="dim")

        for device in device_manager.get_devices_by_priority():
            # Status
            if device.state.value == "on":
                status = "[bold green]EIN[/bold green]"
            elif device.state.value == "blocked":
                status = "[yellow]BLOCK[/yellow]"
            else:
                status = "[dim red]AUS[/dim red]"

            # Laufzeit
            runtime = device.get_current_runtime(data.timestamp)
            hours = runtime // 60
            mins = runtime % 60
            runtime_str = f"{hours}h {mins:02d}m"

            # Priorität mit Farbe
            prio_color = self._get_priority_color(device.priority.value)

            table.add_row(
                device.name[:20],  # Begrenzen auf 20 Zeichen
                f"[{prio_color}]{device.priority.value}[/{prio_color}]",
                f"{device.power_consumption:.0f}W",
                status,
                runtime_str
            )

        # Kombiniere Info und Tabelle
        content = Group(
            Text(info_text),
            Text(""),  # Leerzeile
            table
        )

        title = f"🔌 Gerätesteuerung ({active_count} aktiv)"
        return Panel(content, title=title, border_style="yellow")

    def _create_battery_bar(self, soc: float) -> str:
        """Erstellt eine grafische Batterie-Anzeige"""
        # 20 Zeichen breite Bar
        filled = int(soc / 100 * 20)
        empty = 20 - filled

        # Farbe basierend auf SOC
        color = self._get_battery_color(soc)

        # Erstelle Bar mit Farbcodierung
        bar = f"[{color}]{'█' * filled}[/{color}][dim]{'░' * empty}[/dim]"

        return f"[{bar}]"

    def _get_pv_style(self, power: float) -> str:
        """Bestimmt Style für PV-Leistung"""
        if power >= self.config.thresholds.pv_power['high']:
            return "bold green"
        elif power >= self.config.thresholds.pv_power['medium']:
            return "yellow"
        else:
            return "blue"

    def _get_battery_status(self, data: Any) -> tuple[str, str]:
        """Bestimmt Batterie-Status und Style"""
        if abs(data.battery_power) < self.config.battery.idle_threshold:
            return "Batterie (Standby):", "dim blue"
        elif data.battery_charging:
            return "Batterie ↓ (Lädt):", "yellow"
        else:
            return "Batterie ↑ (Entlädt):", "green"

    def _get_battery_color(self, soc: float) -> str:
        """Bestimmt Farbe für Batterie-SOC"""
        if soc >= self.config.thresholds.battery_soc['high']:
            return "green"
        elif soc >= self.config.thresholds.battery_soc['medium']:
            return "yellow"
        else:
            return "red"

    def _get_autarky_style(self, rate: float) -> str:
        """Bestimmt Style für Autarkiegrad"""
        if rate >= self.config.thresholds.autarky['high']:
            return "bold green"
        elif rate >= self.config.thresholds.autarky['medium']:
            return "yellow"
        else:
            return "red"

    def _get_surplus_style(self, surplus: float) -> str:
        """Bestimmt Style für Überschuss"""
        if surplus >= self.config.thresholds.surplus['high']:
            return "bold green"
        elif surplus >= self.config.thresholds.surplus['medium']:
            return "yellow"
        else:
            return "blue"

    def _get_priority_color(self, priority: int) -> str:
        """Bestimmt Farbe für Priorität"""
        if priority <= 2:
            return "red"
        elif priority <= 4:
            return "yellow"
        elif priority <= 7:
            return "green"
        else:
            return "blue"