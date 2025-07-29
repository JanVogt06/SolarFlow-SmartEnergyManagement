"""
Database Writer für das Logging-System.
"""

import sqlite3
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from .base_writer import BaseWriter


class DatabaseWriter(BaseWriter):
    """Writer für SQLite-Datenbank"""

    def __init__(self, config: Any):
        """
        Initialisiert den Database Writer.

        Args:
            config: Konfigurationsobjekt
        """
        super().__init__(config)
        self.db_path = Path(config.database.database_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Größerer Buffer für Datenbank
        self._buffer_size = 100

        # Initialisiere Datenbank
        self._init_database()

    def _init_database(self) -> None:
        """Erstellt die Tabellen falls sie nicht existieren"""
        try:
            with self._get_connection() as conn:
                # Solar-Daten Tabelle
                conn.execute("""
                             CREATE TABLE IF NOT EXISTS solar_data
                             (
                                 id               INTEGER PRIMARY KEY AUTOINCREMENT,
                                 timestamp        DATETIME NOT NULL,
                                 pv_power         REAL     NOT NULL,
                                 grid_power       REAL     NOT NULL,
                                 battery_power    REAL     DEFAULT 0,
                                 load_power       REAL     NOT NULL,
                                 battery_soc      REAL,
                                 feed_in_power    REAL     NOT NULL,
                                 grid_consumption REAL     NOT NULL,
                                 self_consumption REAL     NOT NULL,
                                 autarky_rate     REAL     NOT NULL,
                                 surplus_power    REAL     NOT NULL,
                                 created_at       DATETIME DEFAULT CURRENT_TIMESTAMP
                             )
                             """)

                # Index für Zeitabfragen
                conn.execute("""
                             CREATE INDEX IF NOT EXISTS idx_solar_timestamp
                                 ON solar_data (timestamp)
                             """)

                # Tagesstatistiken Tabelle
                conn.execute("""
                             CREATE TABLE IF NOT EXISTS daily_stats
                             (
                                 id                       INTEGER PRIMARY KEY AUTOINCREMENT,
                                 date                     DATE NOT NULL UNIQUE,
                                 runtime_hours            REAL NOT NULL,
                                 pv_energy                REAL NOT NULL,
                                 consumption_energy       REAL NOT NULL,
                                 self_consumption_energy  REAL NOT NULL,
                                 feed_in_energy           REAL NOT NULL,
                                 grid_energy              REAL NOT NULL,
                                 grid_energy_day          REAL     DEFAULT 0,
                                 grid_energy_night        REAL     DEFAULT 0,
                                 battery_charge_energy    REAL     DEFAULT 0,
                                 battery_discharge_energy REAL     DEFAULT 0,
                                 pv_power_max             REAL NOT NULL,
                                 consumption_power_max    REAL NOT NULL,
                                 feed_in_power_max        REAL NOT NULL,
                                 grid_power_max           REAL NOT NULL,
                                 surplus_power_max        REAL NOT NULL,
                                 battery_soc_min          REAL,
                                 battery_soc_max          REAL,
                                 autarky_avg              REAL NOT NULL,
                                 self_sufficiency_rate    REAL NOT NULL,
                                 cost_grid_consumption    REAL     DEFAULT 0,
                                 revenue_feed_in          REAL     DEFAULT 0,
                                 cost_saved               REAL     DEFAULT 0,
                                 total_benefit            REAL     DEFAULT 0,
                                 cost_without_solar       REAL     DEFAULT 0,
                                 created_at               DATETIME DEFAULT CURRENT_TIMESTAMP
                             )
                             """)

                # Geräte-Events Tabelle
                conn.execute("""
                             CREATE TABLE IF NOT EXISTS device_events
                             (
                                 id            INTEGER PRIMARY KEY AUTOINCREMENT,
                                 timestamp     DATETIME NOT NULL,
                                 device_name   TEXT     NOT NULL,
                                 action        TEXT     NOT NULL,
                                 old_state     TEXT,
                                 new_state     TEXT     NOT NULL,
                                 reason        TEXT,
                                 surplus_power REAL,
                                 device_power  REAL     NOT NULL,
                                 priority      INTEGER  NOT NULL,
                                 runtime_today INTEGER,
                                 created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
                             )
                             """)

                # Geräte-Status Tabelle
                conn.execute("""
                             CREATE TABLE IF NOT EXISTS device_status
                             (
                                 id                INTEGER PRIMARY KEY AUTOINCREMENT,
                                 timestamp         DATETIME NOT NULL,
                                 total_devices_on  INTEGER  NOT NULL DEFAULT 0,
                                 total_consumption REAL     NOT NULL DEFAULT 0,
                                 surplus_power     REAL     NOT NULL DEFAULT 0,
                                 used_surplus      REAL     NOT NULL DEFAULT 0,
                                 device_states     TEXT, -- JSON mit Gerätezuständen
                                 created_at        DATETIME          DEFAULT CURRENT_TIMESTAMP
                             )
                             """)

                # Index für Zeitabfragen
                conn.execute("""
                             CREATE INDEX IF NOT EXISTS idx_device_status_timestamp
                                 ON device_status (timestamp)
                             """)

                conn.commit()
                self.logger.info(f"Datenbank initialisiert: {self.db_path}")

        except Exception as e:
            self.logger.error(f"Fehler bei Datenbank-Initialisierung: {e}")

    def _get_connection(self) -> sqlite3.Connection:
        """Erstellt eine Datenbankverbindung"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def flush(self) -> bool:
        """
        Schreibt Buffer in Datenbank.

        Returns:
            True bei Erfolg
        """
        if not self._buffer:
            return True

        # Gruppiere nach log_type
        grouped = {}
        for entry in self._buffer:
            log_type = entry['metadata'].get('log_type')
            if log_type not in grouped:
                grouped[log_type] = []
            grouped[log_type].append(entry['data'])

        # Schreibe jede Gruppe
        success = True
        try:
            with self._get_connection() as conn:
                for log_type, data_list in grouped.items():
                    if not self._write_batch(conn, log_type, data_list):
                        success = False

                if success:
                    conn.commit()
                else:
                    conn.rollback()

        except Exception as e:
            self.logger.error(f"Fehler beim Datenbank-Flush: {e}")
            success = False

        # Buffer leeren
        self._buffer.clear()
        return success

    def _write_batch(self, conn: sqlite3.Connection, log_type: str,
                     data_list: List[Dict[str, Any]]) -> bool:
        """
        Schreibt einen Batch von Daten.

        Args:
            conn: Datenbankverbindung
            log_type: Typ des Logs
            data_list: Liste von Daten

        Returns:
            True bei Erfolg
        """
        try:
            if log_type == 'solar':
                return self._write_solar_batch(conn, data_list)
            elif log_type == 'stats':
                return self._write_stats_batch(conn, data_list)
            elif log_type == 'device_event':
                return self._write_device_event_batch(conn, data_list)
            elif log_type == 'device_status':  # NEU
                return self._write_device_status_batch(conn, data_list)
            else:
                self.logger.warning(f"Unbekannter log_type für Datenbank: {log_type}")
                return True  # Kein Fehler, nur nicht unterstützt

        except Exception as e:
            self.logger.error(f"Fehler beim Schreiben von {log_type}: {e}")
            return False

    def _write_solar_batch(self, conn: sqlite3.Connection,
                           data_list: List[Dict[str, Any]]) -> bool:
        """Schreibt Solar-Daten"""
        sql = """
              INSERT INTO solar_data (timestamp, pv_power, grid_power, battery_power, \
                                      load_power, battery_soc, feed_in_power, grid_consumption, \
                                      self_consumption, autarky_rate, surplus_power) \
              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) \
              """

        # Konvertiere Daten
        values = []
        for data in data_list:
            values.append((
                self._parse_timestamp(data.get('timestamp')),
                self._parse_number(data.get('pv_power')),
                self._parse_number(data.get('grid_power')),
                self._parse_number(data.get('battery_power')),
                self._parse_number(data.get('load_power')),
                self._parse_number(data.get('battery_soc')),
                self._parse_number(data.get('feed_in_power')),
                self._parse_number(data.get('grid_consumption')),
                self._parse_number(data.get('self_consumption')),
                self._parse_number(data.get('autarky_rate')),
                self._parse_number(data.get('surplus_power'))
            ))

        conn.executemany(sql, values)
        return True

    def _write_stats_batch(self, conn: sqlite3.Connection,
                           data_list: List[Dict[str, Any]]) -> bool:
        """Schreibt Tagesstatistiken (akkumulierend)"""

        for data in data_list:
            date_str = data.get('date')

            # Prüfe ob Eintrag für dieses Datum bereits existiert
            existing = conn.execute(
                "SELECT * FROM daily_stats WHERE date = ?", (date_str,)
            ).fetchone()

            if existing:
                # UPDATE: Addiere Energiewerte, aktualisiere Max-Werte
                sql = """
                      UPDATE daily_stats \
                      SET runtime_hours            = runtime_hours + ?, \
                          pv_energy                = pv_energy + ?, \
                          consumption_energy       = consumption_energy + ?, \
                          self_consumption_energy  = self_consumption_energy + ?, \
                          feed_in_energy           = feed_in_energy + ?, \
                          grid_energy              = grid_energy + ?, \
                          grid_energy_day          = grid_energy_day + ?, \
                          grid_energy_night        = grid_energy_night + ?, \
                          battery_charge_energy    = battery_charge_energy + ?, \
                          battery_discharge_energy = battery_discharge_energy + ?, \
                          pv_power_max             = MAX(pv_power_max, ?), \
                          consumption_power_max    = MAX(consumption_power_max, ?), \
                          feed_in_power_max        = MAX(feed_in_power_max, ?), \
                          grid_power_max           = MAX(grid_power_max, ?), \
                          surplus_power_max        = MAX(surplus_power_max, ?), \
                          battery_soc_min          = MIN(COALESCE(battery_soc_min, ?), ?), \
                          battery_soc_max          = MAX(COALESCE(battery_soc_max, ?), ?), \
                          autarky_avg              = ?, \
                          self_sufficiency_rate    = ?, \
                          cost_grid_consumption    = cost_grid_consumption + ?, \
                          revenue_feed_in          = revenue_feed_in + ?, \
                          cost_saved               = cost_saved + ?, \
                          total_benefit            = total_benefit + ?, \
                          cost_without_solar       = cost_without_solar + ?
                      WHERE date = ?
                      """

                values = (
                    self._parse_number(data.get('runtime_hours')),
                    self._parse_number(data.get('pv_energy')),
                    self._parse_number(data.get('consumption_energy')),
                    self._parse_number(data.get('self_consumption_energy')),
                    self._parse_number(data.get('feed_in_energy')),
                    self._parse_number(data.get('grid_energy')),
                    self._parse_number(data.get('grid_energy_day')),
                    self._parse_number(data.get('grid_energy_night')),
                    self._parse_number(data.get('battery_charge_energy')),
                    self._parse_number(data.get('battery_discharge_energy')),
                    self._parse_number(data.get('pv_power_max')),
                    self._parse_number(data.get('consumption_power_max')),
                    self._parse_number(data.get('feed_in_power_max')),
                    self._parse_number(data.get('grid_power_max')),
                    self._parse_number(data.get('surplus_power_max')),
                    self._parse_number(data.get('battery_soc_min')),
                    self._parse_number(data.get('battery_soc_min')),
                    self._parse_number(data.get('battery_soc_max')),
                    self._parse_number(data.get('battery_soc_max')),
                    self._parse_number(data.get('autarky_avg')),
                    self._parse_number(data.get('self_sufficiency_rate')),
                    self._parse_number(data.get('cost_grid_consumption')),
                    self._parse_number(data.get('revenue_feed_in')),
                    self._parse_number(data.get('cost_saved')),
                    self._parse_number(data.get('total_benefit')),
                    self._parse_number(data.get('cost_without_solar')),
                    date_str
                )

                conn.execute(sql, values)

            else:
                # INSERT: Neuer Eintrag
                sql = """
                      INSERT INTO daily_stats (date, runtime_hours, pv_energy, consumption_energy, \
                                               self_consumption_energy, feed_in_energy, grid_energy, \
                                               grid_energy_day, grid_energy_night, \
                                               battery_charge_energy, battery_discharge_energy, \
                                               pv_power_max, consumption_power_max, feed_in_power_max, \
                                               grid_power_max, surplus_power_max, battery_soc_min, \
                                               battery_soc_max, autarky_avg, self_sufficiency_rate, \
                                               cost_grid_consumption, revenue_feed_in, cost_saved, \
                                               total_benefit, cost_without_solar) \
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                      """

                values = (
                    date_str,
                    self._parse_number(data.get('runtime_hours')),
                    self._parse_number(data.get('pv_energy')),
                    self._parse_number(data.get('consumption_energy')),
                    self._parse_number(data.get('self_consumption_energy')),
                    self._parse_number(data.get('feed_in_energy')),
                    self._parse_number(data.get('grid_energy')),
                    self._parse_number(data.get('grid_energy_day')),
                    self._parse_number(data.get('grid_energy_night')),
                    self._parse_number(data.get('battery_charge_energy')),
                    self._parse_number(data.get('battery_discharge_energy')),
                    self._parse_number(data.get('pv_power_max')),
                    self._parse_number(data.get('consumption_power_max')),
                    self._parse_number(data.get('feed_in_power_max')),
                    self._parse_number(data.get('grid_power_max')),
                    self._parse_number(data.get('surplus_power_max')),
                    self._parse_number(data.get('battery_soc_min')),
                    self._parse_number(data.get('battery_soc_max')),
                    self._parse_number(data.get('autarky_avg')),
                    self._parse_number(data.get('self_sufficiency_rate')),
                    self._parse_number(data.get('cost_grid_consumption')),
                    self._parse_number(data.get('revenue_feed_in')),
                    self._parse_number(data.get('cost_saved')),
                    self._parse_number(data.get('total_benefit')),
                    self._parse_number(data.get('cost_without_solar'))
                )

                conn.execute(sql, values)

        return True

    def _write_device_event_batch(self, conn: sqlite3.Connection,
                                  data_list: List[Dict[str, Any]]) -> bool:
        """Schreibt Geräte-Events"""
        sql = """
              INSERT INTO device_events (timestamp, device_name, action, old_state, new_state, \
                                         reason, surplus_power, device_power, priority, runtime_today) \
              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) \
              """

        values = []
        for data in data_list:
            values.append((
                self._parse_timestamp(data.get('timestamp')),
                data.get('device_name'),
                data.get('action'),
                data.get('from_state'),
                data.get('to_state'),
                data.get('reason'),
                self._parse_number(data.get('surplus_power')),
                self._parse_number(data.get('device_power')),
                self._parse_number(data.get('priority')),
                self._parse_number(data.get('runtime_today'))
            ))

        conn.executemany(sql, values)
        return True

    def _write_device_status_batch(self, conn: sqlite3.Connection,
                                   data_list: List[Dict[str, Any]]) -> bool:
        """Schreibt Device-Status Daten"""
        sql = """
              INSERT INTO device_status (timestamp, total_devices_on, total_consumption, \
                                         surplus_power, used_surplus, device_states) \
              VALUES (?, ?, ?, ?, ?, ?) \
              """

        values = []
        for data in data_list:
            # Sammle Gerätezustände als JSON
            device_states = {}

            # Extrahiere Geräte-spezifische Daten
            for key, value in data.items():
                if '_state' in key or '_runtime' in key:
                    device_states[key] = value

            import json
            device_states_json = json.dumps(device_states)

            values.append((
                self._parse_timestamp(data.get('timestamp')),
                self._parse_number(data.get('total_on')),
                self._parse_number(data.get('total_consumption')),
                self._parse_number(data.get('surplus_power')),
                self._parse_number(data.get('used_surplus')),
                device_states_json
            ))

        conn.executemany(sql, values)
        return True

    def _parse_number(self, value: Any) -> Optional[float]:
        """Parst eine Zahl aus formatiertem String"""
        if value is None or value == '-':
            return None

        # Entferne Tausender-Trennzeichen und ersetze Komma
        if isinstance(value, str):
            value = value.replace('.', '').replace(',', '.')

        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _parse_timestamp(self, value: Any) -> Optional[str]:
        """Parst einen Timestamp"""
        if value is None or value == '-':
            return None
        return str(value)