"""Separator-Komponente für Display-System."""

from typing import Optional
from ..core import Layout


class Separator:
    """Verschiedene Arten von Trennlinien"""

    def __init__(self, width: int = Layout.SEPARATOR_WIDTH):
        """
        Initialisiert Separator.

        Args:
            width: Standard-Breite für Separatoren
        """
        self.width = width

    def line(self, char: Optional[str] = None, width: Optional[int] = None) -> None:
        """
        Druckt eine einfache Trennlinie.

        Args:
            char: Zeichen für die Linie
            width: Breite der Linie
        """
        char = char or Layout.SEPARATOR_CHAR
        width = width or self.width
        print(char * width)

    def section(self, title: str, width: Optional[int] = None) -> None:
        """
        Druckt eine Trennlinie mit zentriertem Titel.

        Args:
            title: Titel in der Mitte
            width: Gesamtbreite
        """
        width = width or self.width
        title = f" {title} "

        padding = width - len(title)
        left_pad = padding // 2
        right_pad = padding - left_pad

        line = Layout.SEPARATOR_CHAR * left_pad + title + Layout.SEPARATOR_CHAR * right_pad
        print(line)

    def subsection(self, width: Optional[int] = None) -> None:
        """
        Druckt eine Unter-Trennlinie.

        Args:
            width: Breite der Linie
        """
        self.line(Layout.SUB_SEPARATOR_CHAR, width)

    def empty_line(self, count: int = 1) -> None:
        """
        Druckt eine oder mehrere Leerzeilen.

        Args:
            count: Anzahl der Leerzeilen
        """
        for _ in range(count):
            print()