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
from typing import Dict, Any, List

# DEPENDENCY CHECK
REQUIRED_DEPENDENCIES = {
    'requests': 'requests>=2.31.0',
}

# ========== ARGUMENT DEFINITIONS ==========

ARGUMENT_GROUPS = {
    'connection': {
        'description': 'Verbindung',
        'arguments': [
            {
                'name': '--ip',
                'type': str,
                'help': 'IP-Adresse des Fronius Wechselrichters (Standard: aus Config/Umgebung)',
                'config_path': 'connection.fronius_ip'
            },
            {
                'name': '--timeout',
                'type': int,
                'default': 5,
                'help': 'Timeout für API-Anfragen in Sekunden (Standard: 5)',
                'config_path': 'connection.request_timeout'
            }
        ]
    },

    'timing': {
        'description': 'Timing',
        'arguments': [
            {
                'name': '--interval',
                'type': int,
                'help': 'Update-Intervall in Sekunden (Standard: aus Config)',
                'config_path': 'timing.update_interval'
            },
            {
                'name': '--daily-stats-interval',
                'type': int,
                'help': 'Intervall für Tagesstatistik-Anzeige in Sekunden (Standard: 1800 = 30 Min)',
                'config_path': 'timing.daily_stats_interval'
            }
        ]
    },

    'display': {
        'description': 'Anzeige',
        'arguments': [
            {
                'name': '--no-colors',
                'action': 'store_true',
                'help': 'Deaktiviert farbige Ausgabe',
                'config_path': 'display.enable_colors',
                'config_value': lambda args: not args.no_colors
            },
            {
                'name': '--simple',
                'action': 'store_true',
                'help': 'Verwendet vereinfachte Anzeige (eine Zeile)'
            },
            {
                'name': '--no-daily-stats',
                'action': 'store_true',
                'help': 'Deaktiviert die periodische Anzeige der Tagesstatistiken',
                'config_path': 'display.show_daily_stats',
                'config_value': lambda args: not args.no_daily_stats
            }
        ]
    },

    'cost': {
        'description': 'Kostenberechnung',
        'arguments': [
            {
                'name': '--electricity-price',
                'type': float,
                'help': 'Strompreis in EUR/kWh (Standard: 0.40)',
                'config_path': 'costs.electricity_price'
            },
            {
                'name': '--electricity-price-night',
                'type': float,
                'help': 'Nachtstrompreis in EUR/kWh (Standard: 0.30)',
                'config_path': 'costs.electricity_price_night'
            },
            {
                'name': '--feed-in-tariff',
                'type': float,
                'help': 'Einspeisevergütung in EUR/kWh (Standard: 0.082)',
                'config_path': 'costs.feed_in_tariff'
            },
            {
                'name': '--night-tariff-start',
                'type': str,
                'help': 'Beginn Nachttarif (Standard: 22:00)',
                'config_path': 'costs.night_tariff_start'
            },
            {
                'name': '--night-tariff-end',
                'type': str,
                'help': 'Ende Nachttarif (Standard: 06:00)',
                'config_path': 'costs.night_tariff_end'
            }
        ]
    },

    'logging': {
        'description': 'Logging',
        'arguments': [
            {
                'name': '--no-logging',
                'action': 'store_true',
                'help': 'Deaktiviert CSV-Datenlogging',
                'config_path': 'logging.enable_data_logging',
                'config_value': lambda args: not args.no_logging
            },
            {
                'name': '--log-file',
                'type': str,
                'help': 'Pfad zur Log-Datei (Standard: solar_monitor.log)',
                'config_path': 'logging.log_file'
            },
            {
                'name': '--log-level',
                'choices': ['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                'default': 'INFO',
                'help': 'Log-Level für Konsole und Datei (Standard: INFO)',
                'config_path': 'logging.log_level',
                'config_value': lambda args: getattr(logging, args.log_level)
            },
            {
                'name': '--no-daily-stats-logging',
                'action': 'store_true',
                'help': 'Deaktiviert das CSV-Logging der Tagesstatistiken',
                'config_path': 'logging.enable_daily_stats_logging',
                'config_value': lambda args: not args.no_daily_stats_logging
            },
            {
                'name': '--no-database-logging',
                'action': 'store_true',
                'help': 'Deaktiviert das Datenbank-Logging',
                'config_path': 'database.enable_database',
                'config_value': lambda args: not args.no_database_logging
            }
        ]
    },

    'csv': {
        'description': 'CSV-Format',
        'arguments': [
            {
                'name': '--csv-delimiter',
                'type': str,
                'choices': [',', ';', '\t', '|'],
                'help': 'CSV Trennzeichen (Standard: ;)',
                'config_path': 'csv.delimiter'
            },
            {
                'name': '--csv-encoding',
                'type': str,
                'choices': ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1'],
                'help': 'CSV Encoding (Standard: utf-8)',
                'config_path': 'csv.encoding'
            },
            {
                'name': '--csv-decimal',
                'type': str,
                'choices': ['.', ','],
                'help': 'Dezimaltrennzeichen (Standard: ,)',
                'config_path': 'csv.decimal_separator'
            },
            {
                'name': '--csv-english',
                'action': 'store_true',
                'help': 'Verwendet englische CSV-Header statt deutsche',
                'config_path': 'csv.use_german_headers',
                'config_value': lambda args: not args.csv_english
            },
            {
                'name': '--csv-no-info',
                'action': 'store_true',
                'help': 'Keine Info-Zeile unter CSV-Header',
                'config_path': 'csv.include_info_row',
                'config_value': lambda args: not args.csv_no_info
            }
        ]
    },

    'directories': {
        'description': 'Verzeichnisse',
        'arguments': [
            {
                'name': '--data-log-dir',
                'type': str,
                'help': 'Hauptverzeichnis für Log-Dateien (Standard: Datalogs)',
                'config_path': 'directories.data_log_dir'
            },
            {
                'name': '--solar-data-dir',
                'type': str,
                'help': 'Unterverzeichnis für Solardaten (Standard: Solardata)',
                'config_path': 'directories.solar_data_dir'
            },
            {
                'name': '--daily-stats-dir',
                'type': str,
                'help': 'Unterverzeichnis für Tagesstatistiken (Standard: Dailystats)',
                'config_path': 'directories.daily_stats_dir'
            },
            {
                'name': '--device-log-dir',
                'type': str,
                'help': 'Unterverzeichnis für Geräte-Logs (Standard: Devicelogs)',
                'config_path': 'directories.device_log_dir'
            },
            {
                'name': '--database-log-dir',
                'type': str,
                'help': 'Verzeichnis für Datenbank-Logs',
                'config_path': 'database.database_path'
            }
        ]
    },

    'thresholds': {
        'description': 'Schwellwerte',
        'arguments': [
            {
                'name': '--battery-idle',
                'type': float,
                'help': 'Batterie Idle-Schwellwert in Watt (Standard: 10)',
                'config_path': 'battery.idle_threshold'
            },
            {
                'name': '--battery-soc-high',
                'type': float,
                'help': 'Batterie SOC Schwellwert für grün in %% (Standard: 80)',
                'config_path': 'thresholds.battery_soc.high'
            },
            {
                'name': '--battery-soc-medium',
                'type': float,
                'help': 'Batterie SOC Schwellwert für gelb in %% (Standard: 30)',
                'config_path': 'thresholds.battery_soc.medium'
            },
            {
                'name': '--autarky-high',
                'type': float,
                'help': 'Autarkie Schwellwert für grün in %% (Standard: 75)',
                'config_path': 'thresholds.autarky.high'
            },
            {
                'name': '--autarky-medium',
                'type': float,
                'help': 'Autarkie Schwellwert für gelb in %% (Standard: 50)',
                'config_path': 'thresholds.autarky.medium'
            },
            {
                'name': '--surplus-display',
                'type': float,
                'help': 'Überschuss Anzeige-Schwellwert in Watt (Standard: 0)',
                'config_path': 'display.surplus_display_threshold'
            }
        ]
    },

    'device_control': {
        'description': 'Gerätesteuerung',
        'arguments': [
            {
                'name': '--disable-devices',
                'action': 'store_true',
                'help': 'Deaktiviert die intelligente Gerätesteuerung (standardmäßig aktiviert)',
                'config_path': 'devices.enable_control',
                'config_value': lambda args: not args.disable_devices
            },
            {
                'name': '--device-config',
                'type': str,
                'help': 'Pfad zur Gerätekonfigurationsdatei (Standard: devices.json)',
                'config_path': 'devices.config_file'
            },
            {
                'name': '--device-hysteresis',
                'type': int,
                'help': 'Hysterese-Zeit in Minuten für Geräteschaltungen (Standard: 5)',
                'config_path': 'devices.hysteresis_minutes'
            },
            {
                'name': '--no-device-logging',
                'action': 'store_true',
                'help': 'Deaktiviert das Geräte-Logging komplett',
                'config_path': 'logging.enable_device_logging',
                'config_value': lambda args: not args.no_device_logging
            },
            {
                'name': '--device-log-interval',
                'type': int,
                'help': 'Intervall für Geräte-Status-Logging in Sekunden (Standard: 60)',
                'config_path': 'timing.device_log_interval'
            }
        ]
    },

    'system': {
        'description': 'System',
        'arguments': [
            {
                'name': '--skip-check',
                'action': 'store_true',
                'help': 'Überspringe automatische Dependency-Prüfung'
            },
            {
                'name': '--version',
                'action': 'version',
                'version': 'Fronius Solar Monitor 1.0.0'
            }
        ]
    }
}


# ========== HELPER FUNCTIONS ==========

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
import logging


# ========== ARGUMENT PARSING ==========

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


def add_arguments_from_config(parser: argparse.ArgumentParser,
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


def parse_arguments():
    """Kommandozeilen-Argumente parsen"""
    parser = create_base_parser()

    # Füge alle Argumente aus der Konfiguration hinzu
    add_arguments_from_config(parser, ARGUMENT_GROUPS)

    return parser.parse_args()


# ========== CONFIG APPLICATION ==========

def get_nested_attr(obj: Any, path: str) -> Any:
    """
    Holt ein verschachteltes Attribut über einen Punkt-getrennten Pfad.

    Args:
        obj: Objekt
        path: Punkt-getrennter Pfad (z.B. "connection.fronius_ip")

    Returns:
        Attributwert
    """
    attrs = path.split('.')
    for attr in attrs:
        obj = getattr(obj, attr)
    return obj


def set_nested_attr(obj: Any, path: str, value: Any) -> None:
    """
    Setzt ein verschachteltes Attribut über einen Punkt-getrennten Pfad.

    Args:
        obj: Objekt
        path: Punkt-getrennter Pfad (z.B. "connection.fronius_ip")
        value: Zu setzender Wert
    """
    attrs = path.split('.')

    # Navigate to parent
    for attr in attrs[:-1]:
        obj = getattr(obj, attr)

    # Handle dictionary access for last attribute
    if '.' in attrs[-1]:  # For paths like "thresholds.battery_soc.high"
        parts = attrs[-1].split('.')
        parent = getattr(obj, parts[0])
        parent[parts[1]] = value
    else:
        # Set final attribute
        setattr(obj, attrs[-1], value)


def apply_args_to_config(config: Config, args: argparse.Namespace) -> None:
    """
    Wendet alle Kommandozeilen-Argumente auf die Konfiguration an.

    Args:
        config: Config-Instanz
        args: Geparste Argumente
    """
    for group_name, group_config in ARGUMENT_GROUPS.items():
        for arg_config in group_config['arguments']:
            # Skip wenn kein config_path definiert
            if 'config_path' not in arg_config:
                continue

            # Hole Argument-Name (ohne --)
            arg_name = arg_config['name'].lstrip('-').replace('-', '_')

            # Prüfe ob Argument gesetzt wurde
            if hasattr(args, arg_name) and getattr(args, arg_name) is not None:
                # Bestimme den zu setzenden Wert
                if 'config_value' in arg_config:
                    # Custom value function
                    value = arg_config['config_value'](args)
                else:
                    # Direkter Wert
                    value = getattr(args, arg_name)

                # Setze Konfigurationswert
                try:
                    set_nested_attr(config, arg_config['config_path'], value)
                except AttributeError as e:
                    print(f"Warnung: Konnte {arg_config['config_path']} nicht setzen: {e}")


# ========== MAIN FUNCTION ==========

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