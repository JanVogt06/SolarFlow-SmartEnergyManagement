"""
Philips Hue Integration für den Smart Energy Manager
"""

import threading
import time
from typing import Optional, Dict, Any, List, Tuple, NamedTuple

from .interfaces import ISmartDeviceInterface


class HueLight(NamedTuple):
    """Zustand eines Hue-Geräts."""
    light_id: int
    name: str
    on: bool
    reachable: bool


def _import_bridge() -> Any:
    """Importiert phue.Bridge erst bei Bedarf (vermeidet harte Dependency)."""
    from phue import Bridge
    return Bridge


class HueInterface(ISmartDeviceInterface):
    """Implementierung des Smart Device Interface für Philips Hue"""

    LINK_BUTTON_RETRIES = 3
    LINK_BUTTON_WAIT = 10

    def __init__(self, bridge_ip: str, cache_ttl: float = 2.0):
        """
        Initialisiert die Hue-Verbindung.

        Args:
            bridge_ip: IP-Adresse der Hue Bridge
            cache_ttl: Maximales Alter der Zustandsdaten in Sekunden
        """
        super().__init__({'bridge_ip': bridge_ip})
        self.bridge_ip = bridge_ip
        self.cache_ttl = cache_ttl
        self.bridge: Optional[Any] = None

        self._lights: Dict[str, HueLight] = {}
        self._fetched_at: float = 0.0
        self._lock = threading.RLock()

    def connect(self) -> bool:
        """
        Verbindet zur Hue Bridge.

        Returns:
            True bei erfolgreicher Verbindung
        """
        try:
            bridge_cls = _import_bridge()
        except ImportError:
            self.logger.error("phue-Library nicht installiert! Führe aus: pip install phue")
            return False

        if not self._open_bridge(bridge_cls):
            self._connected = False
            return False

        self._connected = True
        self.refresh(force=True)
        self.logger.info(f"Erfolgreich mit Hue Bridge verbunden ({len(self._lights)} Geräte)")
        return True

    def _open_bridge(self, bridge_cls: Any) -> bool:
        """Baut die Bridge-Verbindung auf, ggf. mit Warten auf den Link-Button."""
        try:
            self.logger.info(f"Verbinde zu Hue Bridge: {self.bridge_ip}")
            self.bridge = bridge_cls(self.bridge_ip)
            self.bridge.connect()
            return True
        except Exception as e:
            if "link button has not been pressed" not in str(e):
                self.logger.error(f"Fehler bei Hue-Verbindung: {e}")
                return False

        self.logger.warning("Bitte JETZT den Knopf auf der Hue Bridge drücken!")
        for attempt in range(1, self.LINK_BUTTON_RETRIES + 1):
            time.sleep(self.LINK_BUTTON_WAIT)
            try:
                self.bridge = bridge_cls(self.bridge_ip)
                self.bridge.connect()
                return True
            except Exception:
                self.logger.info(
                    f"Registrierung {attempt}/{self.LINK_BUTTON_RETRIES} fehlgeschlagen, warte weiter..."
                )

        self.logger.error("Hue Bridge Registrierung fehlgeschlagen")
        return False

    def disconnect(self) -> None:
        """Trennt die Verbindung zur Hue Bridge."""
        with self._lock:
            self._connected = False
            self.bridge = None
            self._lights.clear()
            self._fetched_at = 0.0
        self.logger.info("Hue Bridge Verbindung getrennt")

    def refresh(self, force: bool = False) -> bool:
        """
        Liest Namen und Zustand aller Hue-Geräte neu von der Bridge.

        Args:
            force: Ignoriert den Cache und fragt die Bridge in jedem Fall an

        Returns:
            True wenn aktuelle Daten vorliegen
        """
        with self._lock:
            if not self.bridge:
                return False

            if not force and (time.monotonic() - self._fetched_at) < self.cache_ttl:
                return True

            try:
                raw = self.bridge.request('GET', f'/api/{self.bridge.username}/lights/')
            except Exception as e:
                self.logger.error(f"Fehler beim Laden der Hue-Geräte: {e}")
                return False

            lights = self._parse_lights(raw)
            if lights is None:
                return False

            self._log_list_changes(lights)
            self._lights = lights
            self._fetched_at = time.monotonic()
            return True

    def _parse_lights(self, raw: Any) -> Optional[Dict[str, HueLight]]:
        """
        Wandelt die Bridge-Antwort in Geräte-Zustände um.

        Args:
            raw: Antwort des /lights-Endpunkts

        Returns:
            Dict Name -> HueLight oder None wenn die Antwort unbrauchbar ist
        """
        if not isinstance(raw, dict):
            self.logger.error(f"Unerwartete Antwort der Hue Bridge: {raw}")
            return None

        lights: Dict[str, HueLight] = {}
        for light_id, entry in raw.items():
            try:
                state = entry['state']
                name = entry['name']
                lights[name] = HueLight(
                    light_id=int(light_id),
                    name=name,
                    on=bool(state.get('on', False)),
                    reachable=bool(state.get('reachable', True))
                )
            except (KeyError, TypeError, ValueError):
                self.logger.warning(f"Hue-Gerät {light_id} übersprungen: unvollständige Daten")

        return lights

    def _log_list_changes(self, lights: Dict[str, HueLight]) -> None:
        """Loggt neu aufgetauchte und verschwundene Hue-Geräte."""
        if not self._lights:
            return

        added = sorted(set(lights) - set(self._lights))
        removed = sorted(set(self._lights) - set(lights))
        if added:
            self.logger.info(f"Neue Hue-Geräte: {', '.join(added)}")
        if removed:
            self.logger.info(f"Hue-Geräte verschwunden: {', '.join(removed)}")

    def _get_light(self, device_name: str) -> Optional[HueLight]:
        """Gibt den (ggf. aufgefrischten) Zustand eines Geräts zurück."""
        with self._lock:
            self.refresh()
            return self._lights.get(device_name)

    def _set_on(self, device_name: str, on: bool) -> bool:
        """
        Schaltet ein Gerät und wertet die Antwort der Bridge aus.

        Args:
            device_name: Name des Geräts
            on: Zielzustand

        Returns:
            True wenn die Bridge den Befehl ohne Fehler angenommen hat
        """
        if not self._connected or not self.bridge:
            self.logger.warning("Keine Verbindung zur Hue Bridge")
            return False

        light = self._get_light(device_name)
        if light is None:
            self.logger.error(f"Hue-Gerät '{device_name}' nicht gefunden")
            return False

        try:
            result = self.bridge.request(
                'PUT',
                f'/api/{self.bridge.username}/lights/{light.light_id}/state',
                {'on': on}
            )
        except Exception as e:
            self.logger.error(f"Fehler beim Schalten von '{device_name}': {e}")
            return False

        error = self._first_error(result)
        if error:
            self.logger.error(f"Hue meldet Fehler für '{device_name}': {error}")
            return False

        with self._lock:
            cached = self._lights.get(device_name)
            if cached:
                self._lights[device_name] = cached._replace(on=on)

        self.logger.info(f"Schalte '{device_name}' {'EIN' if on else 'AUS'} (Hue)")
        return True

    @staticmethod
    def _first_error(result: Any) -> Optional[str]:
        """Sucht die erste Fehlermeldung in einer Bridge-Antwort."""
        entries = [result] if isinstance(result, dict) else result
        if not isinstance(entries, list):
            return None

        for entry in entries:
            if isinstance(entry, dict) and 'error' in entry:
                error = entry['error']
                return str(error.get('description', error) if isinstance(error, dict) else error)
        return None

    def switch_on(self, device_name: str) -> bool:
        """
        Schaltet ein Gerät ein.

        Args:
            device_name: Name des Geräts (muss exakt dem Hue-Namen entsprechen)

        Returns:
            True bei Erfolg
        """
        return self._set_on(device_name, True)

    def switch_off(self, device_name: str) -> bool:
        """
        Schaltet ein Gerät aus.

        Args:
            device_name: Name des Geräts

        Returns:
            True bei Erfolg
        """
        return self._set_on(device_name, False)

    def get_state(self, device_name: str) -> Optional[bool]:
        """
        Holt den aktuellen Status eines Geräts.

        Args:
            device_name: Name des Geräts

        Returns:
            True wenn an, False wenn aus, None bei Fehler
        """
        light = self._get_light(device_name)
        return light.on if light else None

    def get_status(self, device_name: str) -> Optional[Tuple[bool, bool]]:
        """
        Holt Schaltzustand und Erreichbarkeit eines Geräts.

        Args:
            device_name: Name des Geräts

        Returns:
            Tupel (eingeschaltet, erreichbar) oder None wenn unbekannt
        """
        light = self._get_light(device_name)
        return (light.on, light.reachable) if light else None

    def list_devices(self) -> List[str]:
        """
        Listet alle verfügbaren Geräte auf.

        Returns:
            Liste der Gerätenamen
        """
        if not self._connected:
            return []

        with self._lock:
            self.refresh(force=True)
            return sorted(self._lights)

    def is_device_available(self, device_name: str) -> bool:
        """
        Prüft ob ein Gerät in Hue existiert.

        Args:
            device_name: Name des Geräts

        Returns:
            True wenn Gerät in Hue existiert
        """
        return self._get_light(device_name) is not None

    @property
    def interface_type(self) -> str:
        """Gibt den Interface-Typ zurück."""
        return "hue"
