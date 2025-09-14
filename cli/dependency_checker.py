"""
Dependency Checker für den Smart Energy Manager.
"""

import sys
import subprocess
import importlib.util
from typing import Dict, List, Tuple, Optional

# Erforderliche Dependencies
REQUIRED_DEPENDENCIES: Dict[str, str] = {
    'requests': 'requests>=2.31.0',
    'rich': 'rich>=13.7.0',
    'phue': 'phue>=1.1',
}

OPTIONAL_DEPENDENCIES: Dict[str, str] = {
    'fastapi': 'fastapi>=0.104.0',
    'uvicorn': 'uvicorn>=0.24.0',
}


def check_dependencies(skip_check: bool = False, with_api: bool = False) -> bool:
    """
    Prüft und installiert fehlende Dependencies.

    Args:
        skip_check: Wenn True, wird die Prüfung übersprungen
        with_api: Wenn True, werden auch API-Dependencies geprüft

    Returns:
        True wenn alle Dependencies verfügbar sind, False sonst
    """
    if skip_check:
        return True

    # Sammle fehlende Dependencies
    missing_deps = _find_missing_dependencies()

    # Prüfe API-Dependencies wenn --api gesetzt
    if with_api:
        for module_name, pip_package in OPTIONAL_DEPENDENCIES.items():
            if not _check_single_dependency(module_name, pip_package):
                missing_deps.append((module_name, pip_package))

    # Wenn alle Dependencies installiert sind
    if not missing_deps:
        return True

    # Zeige fehlende Dependencies
    _display_missing_dependencies(missing_deps)

    # Frage nach automatischer Installation
    if _ask_for_installation():
        return _install_missing_dependencies(missing_deps)
    else:
        _display_manual_installation_hint(missing_deps)
        return False


def _check_single_dependency(module_name: str, pip_package: str) -> bool:
    """
    Prüft ob ein einzelnes Modul installiert ist.

    Args:
        module_name: Name des Python-Moduls zum Importieren
        pip_package: Package-Name mit Version für pip install

    Returns:
        True wenn installiert, False sonst
    """
    return importlib.util.find_spec(module_name) is not None


def _find_missing_dependencies() -> List[Tuple[str, str]]:
    """
    Findet alle fehlenden Dependencies.

    Returns:
        Liste von Tupeln (module_name, pip_package)
    """
    missing = []
    for module_name, pip_package in REQUIRED_DEPENDENCIES.items():
        if not _check_single_dependency(module_name, pip_package):
            missing.append((module_name, pip_package))
    return missing


def _display_missing_dependencies(missing_deps: List[Tuple[str, str]]) -> None:
    """
    Zeigt fehlende Dependencies an.

    Args:
        missing_deps: Liste fehlender Dependencies
    """
    print("Fehlende Pakete gefunden:")
    for module_name, pip_package in missing_deps:
        print(f"  - {module_name} ({pip_package})")


def _ask_for_installation() -> bool:
    """
    Fragt den Benutzer ob Dependencies installiert werden sollen.

    Returns:
        True wenn Installation gewünscht
    """
    try:
        response = input("\nSollen die fehlenden Pakete automatisch installiert werden? (j/n): ")
        return response.lower() in ['j', 'ja', 'y', 'yes', '']
    except KeyboardInterrupt:
        print("\nInstallation abgebrochen.")
        return False


def _install_missing_dependencies(missing_deps: List[Tuple[str, str]]) -> bool:
    """
    Installiert fehlende Dependencies.

    Args:
        missing_deps: Liste fehlender Dependencies

    Returns:
        True wenn alle erfolgreich installiert wurden
    """
    print("\nInstalliere fehlende Pakete...")

    failed_installs = []
    for module_name, pip_package in missing_deps:
        if not _install_dependency(pip_package):
            failed_installs.append(pip_package)

    if failed_installs:
        _display_failed_installations(failed_installs)
        return False

    # Alle Installationen erfolgreich
    print("\nAlle Pakete erfolgreich installiert!")

    # Cache invalidieren für neue Imports
    import importlib
    importlib.invalidate_caches()

    return True


def _install_dependency(pip_package: str) -> bool:
    """
    Installiert ein einzelnes Package.

    Args:
        pip_package: Package-Name mit Version für pip install

    Returns:
        True bei erfolgreicher Installation, False sonst
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


def _display_failed_installations(failed_installs: List[str]) -> None:
    """
    Zeigt fehlgeschlagene Installationen an.

    Args:
        failed_installs: Liste fehlgeschlagener Packages
    """
    print("\nFehler bei der Installation folgender Pakete:")
    for package in failed_installs:
        print(f"  - {package}")
    print("\nBitte installieren Sie diese manuell mit:")
    print(f"  pip install {' '.join(failed_installs)}")


def _display_manual_installation_hint(missing_deps: List[Tuple[str, str]]) -> None:
    """
    Zeigt Hinweis für manuelle Installation.

    Args:
        missing_deps: Liste fehlender Dependencies
    """
    print("\nInstallation übersprungen.")
    print("Bitte installieren Sie die fehlenden Pakete manuell mit:")
    pip_packages = [pip_pkg for _, pip_pkg in missing_deps]
    print(f"  pip install {' '.join(pip_packages)}")