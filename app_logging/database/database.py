"""
SQLite Datenbank-Integration für den Smart Energy Manager.
"""

import sqlite3
import logging
from pathlib import Path
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from solar_monitor.models import SolarData
from solar_monitor.daily_stats import DailyStats
from device_management import Device, DeviceState


class DatabaseManager:
    """Datenbank-Manager für SQLite"""
    
    def __init__(self, db_path: str = "Datalogs/solar_energy.db"):
        """
        Initialisiert den Datenbank-Manager.
        
        Args:
            config: Konfigurationsobjekt
            db_path: Pfad zur SQLite-Datenbank
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # Datenbank initialisieren
        self._init_database()
        
    def _init_database(self):
        """Erstellt die Tabellen falls sie nicht existieren"""
        with self.get_connection() as conn:
            # Solar-Daten Tabelle
            conn.execute("""
                CREATE TABLE IF NOT EXISTS solar_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    pv_power REAL NOT NULL,
                    grid_power REAL NOT NULL,
                    battery_power REAL DEFAULT 0,
                    load_power REAL NOT NULL,
                    battery_soc REAL,
                    feed_in_power REAL NOT NULL,
                    grid_consumption REAL NOT NULL,
                    self_consumption REAL NOT NULL,
                    autarky_rate REAL NOT NULL,
                    surplus_power REAL NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Index für schnellere Zeitabfragen
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_solar_timestamp 
                ON solar_data(timestamp)
            """)
            
            # Tagesstatistiken Tabelle
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL UNIQUE,
                    runtime_hours REAL NOT NULL,
                    pv_energy REAL NOT NULL,
                    consumption_energy REAL NOT NULL,
                    self_consumption_energy REAL NOT NULL,
                    feed_in_energy REAL NOT NULL,
                    grid_energy REAL NOT NULL,
                    battery_charge_energy REAL DEFAULT 0,
                    battery_discharge_energy REAL DEFAULT 0,
                    pv_power_max REAL NOT NULL,
                    consumption_power_max REAL NOT NULL,
                    feed_in_power_max REAL NOT NULL,
                    grid_power_max REAL NOT NULL,
                    surplus_power_max REAL NOT NULL,
                    battery_soc_min REAL,
                    battery_soc_max REAL,
                    autarky_avg REAL NOT NULL,
                    self_sufficiency_rate REAL NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Geräte-Events Tabelle
            conn.execute("""
                CREATE TABLE IF NOT EXISTS device_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    device_name TEXT NOT NULL,
                    action TEXT NOT NULL,
                    old_state TEXT,
                    new_state TEXT NOT NULL,
                    reason TEXT,
                    surplus_power REAL,
                    device_power REAL NOT NULL,
                    priority INTEGER NOT NULL,
                    runtime_today INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Index für Geräte-Abfragen
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_device_events 
                ON device_events(device_name, timestamp)
            """)
            
            # Geräte-Status Tabelle (für regelmäßige Snapshots)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS device_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    device_name TEXT NOT NULL,
                    state TEXT NOT NULL,
                    runtime_today INTEGER NOT NULL,
                    power_consumption REAL NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self.logger.info(f"Datenbank initialisiert: {self.db_path}")
    
    @contextmanager
    def get_connection(self):
        """Context Manager für Datenbankverbindungen"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Ermöglicht Zugriff über Spaltennamen
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Datenbankfehler: {e}")
            raise
        finally:
            conn.close()
    
    def insert_solar_data(self, data: SolarData) -> bool:
        """
        Fügt Solar-Daten in die Datenbank ein.
        
        Args:
            data: SolarData-Objekt
            
        Returns:
            True bei Erfolg
        """
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO solar_data (
                        timestamp, pv_power, grid_power, battery_power,
                        load_power, battery_soc, feed_in_power, grid_consumption,
                        self_consumption, autarky_rate, surplus_power
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data.timestamp, data.pv_power, data.grid_power,
                    data.battery_power, data.load_power, data.battery_soc,
                    data.feed_in_power, data.grid_consumption,
                    data.self_consumption, data.autarky_rate, data.surplus_power
                ))
            return True
        except Exception as e:
            self.logger.error(f"Fehler beim Einfügen von Solar-Daten: {e}")
            return False
    
    def get_solar_data_range(self, start_time: datetime, end_time: datetime) -> List[Dict]:
        """
        Holt Solar-Daten für einen Zeitbereich.
        
        Args:
            start_time: Startzeit
            end_time: Endzeit
            
        Returns:
            Liste von Datensätzen als Dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM solar_data 
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp
            """, (start_time, end_time))
            
            return [dict(row) for row in db.fetchall(query)]

    def insert_daily_stats(self, stats: DailyStats) -> bool:
        """
        Fügt Tagesstatistiken in die Datenbank ein.

        Args:
            stats: DailyStats-Objekt

        Returns:
            True bei Erfolg
        """
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO daily_stats (
                        date, runtime_hours, pv_energy, consumption_energy,
                        self_consumption_energy, feed_in_energy, grid_energy,
                        battery_charge_energy, battery_discharge_energy,
                        pv_power_max, consumption_power_max, feed_in_power_max,
                        grid_power_max, surplus_power_max, battery_soc_min,
                        battery_soc_max, autarky_avg, self_sufficiency_rate
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    stats.date, stats.runtime_hours, stats.pv_energy,
                    stats.consumption_energy, stats.self_consumption_energy,
                    stats.feed_in_energy, stats.grid_energy,
                    stats.battery_charge_energy, stats.battery_discharge_energy,
                    stats.pv_power_max, stats.consumption_power_max,
                    stats.feed_in_power_max, stats.grid_power_max,
                    stats.surplus_power_max, stats.battery_soc_min,
                    stats.battery_soc_max, stats.autarky_avg,
                    stats.self_sufficiency_rate
                ))
            return True
        except Exception as e:
            self.logger.error(f"Fehler beim Einfügen von Tagesstatistiken: {e}")
            return False

    def get_daily_stats(self, start_date: date, end_date: date) -> List[Dict]:
        """
        Holt Tagesstatistiken für einen Datumsbereich.

        Args:
            start_date: Startdatum
            end_date: Enddatum

        Returns:
            Liste von Tagesstatistiken
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM daily_stats 
                WHERE date BETWEEN ? AND ?
                ORDER BY date
            """, (start_date, end_date))

            return [dict(row) for row in db.fetchall(query)]

    def insert_device_event(self, device: Device, action: str, reason: str,
                          surplus_power: float, old_state: DeviceState) -> bool:
        """
        Fügt ein Geräte-Event in die Datenbank ein.

        Args:
            device: Device-Objekt
            action: Durchgeführte Aktion
            reason: Grund für die Aktion
            surplus_power: Aktueller Überschuss
            old_state: Vorheriger Status

        Returns:
            True bei Erfolg
        """
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO device_events (
                        timestamp, device_name, action, old_state, new_state,
                        reason, surplus_power, device_power, priority, runtime_today
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    datetime.now(), device.name, action, old_state.value,
                    device.state.value, reason, surplus_power,
                    device.power_consumption, device.priority.value,
                    device.runtime_today
                ))
            return True
        except Exception as e:
            self.logger.error(f"Fehler beim Einfügen von Geräte-Event: {e}")
            return False

    def insert_device_status_snapshot(self, devices: List[Device],
                                    surplus_power: float) -> bool:
        """
        Fügt einen Snapshot des aktuellen Gerätestatus ein.

        Args:
            devices: Liste von Geräten
            surplus_power: Aktueller Überschuss

        Returns:
            True bei Erfolg
        """
        try:
            timestamp = datetime.now()
            with self.get_connection() as conn:
                for device in devices:
                    conn.execute("""
                        INSERT INTO device_status (
                            timestamp, device_name, state, runtime_today, 
                            power_consumption
                        ) VALUES (?, ?, ?, ?, ?)
                    """, (
                        timestamp, device.name, device.state.value,
                        device.runtime_today, device.power_consumption
                    ))
            return True
        except Exception as e:
            self.logger.error(f"Fehler beim Einfügen von Gerätestatus: {e}")
            return False

    def get_device_events(self, device_name: Optional[str] = None,
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None) -> List[Dict]:
        """
        Holt Geräte-Events aus der Datenbank.

        Args:
            device_name: Optional - nur Events für dieses Gerät
            start_time: Optional - Startzeit
            end_time: Optional - Endzeit

        Returns:
            Liste von Events
        """
        query = "SELECT * FROM device_events WHERE 1=1"
        params = []

        if device_name:
            query += " AND device_name = ?"
            params.append(device_name)

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)

        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)

        query += " ORDER BY timestamp DESC"

        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in db.fetchall(query)]

    def get_energy_summary(self, date: date) -> Dict:
        """
        Holt eine Energiezusammenfassung für einen Tag.

        Args:
            date: Datum

        Returns:
            Dictionary mit Energiewerten
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as data_points,
                    SUM(pv_power) * 5.0 / 3600000 as pv_energy_kwh,
                    SUM(load_power) * 5.0 / 3600000 as consumption_kwh,
                    SUM(feed_in_power) * 5.0 / 3600000 as feed_in_kwh,
                    SUM(grid_consumption) * 5.0 / 3600000 as grid_kwh,
                    AVG(autarky_rate) as avg_autarky,
                    MAX(pv_power) as max_pv_power,
                    MAX(surplus_power) as max_surplus
                FROM solar_data
                WHERE date(timestamp) = ?
            """, (date,))

            row = db.fetchone(query)
            return dict(row) if row else {}

    def get_device_runtime_summary(self, date: date) -> List[Dict]:
        """
        Holt eine Zusammenfassung der Gerätelaufzeiten für einen Tag.

        Args:
            date: Datum

        Returns:
            Liste mit Gerätelaufzeiten
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    device_name,
                    COUNT(CASE WHEN new_state = 'on' THEN 1 END) as switch_on_count,
                    COUNT(CASE WHEN new_state = 'off' THEN 1 END) as switch_off_count,
                    MAX(runtime_today) as max_runtime_minutes,
                    AVG(device_power) as avg_power
                FROM device_events
                WHERE date(timestamp) = ?
                GROUP BY device_name
                ORDER BY max_runtime_minutes DESC
            """, (date,))

            return [dict(row) for row in db.fetchall(query)]
