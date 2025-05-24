#!/usr/bin/env python3
"""
Fronius Solar Monitor - Objektorientierte Version
Ein modulares System zur Überwachung von Fronius Solaranlagen.
"""

import requests
import json
import time
import logging
from datetime import datetime
from typing import Dict, Optional, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum


# Konfiguration
class Config:
    """Zentrale Konfigurationsklasse"""
    FRONIUS_IP = "192.168.178.90"
    UPDATE_INTERVAL = 5  # Sekunden
    REQUEST_TIMEOUT = 5  # Sekunden
    LOG_LEVEL = logging.INFO
    

# Datenmodelle
@dataclass
class SolarData:
    """Datenklasse für Solardaten"""
    pv_power: float = 0.0          # Watt
    grid_power: float = 0.0        # Watt (negativ = Einspeisung)
    battery_power: float = 0.0     # Watt (negativ = Laden)
    load_power: float = 0.0        # Watt
    battery_soc: Optional[float] = None  # Prozent
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    @property
    def is_feeding_in(self) -> bool:
        """Prüft ob ins Netz eingespeist wird"""
        return self.grid_power < 0
    
    @property
    def feed_in_power(self) -> float:
        """Gibt die Einspeiseleistung zurück (positiv)"""
        return abs(self.grid_power) if self.is_feeding_in else 0
    
    @property
    def grid_consumption(self) -> float:
        """Gibt den Netzbezug zurück (positiv)"""
        return self.grid_power if self.grid_power > 0 else 0
    
    @property
    def battery_charging(self) -> bool:
        """Prüft ob die Batterie lädt"""
        return self.battery_power < 0
    
    @property
    def battery_charge_power(self) -> float:
        """Gibt die Ladeleistung zurück (positiv)"""
        return abs(self.battery_power) if self.battery_charging else 0
    
    @property
    def battery_discharge_power(self) -> float:
        """Gibt die Entladeleistung zurück (positiv)"""
        return self.battery_power if self.battery_power > 0 else 0
    
    @property
    def self_consumption(self) -> float:
        """Berechnet den Eigenverbrauch"""
        return self.load_power - self.grid_consumption
    
    @property
    def autarky_rate(self) -> float:
        """Berechnet den Autarkiegrad in Prozent"""
        if self.load_power > 0:
            return (self.self_consumption / self.load_power) * 100
        return 0.0


# API-Schnittstelle
class FroniusAPI:
    """Klasse für die Kommunikation mit der Fronius Solar API"""
    
    def __init__(self, ip_address: str, timeout: int = 5):
        self.ip_address = ip_address
        self.timeout = timeout
        self.base_url = f"http://{ip_address}"
        self.logger = logging.getLogger(__name__)
        
    def _make_request(self, endpoint: str) -> Optional[Dict[str, Any]]:
        """Führt einen HTTP-Request aus und gibt JSON zurück"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API-Fehler: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON-Dekodierungsfehler: {e}")
            return None
    
    def get_power_flow_data(self) -> Optional[SolarData]:
        """Holt die aktuellen Leistungsdaten"""
        data = self._make_request("/solar_api/v1/GetPowerFlowRealtimeData.fcgi")
        
        if not data or 'Body' not in data or 'Data' not in data['Body']:
            return None
        
        try:
            site_data = data['Body']['Data']['Site']
            
            # Extrahiere Werte mit Null-Behandlung
            pv_power = site_data.get('P_PV', 0) or 0
            grid_power = site_data.get('P_Grid', 0) or 0
            battery_power = site_data.get('P_Akku', 0) or 0
            load_power = abs(site_data.get('P_Load', 0) or 0)
            
            # Batterie-SOC aus Inverter-Daten
            battery_soc = None
            if 'Inverters' in data['Body']['Data']:
                for inverter in data['Body']['Data']['Inverters'].values():
                    if 'SOC' in inverter:
                        battery_soc = inverter['SOC']
                        break
            
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
    
    def test_connection(self) -> bool:
        """Testet die Verbindung zur API"""
        # Teste mit dem funktionierenden PowerFlow-Endpunkt
        data = self._make_request("/solar_api/v1/GetPowerFlowRealtimeData.fcgi")
        return data is not None


# Ausgabe-Formatierung
class DisplayFormatter:
    """Klasse für die Formatierung der Anzeige"""
    
    @staticmethod
    def format_power(value: float, unit: str = "W") -> str:
        """Formatiert Leistungswerte"""
        return f"{value:>8.0f} {unit}"
    
    @staticmethod
    def format_percentage(value: float) -> str:
        """Formatiert Prozentwerte"""
        return f"{value:>8.0f} %"
    
    def display_data(self, data: SolarData) -> None:
        """Zeigt die Daten formatiert an"""
        print("\n" + "="*50)
        print(f"🕐 {data.timestamp.strftime('%H:%M:%S')}")
        print("="*50)
        
        # PV-Erzeugung
        print(f"☀️  PV-Erzeugung:     {self.format_power(data.pv_power)}")
        
        # Hausverbrauch
        print(f"🏠 Hausverbrauch:    {self.format_power(data.load_power)}")
        
        # Netz
        if data.is_feeding_in:
            print(f"⚡ Einspeisung:      {self.format_power(data.feed_in_power)}")
        elif data.grid_consumption > 0:
            print(f"🔌 Netzbezug:        {self.format_power(data.grid_consumption)}")
        else:
            print(f"🔌 Netz:             {self.format_power(0)}")
        
        # Batterie
        if data.battery_power != 0 or data.battery_soc is not None:
            if data.battery_charging:
                print(f"🔋 Batterie lädt:    {self.format_power(data.battery_charge_power)}")
            elif data.battery_discharge_power > 0:
                print(f"🔋 Batterie entlädt: {self.format_power(data.battery_discharge_power)}")
            
            if data.battery_soc is not None:
                print(f"🔋 Batterie-Stand:   {self.format_percentage(data.battery_soc)}")
        
        # Autarkie
        print(f"\n📊 Autarkie:         {self.format_percentage(data.autarky_rate)}")


# Daten-Logger
class DataLogger:
    """Optional: Klasse zum Logging der Daten"""
    
    def __init__(self, filename: str = "solar_data.csv"):
        self.filename = filename
        self.logger = logging.getLogger(__name__)
        self._ensure_header()
    
    def _ensure_header(self):
        """Stellt sicher, dass die CSV-Header existieren"""
        try:
            with open(self.filename, 'x') as f:
                f.write("timestamp,pv_power,grid_power,battery_power,load_power,battery_soc,autarky_rate\n")
        except FileExistsError:
            pass
    
    def log_data(self, data: SolarData):
        """Schreibt Daten in die CSV-Datei"""
        try:
            with open(self.filename, 'a') as f:
                f.write(f"{data.timestamp.isoformat()},"
                       f"{data.pv_power},"
                       f"{data.grid_power},"
                       f"{data.battery_power},"
                       f"{data.load_power},"
                       f"{data.battery_soc or ''},"
                       f"{data.autarky_rate}\n")
        except IOError as e:
            self.logger.error(f"Fehler beim Schreiben der Log-Datei: {e}")


# Hauptanwendung
class SolarMonitor:
    """Hauptklasse für den Solar Monitor"""
    
    def __init__(self, config: Config):
        self.config = config
        self.api = FroniusAPI(config.FRONIUS_IP, config.REQUEST_TIMEOUT)
        self.display = DisplayFormatter()
        self.logger = logging.getLogger(__name__)
        self.data_logger = DataLogger("solar_data.csv")  # Aktiviert!
        self.running = False
        
    def setup_logging(self):
        """Konfiguriert das Logging"""
        # Erstelle Logger
        logger = logging.getLogger()
        logger.setLevel(self.config.LOG_LEVEL)
        
        # Formatter für beide Handler
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File Handler
        file_handler = logging.FileHandler('solar_monitor.log')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Verhindere doppelte Logs
        logger.propagate = False
    
    def start(self):
        """Startet den Monitor"""
        self.setup_logging()
        self.logger.info("Fronius Solar Monitor gestartet")
        self.logger.info(f"Verbinde mit Wechselrichter auf {self.config.FRONIUS_IP}...")
        
        # Teste Verbindung
        if not self.api.test_connection():
            self.logger.warning("API-Verbindungstest fehlgeschlagen, versuche trotzdem fortzufahren...")
        
        self.running = True
        self.run()
    
    def stop(self):
        """Stoppt den Monitor"""
        self.running = False
        self.logger.info("Monitor wird beendet...")
    
    def run(self):
        """Hauptschleife"""
        try:
            while self.running:
                # Hole Daten
                data = self.api.get_power_flow_data()
                
                if data:
                    # Zeige Daten an
                    self.display.display_data(data)
                    
                    # Optional: Logge Daten
                    if self.data_logger:
                        self.data_logger.log_data(data)
                else:
                    self.logger.warning("Keine Daten empfangen")
                
                # Warte bis zum nächsten Update
                time.sleep(self.config.UPDATE_INTERVAL)
                
        except KeyboardInterrupt:
            self.stop()
            print("\n\nProgramm beendet.")


# Einstiegspunkt
def main():
    """Hauptfunktion"""
    config = Config()
    monitor = SolarMonitor(config)
    monitor.start()


if __name__ == "__main__":
    main()