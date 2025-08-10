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

# Parse Argumente zuerst (für --skip-check)
args = parse_arguments()

# Dependencies prüfen bevor wir weitere Module importieren
if not check_dependencies(args.skip_check):
    sys.exit(1)

# Erst jetzt die anderen Imports (nachdem Dependencies geprüft wurden)
from cli import apply_args_to_config
from solar_monitor import SolarMonitor, Config


def main():
    """Hauptfunktion"""
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


if __name__ == "__main__":
    main()