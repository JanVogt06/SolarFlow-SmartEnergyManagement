"""
Live Display mit Rich Library für Solar Monitor
"""

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.console import Group
from typing import Any, Optional
import logging
import os


class RichLiveDisplay:
    """Live Display mit Rich Library"""

    def __init__(self, config: Any):
        """
        Initialisiert das RichLiveDisplay.

        Args:
            config: Konfigurationsobjekt
        """
        self.config = config
        self.console = Console()
        self.live = None
        self.logger = logging.getLogger(__name__)

        self._initial_display = Panel(
            "[cyan]Solar Monitor wird gestartet...[/cyan]",
            title="[bold blue]SOLAR MONITOR[/bold blue]",
            border_style="bright_blue"
        )

    def initialize(self):
        """Initialisiert das Live Display"""
        if self.live is not None:
            return

        try:
            os.system('clear' if os.name == 'posix' else 'cls')

            self.live = Live(
                self._initial_display,
                console=self.console,
                refresh_per_second=1,
                vertical_overflow="ellipsis"
            )

            self.live.start()
            self.logger.debug("Rich Live Display initialisiert")

        except Exception as e:
            self.logger.error(f"Fehler bei Live-Display Initialisierung: {e}")
            self.live = None
            raise  # Werfe Exception weiter, damit Fallback greift

    def cleanup(self):
        """Räumt das Display auf"""
        if self.live:
            try:
                self.live.stop()
                self.console.clear()
            except Exception as e:
                self.logger.error(f"Fehler beim Cleanup: {e}")
            finally:
                self.live = None

    def display(self, data: Any, device_manager: Optional[Any] = None):
        """
        Zeigt die Daten mit Live-Update an.

        Args:
            data: SolarData-Objekt
            device_manager: Optionaler DeviceManager
        """
        if not self.live:
            return

        try:
            display_panel = self._create_display(data, device_manager)

            self.live.update(display_panel)

        except Exception as e:
            self.logger.error(f"Fehler beim Display-Update: {e}")

    def _create_display(self, data: Any, device_manager: Optional[Any]) -> Panel:
        """Erstellt das komplette Display als einzelnes Panel"""
        timestamp = data.timestamp.strftime('%Y-%m-%d %H:%M:%S') if data.timestamp else "N/A"

        sections = []

        solar_table = self._create_solar_table(data)
        sections.append(Panel(solar_table, title="⚡ Leistungsdaten", border_style="blue"))

        stats_table = self._create_stats_table(data)
        sections.append(Panel(stats_table, title="📊 Kennzahlen", border_style="green"))

        if device_manager and device_manager.devices:
            device_content = self._create_device_content(data, device_manager)
            active_count = len(device_manager.get_active_devices())
            sections.append(Panel(
                device_content,
                title=f"🔌 Gerätesteuerung ({active_count} aktiv)",
                border_style="yellow"
            ))

        content = Group(*sections)

        return Panel(
            content,
            title=f"[bold blue]SOLAR MONITOR[/bold blue] - [dim]{timestamp}[/dim]",
            border_style="bright_blue",
            padding=(1, 2)
        )

    def _create_solar_table(self, data: Any) -> Table:
        """Erstellt die Solar-Daten Tabelle"""
        table = Table(show_header=False, box=None)
        table.add_column("Label", style="cyan", no_wrap=True)
        table.add_column("Value", justify="right", style="white")
        table.add_column("Unit", style="dim")

        pv_color = self._get_value_color(data.pv_power, 'pv_power')
        table.add_row("PV-Erzeugung:", f"[{pv_color}]{data.pv_power:.0f}[/{pv_color}]", "W")

        table.add_row("Hausverbrauch:", f"{data.load_power:.1f}", "W")

        if data.has_battery:
            table.add_row("Gesamtproduktion:", f"{data.total_production:.0f}", "W")

        table.add_row("", "", "")

        if data.is_feeding_in:
            table.add_row("Einspeisung:", f"[green]{data.feed_in_power:.0f}[/green]", "W")
        else:
            table.add_row("Netzbezug:", f"[red]{data.grid_consumption:.0f}[/red]", "W")

        if data.has_battery:
            table.add_row("", "", "")

            if abs(data.battery_power) < self.config.battery.idle_threshold:
                battery_label = "Batterie (Standby):"
                battery_color = "dim"
            elif data.battery_charging:
                battery_label = "Batterie ↓ (Lädt):"
                battery_color = "yellow"
            else:
                battery_label = "Batterie ↑ (Entlädt):"
                battery_color = "green"

            battery_power = abs(data.battery_power)
            table.add_row(battery_label, f"[{battery_color}]{battery_power:.1f}[/{battery_color}]", "W")

            if data.battery_soc is not None:
                soc_color = self._get_value_color(data.battery_soc, 'battery_soc')
                soc_bar = self._create_simple_bar(data.battery_soc, 20)
                table.add_row("Ladestand:", f"{soc_bar}[{soc_color}]{data.battery_soc:.1f}%[/{soc_color}]", "")

        return table

    def _create_stats_table(self, data: Any) -> Table:
        """Erstellt die Statistik-Tabelle"""
        table = Table(show_header=False, box=None)
        table.add_column("Label", style="cyan", no_wrap=True)
        table.add_column("Value", justify="right", style="white")
        table.add_column("Unit", style="dim")

        table.add_row("Eigenverbrauch:", f"{data.self_consumption:.1f}", "W")

        autarky_color = self._get_value_color(data.autarky_rate, 'autarky')
        table.add_row("Autarkiegrad:", f"[{autarky_color}]{data.autarky_rate:.1f}[/{autarky_color}]", "%")

        if data.surplus_power >= self.config.display.surplus_display_threshold:
            surplus_color = self._get_value_color(data.surplus_power, 'surplus')
            table.add_row("Verfügbarer Überschuss:", f"[{surplus_color}]{data.surplus_power:.0f}[/{surplus_color}]", "W")

        return table

    def _create_device_content(self, data: Any, device_manager: Any) -> Group:
        """Erstellt den Geräte-Inhalt"""
        controlled = device_manager.get_total_consumption()

        summary_lines = [
            f"Gesteuerter Verbrauch: [yellow]{controlled:.0f} W[/yellow]",
            f"Aktueller Überschuss: [cyan]{data.surplus_power:.0f} W[/cyan]"
        ]

        if controlled > 0:
            theoretical = data.surplus_power + controlled
            summary_lines.append(f"Theoretischer Überschuss: [dim]{theoretical:.0f} W[/dim]")

        summary_text = "\n".join(summary_lines)

        table = Table(show_header=True, box=None)
        table.add_column("Gerät", style="white")
        table.add_column("Prio", justify="center", style="dim")
        table.add_column("Leistung", justify="right", style="yellow")
        table.add_column("Status", justify="center")
        table.add_column("Laufzeit", justify="right", style="dim")

        for device in device_manager.get_devices_by_priority():
            if device.state.value == "on":
                status = "[bold green]EIN[/bold green]"
            elif device.state.value == "blocked":
                status = "[yellow]BLOCK[/yellow]"
            else:
                status = "[dim red]AUS[/dim red]"

            runtime = device.get_current_runtime(data.timestamp)
            hours = runtime // 60
            mins = runtime % 60
            runtime_str = f"{hours}h {mins:02d}m"

            table.add_row(
                device.name[:20],
                str(device.priority.value),
                f"{device.power_consumption:.0f}W",
                status,
                runtime_str
            )

        return Group(Text.from_markup(summary_text), Text(""), table)

    def _create_simple_bar(self, value: float, width: int = 20) -> str:
        """Erstellt eine einfache Progress-Bar"""
        filled = int(value / 100 * width)
        empty = width - filled
        return f"[{'█' * filled}{'░' * empty}]"

    def _get_value_color(self, value: float, metric: str) -> str:
        """Bestimmt die Farbe basierend auf Schwellwerten"""
        thresholds = self.config.thresholds.__dict__.get(metric, {})

        if not isinstance(thresholds, dict):
            return "white"

        high = thresholds.get('high', float('inf'))
        medium = thresholds.get('medium', 0)

        if metric == 'battery_soc' or metric == 'autarky':
            if value >= high:
                return "green"
            elif value >= medium:
                return "yellow"
            else:
                return "red"
        else:
            if value >= high:
                return "bold green"
            elif value >= medium:
                return "yellow"
            else:
                return "blue"