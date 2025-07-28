"""Standard-Theme für Display-System."""

from typing import Dict, Any, List
from ..core import Colors


class DefaultTheme:
    """Standard-Theme mit vollständiger Funktionalität"""

    def __init__(self):
        """Initialisiert das Default Theme."""
        # Layout-Einstellungen
        self.layout = {
            'separator_width': 60,
            'separator_char': '=',
            'sub_separator_char': '-',
            'label_width': 25,
            'value_width': 10,
            'unit_width': 5,
            'table_padding': 2,
            'min_column_width': 8
        }

        # Farb-Schema
        self.colors = {
            'primary': Colors.BLUE,
            'success': Colors.GREEN,
            'warning': Colors.YELLOW,
            'danger': Colors.RED,
            'info': Colors.CYAN,
            'muted': Colors.DIM
        }

        # Schwellwerte für Farbcodierung
        self.thresholds = {
            'battery_soc': {
                'high': 80,
                'medium': 30,
                'colors': {
                    'high': Colors.GREEN,
                    'medium': Colors.YELLOW,
                    'low': Colors.RED
                }
            },
            'autarky': {
                'high': 75,
                'medium': 50,
                'colors': {
                    'high': Colors.GREEN,
                    'medium': Colors.YELLOW,
                    'low': Colors.RED
                }
            },
            'pv_power': {
                'high': 3000,
                'medium': 1000,
                'colors': {
                    'high': Colors.GREEN,
                    'medium': Colors.YELLOW,
                    'low': Colors.BLUE
                }
            },
            'surplus': {
                'high': 2000,
                'medium': 500,
                'colors': {
                    'high': Colors.GREEN,
                    'medium': Colors.YELLOW,
                    'low': Colors.BLUE
                }
            }
        }

        # Zeichen für verschiedene Elemente
        self.symbols = {
            'arrow_up': '↑',
            'arrow_down': '↓',
            'arrow_right': '→',
            'check': '✓',
            'cross': '✗',
            'battery_full': '█',
            'battery_empty': '░',
            'progress_full': '█',
            'progress_empty': '░',
            'progress_partial': ['▏', '▎', '▍', '▌', '▋', '▊', '▉'],
            'box_top_left': '┌',
            'box_top_right': '┐',
            'box_bottom_left': '└',
            'box_bottom_right': '┘',
            'box_horizontal': '─',
            'box_vertical': '│'
        }

        # Format-Templates
        self.formats = {
            'header': "{title:<20} {subtitle}",
            'value_line': "{label:<{label_width}} {value:>{value_width}} {unit}",
            'percentage': "{value:>5.1f}%",
            'power': "{value:>6.0f}W",
            'energy': "{value:>7.2f} kWh",
            'currency': "{value:>8.2f} €",
            'time': "%Y-%m-%d %H:%M:%S",
            'date': "%d.%m.%Y",
            'time_short': "%H:%M:%S"
        }

        # Anzeige-Optionen
        self.display_options = {
            'show_progress_bars': True,
            'show_colors': True,
            'show_icons': True,
            'show_borders': True,
            'show_timestamps': True,
            'show_units': True,
            'compact_mode': False
        }

    def apply_to_config(self, config: Any) -> None:
        """
        Wendet Theme-Einstellungen auf Config an.

        Args:
            config: Konfigurationsobjekt
        """
        # Aktualisiere Schwellwerte
        for key, values in self.thresholds.items():
            if hasattr(config.thresholds, key):
                setattr(config.thresholds, key, {
                    'high': values['high'],
                    'medium': values['medium']
                })

    def get_color_for_value(self, value: float, metric: str) -> str:
        """
        Gibt die passende Farbe für einen Wert zurück.

        Args:
            value: Zu prüfender Wert
            metric: Metrik-Typ

        Returns:
            Farbcode
        """
        if metric not in self.thresholds:
            return ""

        threshold = self.thresholds[metric]
        colors = threshold['colors']

        if value >= threshold['high']:
            return colors['high']
        elif value >= threshold['medium']:
            return colors['medium']
        else:
            return colors['low']

    def format_header(self, title: str, subtitle: str = "") -> str:
        """
        Formatiert einen Header.

        Args:
            title: Haupttitel
            subtitle: Untertitel

        Returns:
            Formatierter Header
        """
        return self.formats['header'].format(title=title, subtitle=subtitle)

    def format_box(self, content: str, width: int = 60) -> List[str]:
        """
        Erstellt eine Box um Inhalt.

        Args:
            content: Inhalt
            width: Breite der Box

        Returns:
            Liste von Zeilen
        """
        lines = []

        # Oberer Rand
        lines.append(
            self.symbols['box_top_left'] +
            self.symbols['box_horizontal'] * (width - 2) +
            self.symbols['box_top_right']
        )

        # Inhalt
        content_lines = content.split('\n')
        for line in content_lines:
            padding = width - len(line) - 4
            lines.append(
                f"{self.symbols['box_vertical']} {line}{' ' * padding} {self.symbols['box_vertical']}"
            )

        # Unterer Rand
        lines.append(
            self.symbols['box_bottom_left'] +
            self.symbols['box_horizontal'] * (width - 2) +
            self.symbols['box_bottom_right']
        )

        return lines