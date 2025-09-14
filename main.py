#!/usr/bin/env python3
"""
Fronius Solar Monitor - Haupteinstiegspunkt
"""

import sys
import time
from pathlib import Path

# Füge das Projekt-Verzeichnis zum Python-Path hinzu
sys.path.insert(0, str(Path(__file__).parent))

# WICHTIG: Dependency Check VOR allen anderen Imports!
from cli import parse_arguments, check_dependencies

# Parse Argumente zuerst (für --skip-check und --api)
args = parse_arguments()

# Dependencies prüfen (inkl. API deps wenn --api gesetzt)
if not check_dependencies(args.skip_check, with_api=args.api if hasattr(args, 'api') else False):
    sys.exit(1)

# Erst jetzt die anderen Imports (nachdem Dependencies geprüft wurden)
from cli import apply_args_to_config
from solar_monitor import SolarMonitor, Config

# API Import nur wenn benötigt
if hasattr(args, 'api') and args.api:
    from api import APIServer

def main():
    """Hauptfunktion"""
    # Konfiguration erstellen
    config = Config()

    # Kommandozeilen-Argumente anwenden
    apply_args_to_config(config, args)

    try:
        # Monitor erstellen
        monitor = SolarMonitor(config)

        # API Server starten wenn gewünscht
        api_server = None
        if hasattr(args, 'api') and args.api:
            api_server = APIServer(monitor, config)
            api_host = args.api_host if hasattr(args, 'api_host') else '0.0.0.0'
            api_port = args.api_port if hasattr(args, 'api_port') else 8000
            api_server.start(host=api_host, port=api_port)

            # Warte kurz bis API läuft
            time.sleep(1)

        # Einfache Anzeige, wenn gewünscht
        if args.simple:
            print("Simple Mode aktiviert - Einzeilige Ausgabe")
            try:
                while True:
                    data = monitor.get_current_data()
                    if data:
                        monitor.display.show_simple(data)
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
    finally:
        # API Server stoppen wenn vorhanden
        if api_server:
            api_server.stop()


if __name__ == "__main__":
    main()