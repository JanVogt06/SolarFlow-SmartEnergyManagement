"""
Abstrakte Interfaces für Smart Device Integrationen.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import logging


class ISmartDeviceInterface(ABC):
    """Abstraktes Interface für Smart Device Integrationen"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialisiert das Device Interface.

        Args:
            config: Konfiguration für das spezifische Interface
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self._connected = False

    @abstractmethod
    def connect(self) -> bool:
        """
        Stellt Verbindung zum Device-System her.

        Returns:
            True bei erfolgreicher Verbindung
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Trennt die Verbindung zum Device-System."""
        pass

    @abstractmethod
    def switch_on(self, device_name: str) -> bool:
        """
        Schaltet ein Gerät ein.

        Args:
            device_name: Name des Geräts

        Returns:
            True bei Erfolg
        """
        pass

    @abstractmethod
    def switch_off(self, device_name: str) -> bool:
        """
        Schaltet ein Gerät aus.

        Args:
            device_name: Name des Geräts

        Returns:
            True bei Erfolg
        """
        pass

    @abstractmethod
    def get_state(self, device_name: str) -> Optional[bool]:
        """
        Holt den aktuellen Status eines Geräts.

        Args:
            device_name: Name des Geräts

        Returns:
            True wenn an, False wenn aus, None bei Fehler
        """
        pass

    @abstractmethod
    def list_devices(self) -> List[str]:
        """
        Listet alle verfügbaren Geräte auf.

        Returns:
            Liste der Gerätenamen
        """
        pass

    @abstractmethod
    def is_device_available(self, device_name: str) -> bool:
        """
        Prüft ob ein Gerät verfügbar ist.

        Args:
            device_name: Name des Geräts

        Returns:
            True wenn Gerät verfügbar
        """
        pass

    @property
    def connected(self) -> bool:
        """Gibt zurück ob Interface verbunden ist."""
        return self._connected

    @property
    @abstractmethod
    def interface_type(self) -> str:
        """Gibt den Typ des Interfaces zurück (z.B. 'hue', 'shelly')."""
        pass


class NullDeviceInterface(ISmartDeviceInterface):
    """Null-Object Pattern für deaktivierte Hardware-Steuerung"""

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config or {})
        self.logger.info("NullDeviceInterface aktiviert - keine Hardware-Steuerung")

    def connect(self) -> bool:
        self._connected = True
        return True

    def disconnect(self) -> None:
        self._connected = False

    def switch_on(self, device_name: str) -> bool:
        self.logger.debug(f"Virtuell: Gerät '{device_name}' eingeschaltet")
        return True

    def switch_off(self, device_name: str) -> bool:
        self.logger.debug(f"Virtuell: Gerät '{device_name}' ausgeschaltet")
        return True

    def get_state(self, device_name: str) -> Optional[bool]:
        return None

    def list_devices(self) -> List[str]:
        return []

    def is_device_available(self, device_name: str) -> bool:
        return True  # Alle Geräte sind "virtuell verfügbar"

    @property
    def interface_type(self) -> str:
        return "null"