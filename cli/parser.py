"""
ArgumentParser für den Smart Energy Manager.
"""

import argparse
from typing import Dict, Any
from .arguments import ARGUMENT_GROUPS


def create_parser() -> argparse.ArgumentParser:
    """
    Erstellt und konfiguriert den ArgumentParser.

    Returns:
        Konfigurierter ArgumentParser
    """
    parser = argparse.ArgumentParser(
        description="Fronius Solar Monitor - Überwacht Ihre Solaranlage in Echtzeit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=_get_epilog_text()
    )

    # Füge alle Argument-Gruppen hinzu
    _add_arguments_from_config(parser, ARGUMENT_GROUPS)

    return parser


def parse_arguments():
    """
    Parst die Kommandozeilen-Argumente.

    Returns:
        Namespace mit geparsten Argumenten
    """
    parser = create_parser()
    return parser.parse_args()


def _get_epilog_text() -> str:
    """
    Gibt den Epilog-Text für den Parser zurück.

    Returns:
        Epilog-Text mit Beispielen
    """
    return """
Beispiele:
  python main.py                          # Standard-Ausführung mit Gerätesteuerung
  python main.py --ip 192.168.178.100     # Andere IP-Adresse
  python main.py --interval 10            # Update alle 10 Sekunden
  python main.py --no-colors              # Ohne farbige Ausgabe
  python main.py --simple                 # Einzeilige Ausgabe für kleine Displays

Weitere Informationen:
  python main.py --help                   # Diese Hilfe anzeigen
"""


def _add_arguments_from_config(parser: argparse.ArgumentParser,
                               groups: Dict[str, Dict[str, Any]]) -> None:
    """
    Fügt Argumente basierend auf Dictionary-Konfiguration hinzu.

    Args:
        parser: ArgumentParser-Instanz
        groups: Dictionary mit Argument-Gruppen-Definitionen
    """
    for group_name, group_config in groups.items():
        group = parser.add_argument_group(group_config['description'])

        for arg_config in group_config['arguments']:
            # Kopiere Dictionary um Original nicht zu verändern
            arg = arg_config.copy()

            # Entferne custom fields
            arg_name = arg.pop('name')
            arg.pop('config_path', None)
            arg.pop('config_value', None)

            # Füge Argument hinzu
            group.add_argument(arg_name, **arg)