"""
Einfache Philips Hue Integration für den Smart Energy Manager
"""

import logging
import time
from typing import Optional, Dict, Any, List  # <-- List hinzugefügt!
from phue import Bridge


class HueInterface:
    """Einfache Schnittstelle zur Philips Hue Bridge"""

    def __init__(self, bridge_ip: str):
        """
        Initialisiert die Hue-Verbindung.

        Args:
            bridge_ip: IP-Adresse der Hue Bridge
        """
        self.logger = logging.getLogger(__name__)
        self.bridge_ip = bridge_ip
        self.bridge: Optional[Bridge] = None
        self.connected = False

        # Cache für Geräte-IDs
        self.device_map: Dict[str, Any] = {}

    def connect(self) -> bool:
        """
        Verbindet zur Hue Bridge.

        Returns:
            True bei erfolgreicher Verbindung
        """
        try:
            self.logger.info(f"Verbinde zu Hue Bridge: {self.bridge_ip}")
            self.bridge = Bridge(self.bridge_ip)

            # Beim ersten Mal muss der Knopf gedrückt werden
            self.bridge.connect()

            # Lade alle Lichter
            self._refresh_device_map()

            self.connected = True
            self.logger.info("Erfolgreich mit Hue Bridge verbunden")
            return True

        except Exception as e:
            if "link button has not been pressed" in str(e):
                self.logger.warning("=== HUE BRIDGE REGISTRIERUNG ===")
                self.logger.warning("Bitte drücke JETZT den Knopf auf der Hue Bridge!")
                self.logger.warning("Du hast 30 Sekunden Zeit...")

                # Warte kurz und versuche es nochmal
                for i in range(3):
                    time.sleep(10)
                    try:
                        self.bridge = Bridge(self.bridge_ip)
                        self.bridge.connect()
                        self._refresh_device_map()
                        self.connected = True
                        self.logger.info("Erfolgreich mit Hue Bridge verbunden!")
                        return True
                    except Exception:
                        self.logger.info(f"Versuch {i+1}/3 fehlgeschlagen, warte weitere 10 Sekunden...")

            self.logger.error(f"Fehler bei Hue-Verbindung: {e}")
            self.connected = False
            return False

    def _refresh_device_map(self) -> None:
        """Aktualisiert die Geräteliste"""
        if not self.bridge:
            return

        try:
            lights = self.bridge.lights
            self.device_map.clear()

            for light in lights:
                self.device_map[light.name] = light
                self.logger.debug(f"Gefunden: {light.name} (An: {light.on})")

            self.logger.info(f"{len(self.device_map)} Geräte in Hue gefunden")

        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Geräte: {e}")

    def switch_on(self, device_name: str) -> bool:
        """
        Schaltet ein Gerät ein.

        Args:
            device_name: Name des Geräts (muss exakt dem Hue-Namen entsprechen)

        Returns:
            True bei Erfolg
        """
        if not self.connected:
            self.logger.warning("Keine Verbindung zur Hue Bridge")
            return False

        try:
            self.logger.info(f"Schalte '{device_name}' EIN (Hue)")
            self.bridge.set_light(device_name, 'on', True)
            return True

        except Exception as e:
            self.logger.error(f"Fehler beim Einschalten von '{device_name}': {e}")
            return False

    def switch_off(self, device_name: str) -> bool:
        """
        Schaltet ein Gerät aus.

        Args:
            device_name: Name des Geräts

        Returns:
            True bei Erfolg
        """
        if not self.connected:
            self.logger.warning("Keine Verbindung zur Hue Bridge")
            return False

        try:
            self.logger.info(f"Schalte '{device_name}' AUS (Hue)")
            self.bridge.set_light(device_name, 'on', False)
            return True

        except Exception as e:
            self.logger.error(f"Fehler beim Ausschalten von '{device_name}': {e}")
            return False

    def get_state(self, device_name: str) -> Optional[bool]:
        """
        Holt den aktuellen Status eines Geräts.

        Args:
            device_name: Name des Geräts

        Returns:
            True wenn an, False wenn aus, None bei Fehler
        """
        if not self.connected:
            return None

        try:
            light = self.bridge.get_light(device_name)
            return light['state']['on']

        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen des Status von '{device_name}': {e}")
            return None

    def list_devices(self) -> List[str]:
        """
        Listet alle verfügbaren Geräte auf.

        Returns:
            Liste der Gerätenamen
        """
        if not self.connected:
            return []

        self._refresh_device_map()
        return list(self.device_map.keys())