"""
Farb-Management für das Display-System.
"""

from typing import Optional, Dict, Any
from .constants import Colors


class ColorManager:
    """Verwaltet Farben und Themes"""

    def __init__(self, enable_colors: bool = True):
        """
        Initialisiert den ColorManager.

        Args:
            enable_colors: Ob Farben aktiviert sind
        """
        self.enable_colors = enable_colors

        # Threshold-basierte Farbregeln
        self.color_rules = {
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

    def update_thresholds(self, thresholds: Dict[str, Dict[str, float]]) -> None:
        """
        Aktualisiert die Schwellwerte aus der Config.

        Args:
            thresholds: Dictionary mit Schwellwerten
        """
        for key, values in thresholds.items():
            if key in self.color_rules:
                self.color_rules[key]['high'] = values.get('high', self.color_rules[key]['high'])
                self.color_rules[key]['medium'] = values.get('medium', self.color_rules[key]['medium'])

    def get_color(self, color: str) -> str:
        """
        Gibt einen Farbcode zurück.

        Args:
            color: Farbname oder Farbcode

        Returns:
            Farbcode oder leerer String wenn Farben deaktiviert
        """
        if not self.enable_colors:
            return ""

        # Wenn es bereits ein Farbcode ist
        if color.startswith('\033'):
            return color

        # Versuche aus Colors-Klasse zu holen
        return getattr(Colors, color.upper(), "")

    def colorize(self, text: str, color: Optional[str] = None) -> str:
        """
        Färbt Text ein.

        Args:
            text: Zu färbender Text
            color: Farbname oder Farbcode

        Returns:
            Gefärbter Text oder Original
        """
        if not color or not self.enable_colors:
            return text

        color_code = self.get_color(color)
        if not color_code:
            return text

        return f"{color_code}{text}{Colors.RESET}"

    def get_threshold_color(self, value: float, threshold_key: str) -> str:
        """
        Bestimmt die Farbe basierend auf Schwellwerten.

        Args:
            value: Zu prüfender Wert
            threshold_key: Schlüssel für die Schwellwerte

        Returns:
            Farbcode basierend auf Schwellwerten
        """
        if not self.enable_colors or threshold_key not in self.color_rules:
            return ""

        rule = self.color_rules[threshold_key]
        colors = rule['colors']

        if value >= rule['high']:
            return colors['high']
        elif value >= rule['medium']:
            return colors['medium']
        else:
            return colors['low']

    def success(self, text: str) -> str:
        """Formatiert Erfolgs-Text (grün)."""
        return self.colorize(text, Colors.GREEN)

    def warning(self, text: str) -> str:
        """Formatiert Warnungs-Text (gelb)."""
        return self.colorize(text, Colors.YELLOW)

    def error(self, text: str) -> str:
        """Formatiert Fehler-Text (rot)."""
        return self.colorize(text, Colors.RED)

    def info(self, text: str) -> str:
        """Formatiert Info-Text (blau)."""
        return self.colorize(text, Colors.BLUE)

    def bold(self, text: str) -> str:
        """Macht Text fett."""
        if not self.enable_colors:
            return text
        return f"{Colors.BOLD}{text}{Colors.RESET}"