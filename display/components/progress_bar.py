"""Progress Bar Komponente für Display-System."""

from typing import Optional
from ..core import ColorManager


class ProgressBar:
    """Zeigt Progress Bars für verschiedene Werte"""

    def __init__(self, width: int = 20, color_manager: Optional[ColorManager] = None):
        """
        Initialisiert ProgressBar.

        Args:
            width: Breite der Progress Bar
            color_manager: Optional ColorManager für farbige Ausgabe
        """
        self.width = width
        self.color_manager = color_manager

        self.filled_char = "█"
        self.empty_char = "░"
        self.partial_chars = ["▏", "▎", "▍", "▌", "▋", "▊", "▉"]

    def display(self, value: float, max_value: float = 100,
                label: Optional[str] = None,
                show_percentage: bool = True,
                color: Optional[str] = None) -> None:
        """
        Zeigt eine Progress Bar.

        Args:
            value: Aktueller Wert
            max_value: Maximaler Wert (Standard: 100)
            label: Optionale Beschriftung
            show_percentage: Ob Prozentangabe angezeigt werden soll
            color: Optionale Farbe
        """
        percentage = min(max(value / max_value * 100, 0), 100)

        filled_width = percentage / 100 * self.width
        filled_blocks = int(filled_width)
        partial_block = filled_width - filled_blocks

        bar = self.filled_char * filled_blocks

        if partial_block > 0 and filled_blocks < self.width:
            partial_index = int(partial_block * len(self.partial_chars))
            bar += self.partial_chars[min(partial_index, len(self.partial_chars) - 1)]
            filled_blocks += 1

        bar += self.empty_char * (self.width - filled_blocks)

        if self.color_manager and color:
            bar = self.color_manager.colorize(bar, color)

        if label:
            output = f"{label}: [{bar}]"
        else:
            output = f"[{bar}]"

        if show_percentage:
            output += f" {percentage:>5.1f}%"

        print(output)

    def display_battery(self, soc: float, label: str = "Batterie") -> None:
        """
        Zeigt eine Batterie-Progress-Bar mit automatischer Farbcodierung.

        Args:
            soc: State of Charge in Prozent
            label: Beschriftung
        """
        if self.color_manager:
            color = self.color_manager.get_threshold_color(soc, 'battery_soc')
        else:
            color = None

        self.display(soc, 100, label, True, color)

    def display_power(self, current: float, max_power: float,
                      label: str = "Leistung") -> None:
        """
        Zeigt eine Leistungs-Progress-Bar.

        Args:
            current: Aktuelle Leistung
            max_power: Maximale Leistung
            label: Beschriftung
        """
        if self.color_manager:
            color = self.color_manager.get_threshold_color(current, 'pv_power')
        else:
            color = None

        self.display(current, max_power, f"{label} ({current:.0f}W)", False, color)

