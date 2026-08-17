"""
Config Applicator - Wendet CLI-Argumente auf die Konfiguration an.
"""

import argparse
from typing import Any
from .arguments import ARGUMENT_GROUPS


def apply_args_to_config(config: Any, args: argparse.Namespace) -> None:
    """
    Wendet alle Kommandozeilen-Argumente auf die Konfiguration an.

    Args:
        config: Config-Instanz
        args: Geparste Argumente
    """
    for group_name, group_config in ARGUMENT_GROUPS.items():
        for arg_config in group_config['arguments']:
            if 'config_path' not in arg_config:
                continue

            arg_name = arg_config['name'].lstrip('-').replace('-', '_')

            arg_value = getattr(args, arg_name, None)

            # store_true ohne Angabe liefert False - dann Env-Wert behalten
            is_store_true = arg_config.get('action') == 'store_true'
            if is_store_true and arg_value is False:
                continue

            if hasattr(args, arg_name) and arg_value is not None:
                if 'config_value' in arg_config:
                    value = arg_config['config_value'](args)
                else:
                    value = getattr(args, arg_name)

                try:
                    _set_nested_attr(config, arg_config['config_path'], value)
                except AttributeError as e:
                    print(f"Warnung: Konnte {arg_config['config_path']} nicht setzen: {e}")


def _set_nested_attr(obj: Any, path: str, value: Any) -> None:
    """
    Setzt ein verschachteltes Attribut über einen Punkt-getrennten Pfad.

    Args:
        obj: Objekt
        path: Punkt-getrennter Pfad (z.B. "connection.fronius_ip")
        value: Zu setzender Wert
    """
    attrs = path.split('.')

    for attr in attrs[:-1]:
        obj = getattr(obj, attr)

    if '.' in attrs[-1]:  # For paths like "thresholds.battery_soc.high"
        parts = attrs[-1].split('.')
        parent = getattr(obj, parts[0])

        if isinstance(parent, dict):
            parent[parts[1]] = value
        else:
            setattr(parent, parts[1], value)
    else:
        setattr(obj, attrs[-1], value)