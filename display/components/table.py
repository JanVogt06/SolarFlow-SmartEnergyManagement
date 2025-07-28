"""Tabellen-Komponente für Display-System."""

from typing import List, Dict, Any, Optional, Tuple
from ..core import Layout, ColorManager


class Table:
    """Formatiert und zeigt Tabellen an"""

    def __init__(self, color_manager: Optional[ColorManager] = None):
        """
        Initialisiert Table.

        Args:
            color_manager: Optional ColorManager für farbige Ausgabe
        """
        self.color_manager = color_manager

    def display(self, headers: List[str], rows: List[List[Any]],
                column_widths: Optional[List[int]] = None,
                alignments: Optional[List[str]] = None) -> None:
        """
        Zeigt eine formatierte Tabelle.

        Args:
            headers: Spaltenüberschriften
            rows: Datenzeilen
            column_widths: Optionale Spaltenbreiten
            alignments: Optionale Ausrichtungen ('l', 'r', 'c')
        """
        if not headers or not rows:
            return

        # Bestimme Spaltenbreiten wenn nicht angegeben
        if column_widths is None:
            column_widths = self._calculate_column_widths(headers, rows)

        # Standard-Ausrichtungen
        if alignments is None:
            alignments = ['l'] * len(headers)

        # Header ausgeben
        self._print_header_row(headers, column_widths, alignments)
        self._print_separator_row(column_widths)

        # Datenzeilen ausgeben
        for row in rows:
            self._print_data_row(row, column_widths, alignments)

    def display_key_value(self, data: Dict[str, Tuple[Any, str]],
                          label_width: int = Layout.LABEL_WIDTH,
                          value_width: int = Layout.VALUE_WIDTH) -> None:
        """
        Zeigt Key-Value-Paare als Tabelle.

        Args:
            data: Dictionary mit {label: (value, unit)}
            label_width: Breite der Label-Spalte
            value_width: Breite der Wert-Spalte
        """
        for label, (value, unit) in data.items():
            formatted_value = self._format_value(value, value_width)
            print(f"{label:<{label_width}} {formatted_value} {unit}")

    def display_colored_row(self, label: str, value: Any, unit: str,
                            color: Optional[str] = None,
                            label_width: int = Layout.LABEL_WIDTH,
                            value_width: int = Layout.VALUE_WIDTH) -> None:
        """
        Zeigt eine einzelne Zeile mit optionaler Farbe.

        Args:
            label: Beschriftung
            value: Anzuzeigender Wert
            unit: Einheit
            color: Optionale Farbe
            label_width: Breite der Label-Spalte
            value_width: Breite der Wert-Spalte
        """
        formatted_value = self._format_value(value, value_width)

        if self.color_manager and color:
            colored_value = self.color_manager.colorize(f"{formatted_value} {unit}", color)
        else:
            colored_value = f"{formatted_value} {unit}"

        print(f"{label:<{label_width}} {colored_value}")

    def _calculate_column_widths(self, headers: List[str],
                                 rows: List[List[Any]]) -> List[int]:
        """Berechnet optimale Spaltenbreiten."""
        widths = [len(str(h)) for h in headers]

        for row in rows:
            for i, cell in enumerate(row[:len(widths)]):
                widths[i] = max(widths[i], len(str(cell)))

        # Mindestbreite und Padding
        return [max(w + Layout.TABLE_PADDING, Layout.MIN_COLUMN_WIDTH)
                for w in widths]

    def _print_header_row(self, headers: List[str], widths: List[int],
                          alignments: List[str]) -> None:
        """Druckt Header-Zeile."""
        parts = []
        for header, width, align in zip(headers, widths, alignments):
            if align == 'r':
                parts.append(f"{header:>{width}}")
            elif align == 'c':
                parts.append(f"{header:^{width}}")
            else:
                parts.append(f"{header:<{width}}")
        print(" ".join(parts))

    def _print_separator_row(self, widths: List[int]) -> None:
        """Druckt Trennzeile unter Header."""
        parts = ["-" * width for width in widths]
        print(" ".join(parts))

    def _print_data_row(self, row: List[Any], widths: List[int],
                        alignments: List[str]) -> None:
        """Druckt eine Datenzeile."""
        parts = []
        for i, (cell, width, align) in enumerate(zip(row, widths, alignments)):
            cell_str = str(cell)

            # Zahlen rechtsbündig wenn nicht anders angegeben
            if align == 'r' or (align == 'l' and isinstance(cell, (int, float))):
                parts.append(f"{cell_str:>{width}}")
            elif align == 'c':
                parts.append(f"{cell_str:^{width}}")
            else:
                parts.append(f"{cell_str:<{width}}")
        print(" ".join(parts))

    def _format_value(self, value: Any, width: int) -> str:
        """Formatiert einen Wert für die Anzeige."""
        if isinstance(value, float):
            if value >= 1000 or value <= -1000:
                return f"{value:>{width}.0f}"
            else:
                return f"{value:>{width}.1f}"
        else:
            return f"{value:>{width}}"