#!/usr/bin/env python3
"""
Fronius Solar Monitor - Haupteinstiegspunkt

Verwendung:
    python main.py                    # Standard-Ausführung
    python main.py --ip 192.168.1.100 # Mit anderer IP
    python main.py --interval 10      # Mit anderem Update-Intervall
    python main.py --no-colors        # Ohne Farben
    python main.py --help             # Hilfe anzeigen
"""

import argparse
import sys
from pathlib import Path

# Füge das Projekt-Verzeichnis zum Python-Path hinzu
sys.path.insert(0, str(Path(__file__).parent))

from solar_monitor import SolarMonitor, Config


def parse_arguments():
    """Kommandozeilen-Argumente parsen"""
    parser = argparse.ArgumentParser(
        description="Fronius Solar Monitor - Überwacht Ihre Solaranlage in Echtzeit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python main.py                          # Standard-Ausführung
  python main.py --ip 192.168.178.100     # Andere IP-Adresse
  python main.py --interval 10            # Update alle 10 Sekunden
  python main.py --no-colors              # Ohne farbige Ausgabe
  python main.py --no-logging             # Ohne CSV-Logging
  python main.py --log-level DEBUG        # Debug-Modus
        """
    )

    # Verbindung
    parser.add_argument(
        '--ip',
        type=str,
        help='IP-Adresse des Fronius Wechselrichters (Standard: aus Config/Umgebung)'
    )

    parser.add_argument(
        '--timeout',
        type=int,
        default=5,
        help='Timeout für API-Anfragen in Sekunden (Standard: 5)'
    )

    # Timing
    parser.add_argument(
        '--interval',
        type=int,
        help='Update-Intervall in Sekunden (Standard: aus Config)'
    )

    # Anzeige
    parser.add_argument(
        '--no-colors',
        action='store_true',
        help='Deaktiviert farbige Ausgabe'
    )

    parser.add_argument(
        '--simple',
        action='store_true',
        help='Verwendet vereinfachte Anzeige (eine Zeile)'
    )

    # Logging
    parser.add_argument(
        '--no-logging',
        action='store_true',
        help='Deaktiviert CSV-Datenlogging'
    )

    parser.add_argument(
        '--log-file',
        type=str,
        help='Pfad zur Log-Datei (Standard: solar_monitor.log)'
    )

    parser.add_argument(
        '--data-file',
        type=str,
        help='Pfad zur Daten-CSV (Standard: solar_data.csv)'
    )

    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Log-Level für Konsole und Datei (Standard: INFO)'
    )

    # Sonstiges
    parser.add_argument(
        '--version',
        action='version',
        version='Fronius Solar Monitor 1.0.0'
    )

    return parser.parse_args()


def apply_args_to_config(config: Config, args: argparse.Namespace) -> None:
    """Wendet Kommandozeilen-Argumente auf die Konfiguration an"""

    if args.ip:
        config.FRONIUS_IP = args.ip

    if args.interval:
        config.UPDATE_INTERVAL = args.interval

    if args.timeout:
        config.REQUEST_TIMEOUT = args.timeout

    if args.no_colors:
        config.ENABLE_COLORS = False

    if args.no_logging:
        config.ENABLE_DATA_LOGGING = False

    if args.log_file:
        config.LOG_FILE = args.log_file

    if args.data_file:
        config.DATA_LOG_FILE = args.data_file

    if args.log_level:
        import logging
        config.LOG_LEVEL = getattr(logging, args.log_level)


def main():
    """Hauptfunktion"""
    # Argumente parsen
    args = parse_arguments()

    # Konfiguration erstellen
    config = Config()

    # Kommandozeilen-Argumente anwenden
    apply_args_to_config(config, args)

    try:
        # Monitor erstellen und starten
        monitor = SolarMonitor(config)

        # Einfache Anzeige wenn gewünscht
        if args.simple:
            # TODO: Implementiere simple mode
            print("Simple Mode noch nicht implementiert")
            return

        # Normal starten
        monitor.start()

    except KeyboardInterrupt:
        print("\nProgramm durch Benutzer beendet.")
        sys.exit(0)
    except Exception as e:
        print(f"\nFehler: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()