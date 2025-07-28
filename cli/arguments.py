"""
Argument-Definitionen für den Smart Energy Manager CLI.
"""

import log_system
from typing import Dict, Any, List

ARGUMENT_GROUPS: Dict[str, Dict[str, Any]] = {
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

    'log_system': {
        'description': 'Logging',
        'arguments': [
            {
                'name': '--no-log_system',
                'action': 'store_true',
                'help': 'Deaktiviert CSV-Datenlogging',
                'config_path': 'log_system.enable_data_logging',
                'config_value': lambda args: not args.no_logging
            },
            {
                'name': '--log-file',
                'type': str,
                'help': 'Pfad zur Log-Datei (Standard: solar_monitor.log)',
                'config_path': 'log_system.log_file'
            },
            {
                'name': '--log-level',
                'choices': ['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                'default': 'INFO',
                'help': 'Log-Level für Konsole und Datei (Standard: INFO)',
                'config_path': 'log_system.log_level',
                'config_value': lambda args: getattr(log_system, args.log_level)
            },
            {
                'name': '--no-daily-stats-log_system',
                'action': 'store_true',
                'help': 'Deaktiviert das CSV-Logging der Tagesstatistiken',
                'config_path': 'log_system.enable_daily_stats_logging',
                'config_value': lambda args: not args.no_daily_stats_logging
            },
            {
                'name': '--no-database-log_system',
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
                'name': '--no-device-log_system',
                'action': 'store_true',
                'help': 'Deaktiviert das Geräte-Logging komplett',
                'config_path': 'log_system.enable_device_logging',
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