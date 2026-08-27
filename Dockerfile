FROM python:3.14

LABEL org.opencontainers.image.title="SolarFlow Smart Energy Management" \
      org.opencontainers.image.description="Intelligentes Energie-Management für Fronius Solaranlagen" \
      org.opencontainers.image.source="https://github.com/JanVogt06/SolarFlow-SmartEnergyManagement" \
      org.opencontainers.image.licenses="MIT"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Alles Veränderliche liegt unter /data, damit ein einziges Volume genügt.
# HOME zeigt ebenfalls dorthin, weil phue den Bridge-Token in ~/.python_hue ablegt.
ENV HOME=/data \
    SETTINGS_FILE=/data/settings.json \
    DEVICE_CONFIG_FILE=/data/devices.json \
    LOG_FILE=/data/solar_monitor.log \
    DATA_LOG_DIR=/data/Datalogs \
    DATABASE_PATH=/data/Datalogs/solar_energy.db \
    API_ENABLED=True \
    API_HOST=0.0.0.0 \
    API_PORT=8000 \
    USE_LIVE_DISPLAY=False \
    PYTHONUNBUFFERED=1

RUN mkdir -p /data/Datalogs

VOLUME /data

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.getenv('API_PORT', '8000') + '/api/status').read()"]

CMD ["python", "main.py"]
