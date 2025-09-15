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
from cli import parse_arguments, check_dependencies, apply_args_to_config

# Parse Argumente zuerst
args = parse_arguments()

# Bestimme ob API aktiviert ist (Standard: ja, außer --no-api ist gesetzt)
api_enabled = not getattr(args, 'no_api', False)

# Dependencies prüfen (inkl. API deps wenn API aktiviert)
if not check_dependencies(args.skip_check, with_api=api_enabled):
    sys.exit(1)

# Erst jetzt die anderen Imports (nachdem Dependencies geprüft wurden)
from solar_monitor import SolarMonitor, Config

# API Import nur wenn benötigt
if api_enabled:
    try:
        from api import APIServer
    except ImportError:
        print("Warnung: API-Module konnten nicht importiert werden. API wird deaktiviert.")
        api_enabled = False


def main():
    """Hauptfunktion"""
    # Konfiguration erstellen
    config = Config()

    # Kommandozeilen-Argumente anwenden
    apply_args_to_config(config, args)

    # API-Status explizit aus args übernehmen (falls --no-api gesetzt wurde)
    if hasattr(args, 'no_api') and args.no_api:
        config.api.enabled = False

    # API-Host und Port aus args übernehmen wenn gesetzt
    if hasattr(args, 'api_host') and args.api_host:
        config.api.host = args.api_host
    if hasattr(args, 'api_port') and args.api_port:
        config.api.port = args.api_port

    try:
        # Monitor erstellen
        monitor = SolarMonitor(config)

        # API Server starten wenn aktiviert
        api_server = None
        if config.api.enabled and api_enabled:
            try:
                api_server = APIServer(monitor, config)
                api_server.start(host=config.api.host, port=config.api.port)

                # Warte kurz bis API läuft
                time.sleep(1)

                print(f"API Server gestartet auf http://{config.api.host}:{config.api.port}")
                print(f"Dashboard: http://localhost:{config.api.port}/")
                print(f"API Dokumentation: http://localhost:{config.api.port}/docs")
                print("")  # Leerzeile für bessere Lesbarkeit

            except Exception as e:
                print(f"Warnung: API Server konnte nicht gestartet werden: {e}")
                print("Fahre ohne API fort...")
                api_server = None
                config.api.enabled = False

        # Einfache Anzeige, wenn gewünscht
        if hasattr(args, 'simple') and args.simple:
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
            try:
                api_server.stop()
                print("API Server gestoppt.")
            except Exception as e:
                print(f"Fehler beim Stoppen des API Servers: {e}")


if __name__ == "__main__":
    main()