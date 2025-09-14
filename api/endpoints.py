"""
FastAPI Endpoints
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Any, Optional, List, Dict
from datetime import datetime


def create_app(monitor: Any) -> FastAPI:
    """
    Erstellt die FastAPI App mit allen Endpoints.

    Args:
        monitor: SolarMonitor Instanz

    Returns:
        FastAPI App
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

    # Frontend static files (wenn vorhanden)
    frontend_path = Path(__file__).parent.parent.parent / "frontend"
    if frontend_path.exists():
        app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

        @app.get("/")
        async def serve_frontend():
            """Serve Frontend"""
            return FileResponse(frontend_path / "index.html")

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

    @app.get("/api/devices")
    async def get_devices():
        """Geräte-Status"""
        device_manager = monitor.get_device_manager()

        if not device_manager:
            return {"devices": [], "enabled": False}

        devices = []
        for device in device_manager.get_devices_by_priority():
            devices.append({
                "name": device.name,
                "state": device.state.value,
                "power_consumption": device.power_consumption,
                "priority": device.priority.value if hasattr(device.priority, 'value') else device.priority,
                "runtime_today": device.runtime_today,
                "switch_on_threshold": device.switch_on_threshold,
                "switch_off_threshold": device.switch_off_threshold
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

    return app