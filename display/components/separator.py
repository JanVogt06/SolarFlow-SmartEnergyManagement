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

    def double_line(self, width: Optional[int] = None) -> None:
        """
        Druckt eine doppelte Trennlinie.

        Args:
            width: Breite der Linie
        """
        self.line("═", width)

    def dashed_line(self, width: Optional[int] = None) -> None:
        """
        Druckt eine gestrichelte Linie.

        Args:
            width: Breite der Linie
        """
        self.line("-", width)

    def section(self, title: str, width: Optional[int] = None) -> None:
        """
        Druckt eine Trennlinie mit zentriertem Titel.

        Args:
            title: Titel in der Mitte
            width: Gesamtbreite
        """
        width = width or self.width
        title = f" {title} "

        # Berechne Padding
        padding = width - len(title)
        left_pad = padding // 2
        right_pad = padding - left_pad

        # Erstelle Linie
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

    def box_top(self, width: Optional[int] = None) -> None:
        """Druckt oberen Rand einer Box."""
        width = width or self.width
        print("┌" + "─" * (width - 2) + "┐")

    def box_bottom(self, width: Optional[int] = None) -> None:
        """Druckt unteren Rand einer Box."""
        width = width or self.width
        print("└" + "─" * (width - 2) + "┘")

    def box_line(self, content: str, width: Optional[int] = None) -> None:
        """
        Druckt eine Zeile innerhalb einer Box.

        Args:
            content: Inhalt der Zeile
            width: Gesamtbreite der Box
        """
        width = width or self.width
        # Begrenze Inhalt auf verfügbare Breite
        max_content_width = width - 4  # 2 für "│ " und " │"
        if len(content) > max_content_width:
            content = content[:max_content_width - 3] + "..."

        padding = width - len(content) - 4
        print(f"│ {content}{' ' * padding} │")