"""
FastAPI Endpoints
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import Any, Optional, List, Dict
from datetime import datetime, time
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, validator


class DeviceCreate(BaseModel):
    """Schema für das Erstellen eines neuen Geräts"""
    name: str
    description: str = ""
    power_consumption: float
    priority: int
    switch_on_threshold: float
    switch_off_threshold: float
    min_runtime: int = 0
    max_runtime_per_day: int = 0
    allowed_time_ranges: List[List[str]] = []
    hue_device_name: Optional[str] = None  # Name des Hue-Geräts (wenn abweichend)

    @validator('name')
    def name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Name darf nicht leer sein')
        return v.strip()

    @validator('priority')
    def priority_in_range(cls, v):
        if not 1 <= v <= 10:
            raise ValueError('Priorität muss zwischen 1 und 10 liegen')
        return v

    @validator('switch_off_threshold')
    def thresholds_valid(cls, v, values):
        if 'switch_on_threshold' in values and v > values['switch_on_threshold']:
            raise ValueError('Ausschalt-Schwellwert darf nicht höher als Einschalt-Schwellwert sein')
        return v


def create_app(monitor: Any) -> FastAPI:
    """
    Erstellt die FastAPI App mit allen Endpoints.
    """
    app = FastAPI(
        title="SolarFlow API",
        version="1.0.0",
        description="Smart Energy Management System API"
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Frontend static files
    import sys
    from pathlib import Path

    # Bestimme Basis-Pfad
    if getattr(sys, 'frozen', False):
        # Wenn als exe ausgeführt
        base_path = Path(sys._MEIPASS)
    else:
        # Normal Python Ausführung
        # Von api/endpoints.py zwei Ebenen hoch zum Projekt-Root
        base_path = Path(__file__).parent.parent

    frontend_path = base_path / "frontend"

    print(f"Debug: Suche Frontend in: {frontend_path}")
    print(f"Debug: Frontend existiert: {frontend_path.exists()}")

    if frontend_path.exists():
        index_file = frontend_path / "index.html"
        if index_file.exists():
            print(f"Debug: index.html gefunden: {index_file}")

            # Mount die einzelnen Verzeichnisse unter ihren eigenen Pfaden
            styles_path = frontend_path / "styles"
            scripts_path = frontend_path / "scripts"
            assets_path = frontend_path / "assets"

            if styles_path.exists():
                app.mount("/styles", StaticFiles(directory=str(styles_path)), name="styles")
                print(f"Mounted: /styles -> {styles_path}")

            if scripts_path.exists():
                app.mount("/scripts", StaticFiles(directory=str(scripts_path)), name="scripts")
                print(f"Mounted: /scripts -> {scripts_path}")

            if assets_path.exists():
                app.mount("/assets", StaticFiles(directory=str(assets_path)), name="assets")
                print(f"Mounted: /assets -> {assets_path}")

            @app.get("/", response_class=HTMLResponse)
            async def serve_frontend():
                """Serve Frontend index.html"""
                with open(index_file, 'r', encoding='utf-8') as f:
                    return f.read()
        else:
            print(f"WARNUNG: index.html nicht gefunden in {frontend_path}")
    else:
        print(f"WARNUNG: Frontend-Verzeichnis nicht gefunden: {frontend_path}")

    # === API Endpoints ===

    @app.get("/api/status")
    async def get_status():
        """System Status"""
        return {
            "status": "online",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat()
        }

    @app.get("/api/current")
    async def get_current_data():
        """Aktuelle Solar-Daten"""
        data = monitor.get_current_data()

        if not data:
            raise HTTPException(status_code=503, detail="Keine Daten verfügbar")

        return {
            "timestamp": data.timestamp.isoformat() if data.timestamp else None,
            "pv_power": data.pv_power,
            "load_power": data.load_power,
            "grid_power": data.grid_power,
            "battery_power": data.battery_power,
            "battery_soc": data.battery_soc,
            "feed_in_power": data.feed_in_power,
            "grid_consumption": data.grid_consumption,
            "self_consumption": data.self_consumption,
            "autarky_rate": data.autarky_rate,
            "surplus_power": data.surplus_power,
            "has_battery": data.has_battery
        }

    @app.get("/api/stats")
    async def get_daily_stats():
        """Tagesstatistiken"""
        stats = monitor.get_daily_stats()

        return {
            "date": stats.date.isoformat(),
            "pv_energy": stats.pv_energy,
            "consumption_energy": stats.consumption_energy,
            "self_consumption_energy": stats.self_consumption_energy,
            "feed_in_energy": stats.feed_in_energy,
            "grid_energy": stats.grid_energy,
            "autarky_avg": stats.autarky_avg,
            "cost_saved": stats.cost_saved,
            "total_benefit": stats.total_benefit
        }

    @app.get("/api/hue")
    async def get_hue_config():
        """Hue-Konfiguration und verfügbare Geräte"""
        # Hole Config vom Monitor
        config = monitor.config

        # Prüfe ob Hue aktiviert ist
        hue_enabled = config.devices.enable_hue if hasattr(config, 'devices') else False

        if not hue_enabled:
            return {
                "enabled": False,
                "devices": [],
                "bridge_ip": None
            }

        # Hole Hue-Geräte vom Device Interface
        device_controller = monitor.device_controller
        hue_devices = []

        if (device_controller and
            device_controller.device_interface and
            device_controller.device_interface.interface_type == "hue"):
            hue_devices = device_controller.device_interface.list_devices()

        return {
            "enabled": True,
            "devices": hue_devices,
            "bridge_ip": config.devices.hue_bridge_ip
        }

    @app.get("/api/devices")
    async def get_devices():
        """Geräte-Status"""
        device_manager = monitor.get_device_manager()

        if not device_manager:
            return {"devices": [], "enabled": False}

        # Hole EnergyController für Hysterese-Info
        energy_controller = monitor.get_energy_controller()
        hysteresis_seconds = 300  # Default: 5 Minuten
        if energy_controller:
            hysteresis_seconds = int(energy_controller.hysteresis_time.total_seconds())

        now = datetime.now()
        devices = []
        for device in device_manager.get_devices_by_priority():
            # Berechne verbleibende Hysterese-Zeit
            hysteresis_remaining = None
            if device.state.value == "off" and device.last_switch_off:
                time_since_off = (now - device.last_switch_off).total_seconds()
                remaining = hysteresis_seconds - time_since_off
                if remaining > 0:
                    hysteresis_remaining = int(remaining)

            devices.append({
                "name": device.name,
                "state": device.state.value,
                "power_consumption": device.power_consumption,
                "priority": device.priority.value if hasattr(device.priority, 'value') else device.priority,
                "runtime_today": device.runtime_today,
                "switch_on_threshold": device.switch_on_threshold,
                "switch_off_threshold": device.switch_off_threshold,
                "hysteresis_remaining": hysteresis_remaining
            })

        return {
            "devices": devices,
            "enabled": True,
            "total_consumption": device_manager.get_total_consumption()
        }

    @app.post("/api/devices/{device_name}/toggle")
    async def toggle_device(device_name: str):
        """Gerät manuell schalten"""
        device_manager = monitor.get_device_manager()

        if not device_manager:
            raise HTTPException(status_code=404, detail="Gerätesteuerung nicht aktiv")

        device = device_manager.get_device(device_name)
        if not device:
            raise HTTPException(status_code=404, detail=f"Gerät '{device_name}' nicht gefunden")

        # Hier würdest du die Schaltlogik implementieren
        # Für jetzt nur Status zurückgeben
        return {
            "device": device_name,
            "current_state": device.state.value,
            "message": "Manual control not yet implemented"
        }

    @app.post("/api/devices")
    async def create_device(device_data: DeviceCreate):
        """Neues Gerät erstellen"""
        device_manager = monitor.get_device_manager()

        if not device_manager:
            raise HTTPException(status_code=503, detail="Gerätesteuerung nicht aktiv")

        # Prüfe ob Gerät bereits existiert
        if device_manager.get_device(device_data.name):
            raise HTTPException(
                status_code=409,
                detail=f"Gerät mit Namen '{device_data.name}' existiert bereits"
            )

        try:
            # Importiere Device-Klasse
            from device_management.device import Device

            # Konvertiere Zeitbereiche
            time_ranges = []
            for time_range in device_data.allowed_time_ranges:
                if len(time_range) == 2:
                    try:
                        start = time.fromisoformat(time_range[0])
                        end = time.fromisoformat(time_range[1])
                        time_ranges.append((start, end))
                    except ValueError as e:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Ungültiges Zeitformat: {e}"
                        )

            # Erstelle neues Gerät
            new_device = Device(
                name=device_data.name,
                description=device_data.description,
                power_consumption=device_data.power_consumption,
                priority=device_data.priority,
                switch_on_threshold=device_data.switch_on_threshold,
                switch_off_threshold=device_data.switch_off_threshold,
                min_runtime=device_data.min_runtime,
                max_runtime_per_day=device_data.max_runtime_per_day,
                allowed_time_ranges=time_ranges
            )

            # Füge Gerät hinzu
            device_manager.add_device(new_device)

            # Speichere in JSON
            device_manager.save_devices()

            return {
                "success": True,
                "message": f"Gerät '{device_data.name}' erfolgreich erstellt",
                "device": {
                    "name": new_device.name,
                    "power_consumption": new_device.power_consumption,
                    "priority": new_device.priority
                }
            }

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Fehler beim Erstellen: {str(e)}")

    @app.delete("/api/devices/{device_name}")
    async def delete_device(device_name: str):
        """Gerät löschen"""
        device_manager = monitor.get_device_manager()

        if not device_manager:
            raise HTTPException(status_code=503, detail="Gerätesteuerung nicht aktiv")

        device = device_manager.get_device(device_name)
        if not device:
            raise HTTPException(status_code=404, detail=f"Gerät '{device_name}' nicht gefunden")

        try:
            # Entferne Gerät
            device_manager.remove_device(device_name)

            # Speichere in JSON
            device_manager.save_devices()

            return {
                "success": True,
                "message": f"Gerät '{device_name}' erfolgreich gelöscht"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Fehler beim Löschen: {str(e)}")

    return app