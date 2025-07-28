"""
Formatierungs-Utilities für das Display-System.
"""

from typing import Optional, Any, Union
from datetime import datetime
from .constants import Templates


class Formatter:
    """Formatiert Werte für die Anzeige"""

    def __init__(self, config: Any):
        """
        Initialisiert den Formatter.

        Args:
            config: Konfigurationsobjekt
        """
        self.config = config
        self.decimal_separator = config.csv.decimal_separator
        self.currency_symbol = config.costs.currency_symbol

    def format_value(self, value: Optional[Union[int, float]],
                     decimals: Optional[int] = None) -> str:
        """
        Formatiert einen numerischen Wert.

        Args:
            value: Zu formatierender Wert
            decimals: Anzahl Nachkommastellen (auto wenn None)

        Returns:
            Formatierter String
        """
        if value is None:
            return "-"

        # Auto-Dezimalstellen basierend auf Größe
        if decimals is None:
            if isinstance(value, int) or value >= 1000:
                decimals = 0
            elif value >= 10:
                decimals = 1
            else:
                decimals = 2

        try:
            if decimals == 0:
                formatted = f"{value:.0f}"
            else:
                formatted = f"{value:.{decimals}f}"

            # Tausender-Trennzeichen
            if abs(value) >= 1000:
                parts = formatted.split('.')
                parts[0] = self._add_thousands_separator(parts[0])
                formatted = '.'.join(parts)

            # Dezimaltrennzeichen anpassen
            if self.decimal_separator == ',':
                formatted = formatted.replace('.', ',')

            return formatted
        except (ValueError, TypeError):
            return "-"

    def format_power(self, value: Optional[float]) -> str:
        """
        Formatiert einen Leistungswert.

        Args:
            value: Leistung in Watt

        Returns:
            Formatierter String mit Einheit
        """
        if value is None:
            return "- W"
        return f"{self.format_value(value, 0)} W"

    def format_energy(self, value: Optional[float]) -> str:
        """
        Formatiert einen Energiewert.

        Args:
            value: Energie in kWh

        Returns:
            Formatierter String mit Einheit
        """
        if value is None:
            return "- kWh"
        return f"{self.format_value(value, 2)} kWh"

    def format_percentage(self, value: Optional[float]) -> str:
        """
        Formatiert einen Prozentwert.

        Args:
            value: Prozentwert

        Returns:
            Formatierter String mit %
        """
        if value is None:
            return "- %"
        return f"{self.format_value(value, 1)}%"

    def format_currency(self, value: Optional[float]) -> str:
        """
        Formatiert einen Währungswert.

        Args:
            value: Betrag

        Returns:
            Formatierter String mit Währungssymbol
        """
        if value is None:
            return f"- {self.currency_symbol}"
        return f"{self.format_value(value, 2)} {self.currency_symbol}"

    def format_time(self, hours: float) -> str:
        """
        Formatiert Stunden in lesbares Format.

        Args:
            hours: Anzahl Stunden

        Returns:
            Formatierter String (z.B. "2h 30m")
        """
        if hours < 0:
            return "-"

        full_hours = int(hours)
        minutes = int((hours - full_hours) * 60)

        if full_hours == 0:
            return f"{minutes}m"
        elif minutes == 0:
            return f"{full_hours}h"
        else:
            return f"{full_hours}h {minutes}m"

    def format_timestamp(self, timestamp: Optional[datetime],
                         format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """
        Formatiert einen Zeitstempel.

        Args:
            timestamp: Zeitstempel
            format_str: Format-String

        Returns:
            Formatierter Zeitstempel
        """
        if timestamp is None:
            return "-"
        return timestamp.strftime(format_str)

    def format_date(self, date: Any) -> str:
        """
        Formatiert ein Datum.

        Args:
            date: Datum

        Returns:
            Formatiertes Datum
        """
        if hasattr(date, 'strftime'):
            return date.strftime('%d.%m.%Y')
        return str(date)

    def _add_thousands_separator(self, number_str: str) -> str:
        """
        Fügt Tausender-Trennzeichen hinzu.

        Args:
            number_str: Zahlen-String

        Returns:
            String mit Tausender-Trennzeichen
        """
        # Behandle negatives Vorzeichen
        if number_str.startswith('-'):
            return '-' + self._add_thousands_separator(number_str[1:])

        # Füge Punkte als Tausender-Trennzeichen hinzu
        result = ""
        for i, digit in enumerate(reversed(number_str)):
            if i > 0 and i % 3 == 0:
                result = "." + result
            result = digit + result

        return result