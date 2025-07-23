#!/usr/bin/env python3
"""
Fronius Solar Monitor - Haupteinstiegspunkt
"""

import argparse
import sys
import time
import subprocess
import importlib.util
from pathlib import Path

# DEPENDENCY CHECK
REQUIRED_DEPENDENCIES = {
    'requests': 'requests>=2.31.0',
}


def check_single_dependency(module_name, pip_package):
    """
    Prüft ob ein einzelnes Modul installiert ist.

    Args:
        module_name: Name des Python-Moduls zum Importieren
        pip_package: Package-Name mit Version für pip install

    Returns:
        bool: True wenn installiert, False sonst
    """
    return importlib.util.find_spec(module_name) is not None


def install_dependency(pip_package):
    """
    Installiert ein einzelnes Package.

    Args:
        pip_package: Package-Name mit Version für pip install

    Returns:
        bool: True bei erfolgreicher Installation, False sonst
    """
    try:
        print(f"Installiere {pip_package}...")
        subprocess.check_call(
            [sys.executable, '-m', 'pip', 'install', pip_package],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT
        )
        return True
    except subprocess.CalledProcessError:
        return False


def check_dependencies(skip_check=False):
    """Prüft und installiert fehlende Dependencies"""
    if skip_check:
        return True

    # Sammle fehlende Dependencies
    missing_deps = []
    for module_name, pip_package in REQUIRED_DEPENDENCIES.items():
        if not check_single_dependency(module_name, pip_package):
            missing_deps.append((module_name, pip_package))

    # Wenn alle Dependencies installiert sind
    if not missing_deps:
        return True

    # Zeige fehlende Dependencies
    print("Fehlende Pakete gefunden:")
    for module_name, pip_package in missing_deps:
        print(f"  - {module_name} ({pip_package})")

    # Frage nach automatischer Installation
    try:
        response = input("\nSollen die fehlenden Pakete automatisch installiert werden? (j/n): ")
        if response.lower() in ['j', 'ja', 'y', 'yes', '']:
            print("\nInstalliere fehlende Pakete...")

            # Installiere alle fehlenden Dependencies
            failed_installs = []
            for module_name, pip_package in missing_deps:
                if not install_dependency(pip_package):
                    failed_installs.append(pip_package)

            if failed_installs:
                print("\nFehler bei der Installation folgender Pakete:")
                for package in failed_installs:
                    print(f"  - {package}")
                print("\nBitte installieren Sie diese manuell mit:")
                print(f"  pip install {' '.join(failed_installs)}")
                return False

            # Alle Installationen erfolgreich
            print("\nAlle Pakete erfolgreich installiert!")

            # Cache invalidieren für neue Imports
            import importlib
            importlib.invalidate_caches()

            return True
        else:
            print("\nInstallation übersprungen.")
            print("Bitte installieren Sie die fehlenden Pakete manuell mit:")
            print(f"  pip install {' '.join(pip_pkg for _, pip_pkg in missing_deps)}")
            return False

    except KeyboardInterrupt:
        print("\nInstallation abgebrochen.")
        return False


# Prüfe Dependencies bevor weitere Imports
if not check_dependencies('--skip-check' in sys.argv):
    sys.exit(1)

# Füge das Projekt-Verzeichnis zum Python-Path hinzu
sys.path.insert(0, str(Path(__file__).parent))

from solar_monitor import SolarMonitor, Config

def create_base_parser():
    """Erstellt den Basis-ArgumentParser"""
    return argparse.ArgumentParser(
        description="Fronius Solar Monitor - Überwacht Ihre Solaranlage in Echtzeit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=get_epilog_text()
    )


def get_epilog_text():
    """Gibt den Epilog-Text für den Parser zurück"""
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


def add_connection_arguments(parser):
    """Fügt Verbindungs-bezogene Argumente hinzu"""
    group = parser.add_argument_group('Verbindung')

    group.add_argument(
        '--ip',
        type=str,
        help='IP-Adresse des Fronius Wechselrichters (Standard: aus Config/Umgebung)'
    )

    group.add_argument(
        '--timeout',
        type=int,
        default=5,
        help='Timeout für API-Anfragen in Sekunden (Standard: 5)'
    )


def add_timing_arguments(parser):
    """Fügt Timing-bezogene Argumente hinzu"""
    group = parser.add_argument_group('Timing')

    group.add_argument(
        '--interval',
        type=int,
        help='Update-Intervall in Sekunden (Standard: aus Config)'
    )

    group.add_argument(
        '--daily-stats-interval',
        type=int,
        help='Intervall für Tagesstatistik-Anzeige in Sekunden (Standard: 1800 = 30 Min)'
    )


def add_display_arguments(parser):
    """Fügt Anzeige-bezogene Argumente hinzu"""
    group = parser.add_argument_group('Anzeige')

    group.add_argument(
        '--no-colors',
        action='store_true',
        help='Deaktiviert farbige Ausgabe'
    )

    group.add_argument(
        '--simple',
        action='store_true',
        help='Verwendet vereinfachte Anzeige (eine Zeile)'
    )

    group.add_argument(
        '--no-daily-stats',
        action='store_true',
        help='Deaktiviert die periodische Anzeige der Tagesstatistiken'
    )

def add_cost_arguments(parser):
    """Fügt Kosten-bezogene Argumente hinzu"""
    group = parser.add_argument_group('Kostenberechnung')

    group.add_argument(
        '--electricity-price',
        type=float,
        help='Strompreis in EUR/kWh (Standard: 0.40)'
    )

    group.add_argument(
        '--electricity-price-night',
        type=float,
        help='Nachtstrompreis in EUR/kWh (Standard: 0.30)'
    )

    group.add_argument(
        '--feed-in-tariff',
        type=float,
        help='Einspeisevergütung in EUR/kWh (Standard: 0.082)'
    )

    group.add_argument(
        '--night-tariff-start',
        type=str,
        help='Beginn Nachttarif (Standard: 22:00)'
    )

    group.add_argument(
        '--night-tariff-end',
        type=str,
        help='Ende Nachttarif (Standard: 06:00)'
    )


def add_logging_arguments(parser):
    """Fügt Logging-bezogene Argumente hinzu"""
    group = parser.add_argument_group('Logging')

    group.add_argument(
        '--no-logging',
        action='store_true',
        help='Deaktiviert CSV-Datenlogging'
    )

    group.add_argument(
        '--log-file',
        type=str,
        help='Pfad zur Log-Datei (Standard: solar_monitor.log)'
    )

    group.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Log-Level für Konsole und Datei (Standard: INFO)'
    )

    group.add_argument(
        '--no-daily-stats-logging',
        action='store_true',
        help='Deaktiviert das CSV-Logging der Tagesstatistiken'
    )

    group.add_argument(
        '--no-database-logging',
        help='Deaktiviert das Datenbank-Logging'
    )


def add_csv_arguments(parser):
    """Fügt CSV-Format Argumente hinzu"""
    group = parser.add_argument_group('CSV-Format')

    group.add_argument(
        '--csv-delimiter',
        type=str,
        choices=[',', ';', '\t', '|'],
        help='CSV Trennzeichen (Standard: ;)'
    )

    group.add_argument(
        '--csv-encoding',
        type=str,
        choices=['utf-8', 'latin-1', 'cp1252', 'iso-8859-1'],
        help='CSV Encoding (Standard: utf-8)'
    )

    group.add_argument(
        '--csv-decimal',
        type=str,
        choices=['.', ','],
        help='Dezimaltrennzeichen (Standard: ,)'
    )

    group.add_argument(
        '--csv-english',
        action='store_true',
        help='Verwendet englische CSV-Header statt deutsche'
    )

    group.add_argument(
        '--csv-no-info',
        action='store_true',
        help='Keine Info-Zeile unter CSV-Header'
    )


def add_directory_arguments(parser):
    """Fügt Verzeichnis-bezogene Argumente hinzu"""
    group = parser.add_argument_group('Verzeichnisse')

    group.add_argument(
        '--data-log-dir',
        type=str,
        help='Hauptverzeichnis für Log-Dateien (Standard: Datalogs)'
    )

    group.add_argument(
        '--solar-data-dir',
        type=str,
        help='Unterverzeichnis für Solardaten (Standard: Solardata)'
    )

    group.add_argument(
        '--daily-stats-dir',
        type=str,
        help='Unterverzeichnis für Tagesstatistiken (Standard: Dailystats)'
    )

    group.add_argument(
        '--device-log-dir',
        type=str,
        help='Unterverzeichnis für Geräte-Logs (Standard: Devicelogs)'
    )

    group.add_argument(
        '--database-log-dir',
        type=str,
        help='Verzeichnis für Datenbank-Logs'
    )


def add_threshold_arguments(parser):
    """Fügt Schwellwert-Argumente hinzu"""
    group = parser.add_argument_group('Schwellwerte')

    group.add_argument(
        '--battery-idle',
        type=float,
        help='Batterie Idle-Schwellwert in Watt (Standard: 10)'
    )

    group.add_argument(
        '--battery-soc-high',
        type=float,
        help='Batterie SOC Schwellwert für grün in %% (Standard: 80)'
    )

    group.add_argument(
        '--battery-soc-medium',
        type=float,
        help='Batterie SOC Schwellwert für gelb in %% (Standard: 30)'
    )

    group.add_argument(
        '--autarky-high',
        type=float,
        help='Autarkie Schwellwert für grün in %% (Standard: 75)'
    )

    group.add_argument(
        '--autarky-medium',
        type=float,
        help='Autarkie Schwellwert für gelb in %% (Standard: 50)'
    )

    group.add_argument(
        '--surplus-display',
        type=float,
        help='Überschuss Anzeige-Schwellwert in Watt (Standard: 0)'
    )


def add_device_control_arguments(parser):
    """Fügt Gerätesteuerungs-Argumente hinzu"""
    group = parser.add_argument_group('Gerätesteuerung')

    group.add_argument(
        '--disable-devices',
        action='store_true',
        help='Deaktiviert die intelligente Gerätesteuerung (standardmäßig aktiviert)'
    )

    group.add_argument(
        '--device-config',
        type=str,
        help='Pfad zur Gerätekonfigurationsdatei (Standard: devices.json)'
    )

    group.add_argument(
        '--device-hysteresis',
        type=int,
        help='Hysterese-Zeit in Minuten für Geräteschaltungen (Standard: 5)'
    )

    group.add_argument(
        '--no-device-logging',
        action='store_true',
        help='Deaktiviert das Geräte-Logging komplett'
    )

    group.add_argument(
        '--device-log-interval',
        type=int,
        help='Intervall für Geräte-Status-Logging in Sekunden (Standard: 60)'
    )


def add_system_arguments(parser):
    """Fügt System-Argumente hinzu"""
    group = parser.add_argument_group('System')

    group.add_argument(
        '--skip-check',
        action='store_true',
        help='Überspringe automatische Dependency-Prüfung'
    )

    group.add_argument(
        '--version',
        action='version',
        version='Fronius Solar Monitor 1.0.0'
    )


def parse_arguments():
    """Kommandozeilen-Argumente parsen"""
    parser = create_base_parser()

    # Füge alle Argument-Gruppen hinzu
    add_connection_arguments(parser)
    add_timing_arguments(parser)
    add_display_arguments(parser)
    add_cost_arguments(parser)
    add_logging_arguments(parser)
    add_csv_arguments(parser)
    add_directory_arguments(parser)
    add_threshold_arguments(parser)
    add_device_control_arguments(parser)
    add_system_arguments(parser)

    return parser.parse_args()

def apply_connection_config(config: Config, args: argparse.Namespace) -> None:
    """Wendet Verbindungs-Konfiguration an"""
    if args.ip:
        config.connection.fronius_ip = args.ip

    if args.timeout:
        config.connection.request_timeout = args.timeout


def apply_timing_config(config: Config, args: argparse.Namespace) -> None:
    """Wendet Timing-Konfiguration an"""
    if args.interval:
        config.timing.update_interval = args.interval

    if args.daily_stats_interval is not None:
        config.timing.daily_stats_interval = args.daily_stats_interval


def apply_display_config(config: Config, args: argparse.Namespace) -> None:
    """Wendet Anzeige-Konfiguration an"""
    if args.no_colors:
        config.display.enable_colors = False

    if args.no_daily_stats:
        config.display.show_daily_stats = False

def apply_cost_config(config: Config, args: argparse.Namespace) -> None:
    """Wendet Kosten-Konfiguration an"""
    if args.electricity_price is not None:
        config.costs.electricity_price = args.electricity_price

    if args.electricity_price_night is not None:
        config.costs.electricity_price_night = args.electricity_price_night

    if args.feed_in_tariff is not None:
        config.costs.feed_in_tariff = args.feed_in_tariff

    if args.night_tariff_start:
        config.costs.night_tariff_start = args.night_tariff_start

    if args.night_tariff_end:
        config.costs.night_tariff_end = args.night_tariff_end

def apply_logging_config(config: Config, args: argparse.Namespace) -> None:
    """Wendet Logging-Konfiguration an"""
    if args.no_logging:
        config.logging.enable_data_logging = False

    if args.log_file:
        config.logging.log_file = args.log_file

    if args.log_level:
        import logging
        config.logging.log_level = getattr(logging, args.log_level)

    if args.no_daily_stats_logging:
        config.logging.enable_daily_stats_logging = False

    if args.no_database_logging:
        config.database.enable_database = False


def apply_csv_config(config: Config, args: argparse.Namespace) -> None:
    """Wendet CSV-Format Konfiguration an"""
    if args.csv_delimiter:
        config.csv.delimiter = args.csv_delimiter

    if args.csv_encoding:
        config.csv.encoding = args.csv_encoding

    if args.csv_decimal:
        config.csv.decimal_separator = args.csv_decimal

    if args.csv_english:
        config.csv.use_german_headers = False

    if args.csv_no_info:
        config.csv.include_info_row = False


def apply_directory_config(config: Config, args: argparse.Namespace) -> None:
    """Wendet Verzeichnis-Konfiguration an"""
    if args.data_log_dir:
        config.directories.data_log_dir = args.data_log_dir

    if args.solar_data_dir:
        config.directories.solar_data_dir = args.solar_data_dir

    if args.daily_stats_dir:
        config.directories.daily_stats_dir = args.daily_stats_dir

    if args.device_log_dir:
        config.directories.device_log_dir = args.device_log_dir

    if args.database_log_dir:
        config.database.database_path = args.database_log_dir


def apply_threshold_config(config: Config, args: argparse.Namespace) -> None:
    """Wendet Schwellwert-Konfiguration an"""
    if args.battery_idle is not None:
        config.battery.idle_threshold = args.battery_idle

    if args.battery_soc_high is not None:
        config.THRESHOLDS['battery_soc']['high'] = args.battery_soc_high

    if args.battery_soc_medium is not None:
        config.THRESHOLDS['battery_soc']['medium'] = args.battery_soc_medium

    if args.autarky_high is not None:
        config.THRESHOLDS['autarky']['high'] = args.autarky_high

    if args.autarky_medium is not None:
        config.THRESHOLDS['autarky']['medium'] = args.autarky_medium

    if args.surplus_display is not None:
        config.display.surplus_display_threshold = args.surplus_display


def apply_device_config(config: Config, args: argparse.Namespace) -> None:
    """Wendet Gerätesteuerungs-Konfiguration an"""
    if args.disable_devices:
        config.devices.enable_control = False

    if args.device_config:
        config.devices.config_file = args.device_config

    if args.device_hysteresis is not None:
        config.devices.hysteresis_minutes = args.device_hysteresis

    if args.no_device_logging:
        config.logging.enable_device_logging = False

    if args.device_log_interval is not None:
        config.timing.device_log_interval = args.device_log_interval


def apply_args_to_config(config: Config, args: argparse.Namespace) -> None:
    """Wendet alle Kommandozeilen-Argumente auf die Konfiguration an"""
    apply_connection_config(config, args)
    apply_timing_config(config, args)
    apply_display_config(config, args)
    apply_cost_config(config, args)
    apply_logging_config(config, args)
    apply_csv_config(config, args)
    apply_directory_config(config, args)
    apply_threshold_config(config, args)
    apply_device_config(config, args)

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

        # Einfache Anzeige, wenn gewünscht
        if args.simple:
            print("Simple Mode aktiviert - Einzeilige Ausgabe")
            try:
                while True:
                    data = monitor.get_current_data()
                    if data:
                        monitor.display.display_simple(data)
                    time.sleep(config.timing.update_interval)
            except KeyboardInterrupt:
                print("\nSimple Mode beendet.")
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