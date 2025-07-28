"""Header-Komponente für Display-System."""

from typing import Optional
from ..core import Layout


class Header:
    """Formatiert und zeigt Header an"""

    def __init__(self, width: int = Layout.SEPARATOR_WIDTH):
        """
        Initialisiert Header.

        Args:
            width: Breite des Headers
        """
        self.width = width

    def display(self, title: str, subtitle: Optional[str] = None,
                separator_char: str = Layout.SEPARATOR_CHAR) -> None:
        """
        Zeigt einen formatierten Header.

        Args:
            title: Haupttitel
            subtitle: Optionaler Untertitel
            separator_char: Zeichen für Trennlinie
        """
        self._print_separator(separator_char)
        if subtitle:
            print(f"{title:<20} {subtitle}")
        else:
            print(title)
        self._print_separator(separator_char)

    def display_simple(self, title: str) -> None:
        """
        Zeigt einen einfachen Header ohne Trennlinien.

        Args:
            title: Anzuzeigender Titel
        """
        print(f"\n{title}:")

    def display_section(self, title: str,
                        separator_char: str = Layout.SUB_SEPARATOR_CHAR) -> None:
        """
        Zeigt einen Abschnitts-Header.

        Args:
            title: Abschnittstitel
            separator_char: Zeichen für Trennlinie
        """
        print(f"\n{title}:")
        self._print_separator(separator_char)

    def _print_separator(self, char: str) -> None:
        """Druckt eine Trennlinie."""
        print(char * self.width)