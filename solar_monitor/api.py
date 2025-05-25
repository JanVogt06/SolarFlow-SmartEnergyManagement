"""
Fronius API-Kommunikationsmodul.
"""

import json
import logging
from typing import Dict, Optional, Any

import requests

from .models import SolarData


class FroniusAPI:
    """Klasse für die Kommunikation mit der Fronius Solar API"""

    def __init__(self, ip_address: str, timeout: int = 5):
        """
        Initialisiert die API-Verbindung.

        Args:
            ip_address: IP-Adresse des Fronius Wechselrichters
            timeout: Timeout für HTTP-Requests in Sekunden
        """
        self.ip_address = ip_address
        self.timeout = timeout
        self.base_url = f"http://{ip_address}"
        self.logger = logging.getLogger(__name__)

        # API-Endpunkte
        self.endpoints = {
            'power_flow': '/solar_api/v1/GetPowerFlowRealtimeData.fcgi',
            'inverter_info': '/solar_api/v1/GetInverterInfo.cgi',
            'meter_data': '/solar_api/v1/GetMeterRealtimeData.cgi',
            'storage_data': '/solar_api/v1/GetStorageRealtimeData.cgi'
        }

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
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
        data = self._make_request(self.endpoints['power_flow'])

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

    def _extract_battery_soc(self, data: Dict) -> Optional[float]:
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
        data = self._make_request(self.endpoints['power_flow'])
        return data is not None

    def get_inverter_info(self) -> Optional[Dict]:
        """
        Holt Informationen über den Wechselrichter.

        Returns:
            Dictionary mit Inverter-Infos oder None
        """
        return self._make_request(self.endpoints['inverter_info'])

    def get_api_version(self) -> Optional[str]:
        """
        Versucht die API-Version zu ermitteln.

        Returns:
            API-Version als String oder None
        """
        # Verschiedene mögliche Endpunkte für API-Version
        version_endpoints = [
            '/solar_api/GetAPIVersion.json',
            '/solar_api/v1/GetAPIVersion.json'
        ]

        for endpoint in version_endpoints:
            data = self._make_request(endpoint)
            if data and 'APIVersion' in data:
                return data['APIVersion']

        return None