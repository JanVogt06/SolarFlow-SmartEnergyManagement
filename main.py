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
    # Hier können später weitere Dependencies hinzugefügt werden:
    # 'pandas': 'pandas>=1.5.0',
    # 'numpy': 'numpy>=1.24.0',
    # 'matplotlib': 'matplotlib>=3.5.0',
    # 'influxdb': 'influxdb>=5.3.0',
    # 'paho-mqtt': 'paho-mqtt>=1.6.0',
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


def parse_arguments():
    """Kommandozeilen-Argumente parsen"""
    parser = argparse.ArgumentParser(
        description="Fronius Solar Monitor - Überwacht Ihre Solaranlage in Echtzeit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Beispiele:
          python main.py                          # Standard-Ausführung mit Gerätesteuerung
          python main.py --ip 192.168.178.100     # Andere IP-Adresse
          python main.py --interval 10            # Update alle 10 Sekunden
          python main.py --timeout 10             # Längerer Timeout für langsame Verbindungen
          python main.py --no-colors              # Ohne farbige Ausgabe
          python main.py --simple                 # Einzeilige Ausgabe für kleine Displays

        Gerätesteuerung:
          python main.py                          # Gerätesteuerung ist standardmäßig aktiv
          python main.py --disable-devices        # Deaktiviert intelligente Gerätesteuerung
          python main.py --device-config my_devices.json  # Eigene Gerätedatei
          python main.py --device-hysteresis 10   # 10 Min Hysterese

        Geräte-Logging:
          python main.py --no-device-logging      # Gerätesteuerung ohne Logging
          python main.py --device-log-dir MyDeviceLogs    # Eigenes Geräte-Log-Verzeichnis
          python main.py --device-log-interval 300         # Status-Log alle 5 Minuten
          python main.py --no-device-events       # Ohne Event-Logging
          python main.py --no-device-status       # Ohne periodisches Status-Logging
          python main.py --no-device-summary      # Ohne tägliche Zusammenfassung

        Logging und Verzeichnisse:
          python main.py --no-logging             # Ohne CSV-Logging
          python main.py --no-daily-stats-logging # Ohne Tagesstatistik-CSV
          python main.py --data-log-dir MyLogs    # Eigenes Hauptverzeichnis
          python main.py --solar-data-dir Solar   # Eigenes Solardaten-Verzeichnis
          python main.py --daily-stats-dir Stats  # Eigenes Statistik-Verzeichnis
          python main.py --device-log-dir Devices # Eigenes Geräte-Log-Verzeichnis
          python main.py --no-daily-stats         # Ohne periodische Tagesstatistiken
          python main.py --daily-stats-interval 3600  # Tagesstatistiken jede Stunde
          python main.py --log-file my.log        # Eigene Log-Datei
          python main.py --data-file data.csv     # Eigene Daten-CSV
          python main.py --log-level DEBUG        # Debug-Modus
          python main.py --log-level WARNING      # Nur Warnungen und Fehler
          python main.py --skip-check             # Dependency-Check überspringen
          python main.py --version                # Version anzeigen

        CSV-Format Optionen:
          python main.py --csv-delimiter ";"      # CSV Trennzeichen (Standard: ;)
          python main.py --csv-encoding utf-8     # CSV Encoding (Standard: utf-8)
          python main.py --csv-decimal ","        # Dezimaltrennzeichen (Standard: ,)
          python main.py --csv-english            # Englische CSV-Header
          python main.py --csv-no-info            # Keine Info-Zeile unter Header

        Schwellwerte:
          python main.py --battery-idle 20        # Batterie Idle-Schwelle in Watt
          python main.py --autarky-high 80        # Autarkie hoch ab % (grün)
          python main.py --autarky-medium 40      # Autarkie mittel ab % (gelb)
          python main.py --battery-soc-high 85    # Batterie SOC hoch ab %
          python main.py --battery-soc-medium 25  # Batterie SOC mittel ab %

        Kombinationen:
          python main.py --ip 192.168.1.100 --interval 10 --no-colors
          python main.py --log-level WARNING --no-logging
          python main.py --data-file /path/to/solar_$(date +%%Y%%m%%d).csv
          python main.py --csv-delimiter "," --csv-decimal "." --csv-english
          python main.py --disable-devices --log-level INFO
          python main.py --device-config pool.json --no-colors
          python main.py --device-log-interval 60 --no-device-events
          python main.py --disable-devices --no-logging

        Umgebungsvariablen (alternativ zu Kommandozeilen-Optionen):
          export FRONIUS_IP=192.168.178.100
          export UPDATE_INTERVAL=10
          export LOG_LEVEL=WARNING
          export ENABLE_COLORS=false
          export ENABLE_DATA_LOGGING=false
          export ENABLE_DAILY_STATS_LOGGING=false
          export ENABLE_DEVICE_CONTROL=true       # oder false zum Deaktivieren
          export DEVICE_CONFIG_FILE=devices.json
          export DEVICE_HYSTERESIS_MINUTES=5
          export ENABLE_DEVICE_LOGGING=true
          export DEVICE_LOG_DIR=Devicelogs
          export DEVICE_LOG_INTERVAL=60
          export DEVICE_LOG_EVENTS=true
          export DEVICE_LOG_STATUS=true
          export DEVICE_LOG_DAILY_SUMMARY=true
          export SOLAR_DATA_DIR=MySolarData
          export DAILY_STATS_DIR=MyDailyStats
          python main.py
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

    # CSV Format Optionen
    parser.add_argument(
        '--csv-delimiter',
        type=str,
        choices=[',', ';', '\t', '|'],
        help='CSV Trennzeichen (Standard: ;)'
    )

    parser.add_argument(
        '--csv-encoding',
        type=str,
        choices=['utf-8', 'latin-1', 'cp1252', 'iso-8859-1'],
        help='CSV Encoding (Standard: utf-8)'
    )

    parser.add_argument(
        '--csv-decimal',
        type=str,
        choices=['.', ','],
        help='Dezimaltrennzeichen (Standard: ,)'
    )

    parser.add_argument(
        '--csv-english',
        action='store_true',
        help='Verwendet englische CSV-Header statt deutsche'
    )

    parser.add_argument(
        '--csv-no-info',
        action='store_true',
        help='Keine Info-Zeile unter CSV-Header'
    )

    # Daten-Logging Verzeichnis
    parser.add_argument(
        '--data-log-dir',
        type=str,
        help='Hauptverzeichnis für Log-Dateien (Standard: Datalogs)'
    )

    parser.add_argument(
        '--solar-data-dir',
        type=str,
        help='Unterverzeichnis für Solardaten (Standard: Solardata)'
    )

    parser.add_argument(
        '--daily-stats-dir',
        type=str,
        help='Unterverzeichnis für Tagesstatistiken (Standard: Dailystats)'
    )

    parser.add_argument(
        '--data-log-base-name',
        type=str,
        help='Basis-Name für Log-Dateien (Standard: solar_data)'
    )

    parser.add_argument(
        '--no-daily-stats-logging',
        action='store_true',
        help='Deaktiviert das CSV-Logging der Tagesstatistiken'
    )

    # Batterie
    parser.add_argument(
        '--battery-idle',
        type=float,
        help='Batterie Idle-Schwellwert in Watt (Standard: 10)'
    )

    # Schwellwerte
    parser.add_argument(
        '--battery-soc-high',
        type=float,
        help='Batterie SOC Schwellwert für grün in %% (Standard: 80)'
    )

    parser.add_argument(
        '--battery-soc-medium',
        type=float,
        help='Batterie SOC Schwellwert für gelb in %% (Standard: 30)'
    )

    parser.add_argument(
        '--autarky-high',
        type=float,
        help='Autarkie Schwellwert für grün in %% (Standard: 75)'
    )

    parser.add_argument(
        '--autarky-medium',
        type=float,
        help='Autarkie Schwellwert für gelb in %% (Standard: 50)'
    )

    parser.add_argument(
        '--pv-power-high',
        type=float,
        help='PV-Leistung Schwellwert für grün in Watt (Standard: 3000)'
    )

    parser.add_argument(
        '--pv-power-medium',
        type=float,
        help='PV-Leistung Schwellwert für gelb in Watt (Standard: 1000)'
    )

    parser.add_argument(
        '--surplus-high',
        type=float,
        help='Überschuss Schwellwert für grün in Watt (Standard: 2000)'
    )

    parser.add_argument(
        '--surplus-medium',
        type=float,
        help='Überschuss Schwellwert für gelb in Watt (Standard: 500)'
    )

    parser.add_argument(
        '--surplus-display',
        type=float,
        help='Überschuss Anzeige-Schwellwert in Watt (Standard: 0)'
    )

    # System
    parser.add_argument(
        '--skip-check',
        action='store_true',
        help='Überspringe automatische Dependency-Prüfung'
    )

    # Tagesstatistiken
    parser.add_argument(
        '--no-daily-stats',
        action='store_true',
        help='Deaktiviert die periodische Anzeige der Tagesstatistiken'
    )

    parser.add_argument(
        '--daily-stats-interval',
        type=int,
        help='Intervall für Tagesstatistik-Anzeige in Sekunden (Standard: 1800 = 30 Min)'
    )

    # Sonstiges
    parser.add_argument(
        '--version',
        action='version',
        version='Fronius Solar Monitor 1.0.0'
    )

    # Gerätesteuerung
    parser.add_argument(
        '--disable-devices',
        action='store_true',
        help='Deaktiviert die intelligente Gerätesteuerung (standardmäßig aktiviert)'
    )

    parser.add_argument(
        '--device-config',
        type=str,
        help='Pfad zur Gerätekonfigurationsdatei (Standard: devices.json)'
    )

    parser.add_argument(
        '--device-hysteresis',
        type=int,
        help='Hysterese-Zeit in Minuten für Geräteschaltungen (Standard: 5)'
    )

    # Device-Logging Argumente
    parser.add_argument(
        '--device-log-dir',
        type=str,
        help='Unterverzeichnis für Geräte-Logs (Standard: Devicelogs)'
    )

    parser.add_argument(
        '--no-device-logging',
        action='store_true',
        help='Deaktiviert das Geräte-Logging komplett'
    )

    parser.add_argument(
        '--device-log-interval',
        type=int,
        help='Intervall für Geräte-Status-Logging in Sekunden (Standard: 60)'
    )

    parser.add_argument(
        '--no-device-events',
        action='store_true',
        help='Deaktiviert das Event-basierte Geräte-Logging'
    )

    parser.add_argument(
        '--no-device-status',
        action='store_true',
        help='Deaktiviert das periodische Status-Logging'
    )

    parser.add_argument(
        '--no-device-summary',
        action='store_true',
        help='Deaktiviert die tägliche Geräte-Zusammenfassung'
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

    # CSV Format Optionen
    if args.csv_delimiter:
        config.CSV_DELIMITER = args.csv_delimiter

    if args.csv_encoding:
        config.CSV_ENCODING = args.csv_encoding

    if args.csv_decimal:
        config.CSV_DECIMAL_SEPARATOR = args.csv_decimal

    if args.csv_english:
        config.CSV_USE_GERMAN_HEADERS = False

    if args.csv_no_info:
        config.CSV_INCLUDE_INFO_ROW = False

    # Daten-Logging
    if args.data_log_dir:
        config.DATA_LOG_DIR = args.data_log_dir

    if args.solar_data_dir:
        config.SOLAR_DATA_DIR = args.solar_data_dir

    if args.daily_stats_dir:
        config.DAILY_STATS_DIR = args.daily_stats_dir

    if args.data_log_base_name:
        config.DATA_LOG_BASE_NAME = args.data_log_base_name

    if args.no_daily_stats_logging:
        config.ENABLE_DAILY_STATS_LOGGING = False

    # Batterie
    if args.battery_idle is not None:
        config.BATTERY_IDLE_THRESHOLD = args.battery_idle

    # Schwellwerte - mit der neuen THRESHOLDS-Struktur
    if args.battery_soc_high is not None:
        config.THRESHOLDS['battery_soc']['high'] = args.battery_soc_high

    if args.battery_soc_medium is not None:
        config.THRESHOLDS['battery_soc']['medium'] = args.battery_soc_medium

    if args.autarky_high is not None:
        config.THRESHOLDS['autarky']['high'] = args.autarky_high

    if args.autarky_medium is not None:
        config.THRESHOLDS['autarky']['medium'] = args.autarky_medium

    if args.pv_power_high is not None:
        config.THRESHOLDS['pv_power']['high'] = args.pv_power_high

    if args.pv_power_medium is not None:
        config.THRESHOLDS['pv_power']['medium'] = args.pv_power_medium

    if args.surplus_high is not None:
        config.THRESHOLDS['surplus']['high'] = args.surplus_high

    if args.surplus_medium is not None:
        config.THRESHOLDS['surplus']['medium'] = args.surplus_medium

    if args.surplus_display is not None:
        config.SURPLUS_DISPLAY_THRESHOLD = args.surplus_display

    # Tagesstatistiken
    if args.no_daily_stats:
        config.SHOW_DAILY_STATS = False

    if args.daily_stats_interval is not None:
        config.DAILY_STATS_INTERVAL = args.daily_stats_interval

    # Gerätesteuerung - WICHTIG: Logik umgekehrt!
    if args.disable_devices:
        config.ENABLE_DEVICE_CONTROL = False

    if args.device_config:
        config.DEVICE_CONFIG_FILE = args.device_config

    if args.device_hysteresis is not None:
        config.DEVICE_HYSTERESIS_MINUTES = args.device_hysteresis

    # Device-Logging
    if args.device_log_dir:
        config.DEVICE_LOG_DIR = args.device_log_dir

    if args.no_device_logging:
        config.ENABLE_DEVICE_LOGGING = False

    if args.device_log_interval is not None:
        config.DEVICE_LOG_INTERVAL = args.device_log_interval

    if args.no_device_events:
        config.DEVICE_LOG_EVENTS = False

    if args.no_device_status:
        config.DEVICE_LOG_STATUS = False

    if args.no_device_summary:
        config.DEVICE_LOG_DAILY_SUMMARY = False


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
                    time.sleep(config.UPDATE_INTERVAL)
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