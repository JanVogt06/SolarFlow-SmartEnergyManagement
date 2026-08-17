"""
FastAPI Endpoints
"""

import logging
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from typing import Any, Optional, List
from datetime import datetime, time
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator, ValidationInfo


_logger = logging.getLogger(__name__)


class SettingsUpdate(BaseModel):
    """Schema für Änderungen an den Server-Einstellungen"""
    fronius_ip: Optional[str] = None
    hue_bridge_ip: Optional[str] = None
    enable_hue: Optional[bool] = None
    update_interval: Optional[int] = Field(None, ge=1, le=3600)
    electricity_price: Optional[float] = Field(None, ge=0, le=10)
    electricity_price_night: Optional[float] = Field(None, ge=0, le=10)
    feed_in_tariff: Optional[float] = Field(None, ge=0, le=10)
    hysteresis_minutes: Optional[int] = Field(None, ge=0, le=1440)
    manual_override_minutes: Optional[int] = Field(None, ge=0, le=1440)
    min_battery_soc_on: Optional[float] = Field(None, ge=0, le=100)
    min_battery_soc_off: Optional[float] = Field(None, ge=0, le=100)

    @field_validator('fronius_ip', 'hue_bridge_ip')
    @classmethod
    def host_is_plausible(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None

        host = v.strip()
        if not host or '/' in host or ' ' in host:
            raise ValueError('Adresse muss ein Hostname oder eine IP ohne Protokoll sein')
        return host

    @field_validator('min_battery_soc_off')
    @classmethod
    def battery_thresholds_valid(cls, v: Optional[float], info: ValidationInfo) -> Optional[float]:
        soc_on = info.data.get('min_battery_soc_on')
        if v is not None and soc_on is not None and v > soc_on:
            raise ValueError('Ausschalt-Ladestand darf nicht höher als Einschalt-Ladestand sein')
        return v


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

    @field_validator('name')
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Name darf nicht leer sein')
        return v.strip()

    @field_validator('priority')
    @classmethod
    def priority_in_range(cls, v: int) -> int:
        if not 1 <= v <= 10:
            raise ValueError('Priorität muss zwischen 1 und 10 liegen')
        return v

    @field_validator('switch_off_threshold')
    @classmethod
    def thresholds_valid(cls, v: float, info: ValidationInfo) -> float:
        on_threshold = info.data.get('switch_on_threshold')
        if on_threshold is not None and v > on_threshold:
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

    # Nur lokale Origins: mit "*" könnte jede Webseite ungefragt Geräte schalten
    api_port = getattr(getattr(monitor, 'config', None), 'api', None)
    api_port = api_port.port if api_port else 8000
    cors_origins = [
        f"http://localhost:{api_port}",
        f"http://127.0.0.1:{api_port}",
    ]
    cors_origin_regex = r"^http://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+):\d+$"
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_origin_regex=cors_origin_regex,
        allow_methods=["GET", "POST", "DELETE", "PUT"],
        allow_headers=["*"],
    )

    # Als PyInstaller-Bundle liegt das Frontend im entpackten Temp-Verzeichnis
    base_path = Path(sys._MEIPASS) if getattr(sys, 'frozen', False) else Path(__file__).parent.parent
    frontend_path = base_path / "frontend"

    _logger.debug(f"Suche Frontend in: {frontend_path} (existiert: {frontend_path.exists()})")

    if frontend_path.exists():
        index_file = frontend_path / "index.html"
        if index_file.exists():
            _logger.debug(f"index.html gefunden: {index_file}")

            styles_path = frontend_path / "styles"
            scripts_path = frontend_path / "scripts"
            assets_path = frontend_path / "assets"

            if styles_path.exists():
                app.mount("/styles", StaticFiles(directory=str(styles_path)), name="styles")
                _logger.debug(f"Mounted: /styles -> {styles_path}")

            if scripts_path.exists():
                app.mount("/scripts", StaticFiles(directory=str(scripts_path)), name="scripts")
                _logger.debug(f"Mounted: /scripts -> {scripts_path}")

            if assets_path.exists():
                app.mount("/assets", StaticFiles(directory=str(assets_path)), name="assets")
                _logger.debug(f"Mounted: /assets -> {assets_path}")

            @app.get("/", response_class=FileResponse)
            def serve_frontend():
                """Serve Frontend index.html"""
                return FileResponse(index_file, media_type="text/html")
        else:
            _logger.warning(f"index.html nicht gefunden in {frontend_path}")
    else:
        _logger.warning(f"Frontend-Verzeichnis nicht gefunden: {frontend_path}")


    @app.get("/api/status")
    def get_status():
        """System Status"""
        return {
            "status": "online",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat()
        }

    @app.get("/api/current")
    def get_current_data():
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
    def get_daily_stats():
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

    @app.get("/api/settings")
    def get_settings():
        """Aktuelle Server-Einstellungen"""
        return monitor.settings.current()

    @app.put("/api/settings")
    def update_settings(update: SettingsUpdate):
        """Server-Einstellungen ändern, sofort anwenden und dauerhaft speichern"""
        changes = update.model_dump(exclude_none=True)
        if not changes:
            raise HTTPException(status_code=400, detail="Keine Änderungen übergeben")

        if not monitor.apply_settings(changes):
            raise HTTPException(
                status_code=500,
                detail="Einstellungen konnten nicht gespeichert werden — Datei nicht beschreibbar"
            )

        return {
            "success": True,
            "message": "Einstellungen gespeichert",
            "settings": monitor.settings.current()
        }

    @app.get("/api/hue")
    def get_hue_config():
        """Hue-Konfiguration und verfügbare Geräte"""
        config = monitor.config

        hue_enabled = config.devices.enable_hue if hasattr(config, 'devices') else False

        if not hue_enabled:
            return {
                "enabled": False,
                "devices": [],
                "bridge_ip": None
            }

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
    def get_devices():
        """Geräte-Status"""
        device_manager = monitor.get_device_manager()

        if not device_manager:
            return {"devices": [], "enabled": False}

        energy_controller = monitor.get_energy_controller()
        hysteresis_seconds = 300  # Default: 5 Minuten
        if energy_controller:
            hysteresis_seconds = int(energy_controller.hysteresis_time.total_seconds())

        now = datetime.now()
        devices = []
        for device in device_manager.get_devices_by_priority():
            hysteresis_remaining = None
            if device.state.value == "off" and device.last_switch_off:
                time_since_off = (now - device.last_switch_off).total_seconds()
                remaining = hysteresis_seconds - time_since_off
                if remaining > 0:
                    hysteresis_remaining = int(remaining)

            manual_remaining = None
            if device.is_manual(now):
                manual_remaining = int((device.manual_until - now).total_seconds())

            devices.append({
                "name": device.name,
                "description": device.description,
                "state": device.state.value,
                "power_consumption": device.power_consumption,
                "priority": device.priority.value if hasattr(device.priority, 'value') else device.priority,
                "runtime_today": device.runtime_today,
                "switch_on_threshold": device.switch_on_threshold,
                "switch_off_threshold": device.switch_off_threshold,
                "hysteresis_remaining": hysteresis_remaining,
                "manual_remaining": manual_remaining
            })

        return {
            "devices": devices,
            "enabled": True,
            "total_consumption": device_manager.get_total_consumption()
        }

    def _require_device(device_name: str):
        """Holt ein Gerät samt EnergyController oder wirft einen HTTP-Fehler."""
        device_manager = monitor.get_device_manager()
        energy_controller = monitor.get_energy_controller()

        if not device_manager or not energy_controller:
            raise HTTPException(status_code=503, detail="Gerätesteuerung nicht aktiv")

        device = device_manager.get_device(device_name)
        if not device:
            raise HTTPException(status_code=404, detail=f"Gerät '{device_name}' nicht gefunden")

        return device, energy_controller

    @app.post("/api/devices/{device_name}/toggle")
    def toggle_device(device_name: str):
        """Gerät manuell schalten und für die Übersteuerungsdauer aus der Automatik nehmen."""
        from device_management.device import DeviceState

        device, energy_controller = _require_device(device_name)

        if device.state == DeviceState.UNREACHABLE:
            raise HTTPException(
                status_code=409,
                detail=f"Gerät '{device_name}' ist nicht erreichbar"
            )

        target_on = device.state != DeviceState.ON
        if not energy_controller.switch_manually(device, target_on):
            raise HTTPException(
                status_code=502,
                detail="Schaltung fehlgeschlagen — Status unverändert"
            )

        return {
            "device": device_name,
            "current_state": device.state.value,
            "message": f"Gerät '{device_name}' manuell {'eingeschaltet' if target_on else 'ausgeschaltet'}"
        }

    @app.delete("/api/devices/{device_name}/manual")
    def release_manual(device_name: str):
        """Manuelle Übersteuerung beenden und sofort wieder automatisch steuern."""
        device, energy_controller = _require_device(device_name)
        energy_controller.release_manual_override(device)

        return {
            "device": device_name,
            "message": f"Gerät '{device_name}' wird wieder automatisch gesteuert"
        }

    @app.post("/api/devices")
    def create_device(device_data: DeviceCreate):
        """Neues Gerät erstellen"""
        device_manager = monitor.get_device_manager()

        if not device_manager:
            raise HTTPException(status_code=503, detail="Gerätesteuerung nicht aktiv")

        if device_manager.get_device(device_data.name):
            raise HTTPException(
                status_code=409,
                detail=f"Gerät mit Namen '{device_data.name}' existiert bereits"
            )

        try:
            from device_management.device import Device

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

            device_manager.add_device(new_device)

            if not device_manager.save_devices():
                device_manager.remove_device(new_device.name)
                raise HTTPException(
                    status_code=500,
                    detail="Gerät konnte nicht gespeichert werden — Konfigurationsdatei nicht beschreibbar"
                )

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
    def delete_device(device_name: str):
        """Gerät löschen"""
        device_manager = monitor.get_device_manager()

        if not device_manager:
            raise HTTPException(status_code=503, detail="Gerätesteuerung nicht aktiv")

        device = device_manager.get_device(device_name)
        if not device:
            raise HTTPException(status_code=404, detail=f"Gerät '{device_name}' nicht gefunden")

        device_manager.remove_device(device_name)

        if not device_manager.save_devices():
            device_manager.add_device(device)
            raise HTTPException(
                status_code=500,
                detail="Löschen konnte nicht gespeichert werden — Konfigurationsdatei nicht beschreibbar"
            )

        return {
            "success": True,
            "message": f"Gerät '{device_name}' erfolgreich gelöscht"
        }

    return app