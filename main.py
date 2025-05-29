#!/usr/bin/env python3
"""
Fronius Solar Monitor - Haupteinstiegspunkt

Verwendung:
    python main.py                       # Standard-Ausführung
    python main.py --ip 192.168.1.100    # Mit anderer IP
    python main.py --interval 10         # Mit anderem Update-Intervall
    python main.py --timeout 10          # Mit anderem Timeout
    python main.py --no-colors           # Ohne Farben
    python main.py --simple              # Einzeilige Ausgabe
    python main.py --no-logging          # Ohne CSV-Datei
    python main.py --log-file my.log     # Eigene Log-Datei
    python main.py --data-file data.csv  # Eigene Daten-CSV
    python main.py --log-level DEBUG     # Debug-Level
    python main.py --skip-check          # Dependency-Check überspringen
    python main.py --version             # Version anzeigen
    python main.py --help                # Hilfe anzeigen
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
  python main.py                          # Standard-Ausführung
  python main.py --ip 192.168.178.100     # Andere IP-Adresse
  python main.py --interval 10            # Update alle 10 Sekunden
  python main.py --timeout 10             # Längerer Timeout für langsame Verbindungen
  python main.py --no-colors              # Ohne farbige Ausgabe
  python main.py --simple                 # Einzeilige Ausgabe für kleine Displays
  python main.py --no-logging             # Ohne CSV-Logging
  python main.py --log-file my.log        # Eigene Log-Datei
  python main.py --data-file data.csv     # Eigene Daten-CSV
  python main.py --log-level DEBUG        # Debug-Modus
  python main.py --log-level WARNING      # Nur Warnungen und Fehler
  python main.py --skip-check             # Dependency-Check überspringen
  python main.py --version                # Version anzeigen

Kombinationen:
  python main.py --ip 192.168.1.100 --interval 10 --no-colors
  python main.py --log-level WARNING --no-logging
  python main.py --data-file /path/to/solar_$(date +%%Y%%m%%d).csv

Umgebungsvariablen (alternativ zu Kommandozeilen-Optionen):
  export FRONIUS_IP=192.168.178.100
  export UPDATE_INTERVAL=10
  export LOG_LEVEL=WARNING
  export ENABLE_COLORS=false
  export ENABLE_DATA_LOGGING=false
  python main.py

Tipps:
  - Verwende --log-level WARNING um die API-Version-Fehler zu unterdrücken
  - Mit --no-logging sparst du Speicherplatz wenn du keine Historie brauchst
  - Die Daten-CSV kann in Excel oder mit pandas analysiert werden
  - Mit --skip-check kannst du die Dependency-Prüfung überspringen
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

    # System
    parser.add_argument(
        '--skip-check',
        action='store_true',
        help='Überspringe automatische Dependency-Prüfung'
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