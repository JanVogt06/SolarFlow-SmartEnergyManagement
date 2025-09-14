"""
API Server Integration
"""

import threading
import logging
from typing import Optional, Any
import uvicorn
from .endpoints import create_app


class APIServer:
    """Managed den API Server als Thread"""

    def __init__(self, monitor: Any, config: Any):
        """
        Initialisiert den API Server.

        Args:
            monitor: SolarMonitor Instanz
            config: Config Objekt
        """
        self.monitor = monitor
        self.config = config
        self.logger = logging.getLogger(__name__)

        # FastAPI App erstellen
        self.app = create_app(monitor)

        # Server Thread
        self.server_thread: Optional[threading.Thread] = None
        self.server: Optional[uvicorn.Server] = None

    def start(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        """Startet den API Server im Hintergrund"""
        self.logger.info(f"Starte API Server auf http://{host}:{port}")

        # Uvicorn Config
        config = uvicorn.Config(
            app=self.app,
            host=host,
            port=port,
            log_level="warning",  # Reduziere Log-Spam
            access_log=False
        )

        self.server = uvicorn.Server(config)

        # Starte in Thread
        self.server_thread = threading.Thread(
            target=self.server.run,
            daemon=True
        )
        self.server_thread.start()

        self.logger.info("API Server läuft")
        self.logger.info(f"Dashboard: http://localhost:{port}/")
        self.logger.info(f"API Docs: http://localhost:{port}/docs")

    def stop(self) -> None:
        """Stoppt den API Server"""
        if self.server:
            self.server.should_exit = True
            self.logger.info("API Server gestoppt")