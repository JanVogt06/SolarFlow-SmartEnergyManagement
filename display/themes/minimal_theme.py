"""Minimales Theme für Display-System."""

from typing import Dict, Any, List


class MinimalTheme:
    """Minimales Theme ohne Farben und Schnickschnack"""

    def __init__(self):
        """Initialisiert das Minimal Theme."""
        # Layout-Einstellungen (kompakter)
        self.layout = {
            'separator_width': 40,
            'separator_char': '-',
            'sub_separator_char': '-',
            'label_width': 20,
            'value_width': 8,
            'unit_width': 4,
            'table_padding': 1,
            'min_column_width': 6
        }

        # Keine Farben
        self.colors = {
            'primary': '',
            'success': '',
            'warning': '',
            'danger': '',
            'info': '',
            'muted': ''
        }

        # Schwellwerte bleiben für Logik
        self.thresholds = {
            'battery_soc': {
                'high': 80,
                'medium': 30,
                'colors': {
                    'high': '',
                    'medium': '',
                    'low': ''
                }
            },
            'autarky': {
                'high': 75,
                'medium': 50,
                'colors': {
                    'high': '',
                    'medium': '',
                    'low': ''
                }
            },
            'pv_power': {
                'high': 3000,
                'medium': 1000,
                'colors': {
                    'high': '',
                    'medium': '',
                    'low': ''
                }
            },
            'surplus': {
                'high': 2000,
                'medium': 500,
                'colors': {
                    'high': '',
                    'medium': '',
                    'low': ''
                }
            }
        }

        # Einfache ASCII-Zeichen
        self.symbols = {
            'arrow_up': '^',
            'arrow_down': 'v',
            'arrow_right': '>',
            'check': '[OK]',
            'cross': '[X]',
            'battery_full': '#',
            'battery_empty': '-',
            'progress_full': '#',
            'progress_empty': '-',
            'progress_partial': ['|'],
            'box_top_left': '+',
            'box_top_right': '+',
            'box_bottom_left': '+',
            'box_bottom_right': '+',
            'box_horizontal': '-',
            'box_vertical': '|'
        }

        # Vereinfachte Format-Templates
        self.formats = {
            'header': "{title} - {subtitle}",
            'value_line': "{label:<{label_width}} {value:>{value_width}} {unit}",
            'percentage': "{value:.0f}%",
            'power': "{value:.0f}W",
            'energy': "{value:.1f} kWh",
            'currency': "{value:.2f} EUR",
            'time': "%Y-%m-%d %H:%M:%S",
            'date': "%d.%m.%Y",
            'time_short': "%H:%M"
        }

        # Anzeige-Optionen
        self.display_options = {
            'show_progress_bars': False,
            'show_colors': False,
            'show_icons': False,
            'show_borders': False,
            'show_timestamps': True,
            'show_units': True,
            'compact_mode': True
        }

    def apply_to_config(self, config: Any) -> None:
        """
        Wendet Theme-Einstellungen auf Config an.

        Args:
            config: Konfigurationsobjekt
        """
        # Deaktiviere Farben
        config.display.enable_colors = False

    def get_color_for_value(self, value: float, metric: str) -> str:
        """
        Gibt keine Farbe zurück (Minimal Theme).

        Args:
            value: Zu prüfender Wert
            metric: Metrik-Typ

        Returns:
            Leerer String
        """
        return ""

    def format_header(self, title: str, subtitle: str = "") -> str:
        """
        Formatiert einen einfachen Header.

        Args:
            title: Haupttitel
            subtitle: Untertitel

        Returns:
            Formatierter Header
        """
        if subtitle:
            return f"{title} - {subtitle}"
        return title

    def format_box(self, content: str, width: int = 40) -> List[str]:
        """
        Erstellt eine einfache Box.

        Args:
            content: Inhalt
            width: Breite der Box

        Returns:
            Liste von Zeilen
        """
        lines = []
        separator = '-' * width

        lines.append(separator)

        content_lines = content.split('\n')
        for line in content_lines:
            # Kürze zu lange Zeilen
            if len(line) > width - 2:
                line = line[:width - 5] + "..."
            lines.append(line)

        lines.append(separator)

        return lines

    def get_status_indicator(self, is_active: bool) -> str:
        """
        Gibt einen einfachen Status-Indikator zurück.

        Args:
            is_active: Ob aktiv

        Returns:
            Status-String
        """
        return "[ON]" if is_active else "[OFF]"

    def format_progress(self, value: float, max_value: float, width: int = 10) -> str:
        """
        Formatiert einen einfachen Progress-Indikator.

        Args:
            value: Aktueller Wert
            max_value: Maximum
            width: Breite

        Returns:
            Progress-String
        """
        percentage = min(max(value / max_value * 100, 0), 100) if max_value > 0 else 0
        filled = int(percentage / 100 * width)

        bar = self.symbols['progress_full'] * filled
        bar += self.symbols['progress_empty'] * (width - filled)

        return f"[{bar}] {percentage:.0f}%"