"""
Fronius Solar Monitor - Haupteinstiegspunkt
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from cli import parse_arguments, check_dependencies, apply_args_to_config

args = parse_arguments()

api_enabled = not getattr(args, 'no_api', False)

if not check_dependencies(args.skip_check, with_api=api_enabled):
    sys.exit(1)

from solar_monitor import SolarMonitor, Config, SettingsStore

APIServer = None  # Standardwert falls Import fehlschlägt
if api_enabled:
    try:
        from api import APIServer
    except ImportError:
        print("Warnung: API-Module konnten nicht importiert werden. API wird deaktiviert.")
        api_enabled = False
        APIServer = None  # Explizit None setzen

def main():
    """Hauptfunktion"""
    # Konfiguration erstellen: Umgebung < gespeicherte Einstellungen < CLI-Argumente
    config = Config()
    settings = SettingsStore(config)
    settings.load()
    apply_args_to_config(config, args)

    if hasattr(args, 'no_api') and args.no_api:
        config.api.enabled = False

    if hasattr(args, 'api_host') and args.api_host:
        config.api.host = args.api_host
    if hasattr(args, 'api_port') and args.api_port:
        config.api.port = args.api_port

    api_server = None

    try:
        monitor = SolarMonitor(config, settings)

        if config.api.enabled and api_enabled and APIServer is not None:
            try:
                api_server = APIServer(monitor, config)
                api_server.start(host=config.api.host, port=config.api.port)

                time.sleep(1)

                dashboard_url = f"http://localhost:{config.api.port}/"

                print(f"API Server gestartet auf http://{config.api.host}:{config.api.port}")
                print(f"Dashboard: {dashboard_url}")
                print(f"API Dokumentation: http://localhost:{config.api.port}/docs")
                print("")

            except Exception as e:
                print(f"Warnung: API Server konnte nicht gestartet werden: {e}")
                print("Fahre ohne API fort...")
                api_server = None
                config.api.enabled = False

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

        monitor.start()

    except KeyboardInterrupt:
        print("\nProgramm durch Benutzer beendet.")
        sys.exit(0)
    except Exception as e:
        print(f"\nFehler: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if api_server:
            try:
                api_server.stop()
                print("API Server gestoppt.")
            except Exception as e:
                print(f"Fehler beim Stoppen des API Servers: {e}")


if __name__ == "__main__":
    main()