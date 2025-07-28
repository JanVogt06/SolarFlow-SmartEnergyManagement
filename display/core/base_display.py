"""
Basis-Klasse für alle Display-Komponenten.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from .constants import Colors, Layout
from .color_manager import ColorManager
from .formatter import Formatter


class BaseDisplay(ABC):
    """Abstrakte Basis für alle Display-Klassen"""

    def __init__(self, config: Any):
        """
        Initialisiert das Display.

        Args:
            config: Konfigurationsobjekt
        """
        self.config = config
        self.color_manager = ColorManager(config.display.enable_colors)
        self.formatter = Formatter(config)

    def print_separator(self, char: Optional[str] = None,
                        width: Optional[int] = None) -> None:
        """
        Druckt eine Trennlinie.

        Args:
            char: Zeichen für die Trennlinie
            width: Breite der Trennlinie
        """
        char = char or Layout.SEPARATOR_CHAR
        width = width or Layout.SEPARATOR_WIDTH
        print(char * width)

    def print_sub_separator(self) -> None:
        """Druckt eine Unter-Trennlinie."""
        self.print_separator(Layout.SUB_SEPARATOR_CHAR)

    def print_header(self, title: str, subtitle: Optional[str] = None) -> None:
        """
        Druckt einen formatierten Header.

        Args:
            title: Haupttitel
            subtitle: Optionaler Untertitel
        """
        self.print_separator()
        if subtitle:
            print(f"{title:<20} {subtitle}")
        else:
            print(title)
        self.print_separator()

    def print_section(self, title: str) -> None:
        """
        Druckt einen Abschnitts-Header.

        Args:
            title: Abschnittstitel
        """
        print(f"\n{title}:")
        self.print_sub_separator()

    def print_value_line(self, label: str, value: Any, unit: str,
                         color: Optional[str] = None,
                         decimals: Optional[int] = None) -> None:
        """
        Druckt eine formatierte Wert-Zeile.

        Args:
            label: Beschriftung
            value: Anzuzeigender Wert
            unit: Einheit
            color: Optionale Farbe
            decimals: Anzahl Nachkommastellen
        """
        formatted_value = self.formatter.format_value(value, decimals)
        colored_value = self.color_manager.colorize(
            f"{formatted_value} {unit}", color
        )
        print(f"{label:<{Layout.LABEL_WIDTH}} {colored_value}")

    def print_empty_line(self) -> None:
        """Druckt eine Leerzeile."""
        print()

    @abstractmethod
    def display(self, data: Any) -> None:
        """
        Hauptmethode zum Anzeigen der Daten.

        Args:
            data: Anzuzeigende Daten
        """
        pass