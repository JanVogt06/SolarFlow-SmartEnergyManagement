"""
Basis-Formatter für das Logging-System.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from ..core.interfaces import LogFormatter


class BaseFormatter(LogFormatter):
    """Basis-Implementierung für alle Formatter"""

    def __init__(self, config: Any):
        """
        Initialisiert den Formatter.

        Args:
            config: Konfigurationsobjekt
        """
        self.config = config
        self.decimal_separator = config.csv.decimal_separator
        self.use_german_headers = config.csv.use_german_headers

    def format_number(self, value: Optional[float], decimals: int = 0,
                      with_sign: bool = False) -> str:
        """
        Formatiert eine Zahl.

        Args:
            value: Zu formatierender Wert
            decimals: Anzahl Nachkommastellen
            with_sign: Ob Vorzeichen immer angezeigt werden soll

        Returns:
            Formatierter String
        """
        if value is None:
            return "-"

        try:
            if decimals == 0:
                formatted = f"{value:+.0f}" if with_sign else f"{value:.0f}"
            else:
                formatted = f"{value:+.{decimals}f}" if with_sign else f"{value:.{decimals}f}"

            # Dezimaltrennzeichen anpassen
            if self.decimal_separator == ",":
                formatted = formatted.replace(".", ",")

            return formatted
        except (ValueError, TypeError):
            return "-"

    def format_timestamp(self, timestamp: datetime,
                        format_string: str = '%Y-%m-%d %H:%M:%S') -> str:
        """
        Formatiert einen Zeitstempel.

        Args:
            timestamp: Zu formatierender Zeitstempel
            format_string: Format-String für strftime

        Returns:
            Formatierter Zeitstempel
        """
        if timestamp is None:
            return "-"
        return timestamp.strftime(format_string)

    def format_boolean(self, value: bool) -> str:
        """
        Formatiert einen Boolean-Wert.

        Args:
            value: Boolean-Wert

        Returns:
            "1" für True, "0" für False
        """
        return "1" if value else "0"

    def get_session_info(self, title: str, **kwargs: Any) -> List[str]:
        """
        Erstellt Session-Info-Zeilen.

        Args:
            title: Titel der Session-Info
            **kwargs: Zusätzliche Info-Felder

        Returns:
            Liste mit Info-Zeilen
        """
        info_lines: List[str] = [
            f"# {title}",
            f"# Erstellt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"# CSV-Format: Delimiter='{self.config.csv.delimiter}', "
            f"Decimal='{self.decimal_separator}', "
            f"Encoding='{self.config.csv.encoding}'"
        ]

        # Zusätzliche Infos
        for key, value in kwargs.items():
            info_lines.append(f"# {key}: {value}")

        return info_lines