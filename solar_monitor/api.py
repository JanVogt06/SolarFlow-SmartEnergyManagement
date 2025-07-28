"""
Fronius API-Kommunikationsmodul.
"""

import json
import log_system
from typing import Dict, Optional, Any, Union

import requests

from .models import SolarData


class FroniusAPI:
    """Klasse für die Kommunikation mit der Fronius Solar API"""

    def __init__(self, ip_address: str, timeout: int = 5) -> None:
        """
        Initialisiert die API-Verbindung.

        Args:
            ip_address: IP-Adresse des Fronius Wechselrichters
            timeout: Timeout für HTTP-Requests in Sekunden
        """
        self.ip_address: str = ip_address
        self.timeout: int = timeout
        self.base_url: str = f"http://{ip_address}"
        self.logger = log_system.getLogger(__name__)

        # API-Endpunkt für Leistungsdaten
        self.power_flow_endpoint: str = '/solar_api/v1/GetPowerFlowRealtimeData.fcgi'

    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Führt einen HTTP-Request aus und gibt JSON zurück.

        Args:
            endpoint: API-Endpunkt
            params: Optionale Query-Parameter

        Returns:
            JSON-Response oder None bei Fehler
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            self.logger.error(f"API-Fehler: {e}")
            return None
        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout bei Anfrage an {url}")
            return None
        except requests.exceptions.ConnectionError:
            self.logger.error(f"Verbindungsfehler zu {self.ip_address}")
            return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API-Fehler: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON-Dekodierungsfehler: {e}")
            return None

    def get_power_flow_data(self) -> Optional[SolarData]:
        """
        Holt die aktuellen Leistungsdaten vom Wechselrichter.

        Returns:
            SolarData-Objekt oder None bei Fehler
        """
        data = self._make_request(self.power_flow_endpoint)

        if not data:
            return None

        # Validiere Response-Struktur
        if 'Body' not in data or 'Data' not in data['Body']:
            self.logger.error("Ungültige API-Response-Struktur")
            return None

        try:
            site_data = data['Body']['Data']['Site']

            # Extrahiere Werte mit Null-Behandlung
            pv_power = self._safe_float(site_data.get('P_PV'))
            grid_power = self._safe_float(site_data.get('P_Grid'))
            battery_power = self._safe_float(site_data.get('P_Akku'))
            load_power = abs(self._safe_float(site_data.get('P_Load')))

            # Batterie-SOC aus Inverter-Daten
            battery_soc = self._extract_battery_soc(data['Body']['Data'])

            return SolarData(
                pv_power=pv_power,
                grid_power=grid_power,
                battery_power=battery_power,
                load_power=load_power,
                battery_soc=battery_soc
            )

        except (KeyError, TypeError) as e:
            self.logger.error(f"Fehler beim Parsen der Daten: {e}")
            return None

    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        """
        Konvertiert einen Wert sicher in float.

        Args:
            value: Zu konvertierender Wert
            default: Standardwert bei Fehler

        Returns:
            Float-Wert
        """
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def _extract_battery_soc(self, data: Dict[str, Any]) -> Optional[float]:
        """
        Extrahiert den Batterie-Ladestand aus den Daten.

        Args:
            data: API-Response-Daten

        Returns:
            Batterie-SOC in Prozent oder None
        """
        # Versuche SOC aus Inverter-Daten zu extrahieren
        if 'Inverters' in data:
            for inverter in data['Inverters'].values():
                if 'SOC' in inverter:
                    return self._safe_float(inverter['SOC'])

        # Alternative: Versuche aus Storage-Daten
        if 'Storage' in data:
            for storage in data['Storage'].values():
                if 'StateOfCharge_Relative' in storage:
                    return self._safe_float(storage['StateOfCharge_Relative'])

        return None

    def test_connection(self) -> bool:
        """
        Testet die Verbindung zur API.

        Returns:
            True wenn Verbindung erfolgreich, sonst False
        """
        data = self._make_request(self.power_flow_endpoint)
        return data is not None