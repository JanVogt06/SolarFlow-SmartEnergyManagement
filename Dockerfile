# Base Image: Python 3.11 (schlank)
FROM python:3.11-slim

# Arbeitsverzeichnis im Container
WORKDIR /app

# System-Abhängigkeiten installieren (gcc für manche Python-Packages)
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python-Dependencies installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Gesamten Projekt-Code kopieren
COPY . .

# Persistente Daten-Verzeichnisse sicherstellen
RUN mkdir -p /app/Datalogs

# Port 8000 nach außen öffnen (für FastAPI)
EXPOSE 8000

# Container startet mit diesem Befehl
CMD ["python", "main.py"]
