#!/bin/bash
# =============================================================================
# SolarFlow - Sync Datalogs & Config vom Server auf den Mac
# =============================================================================

REMOTE="jan-server"
REMOTE_BASE="/home/janvogt/dockercontainer/SolarFlow-SmartEnergyManagement"
LOCAL_BASE="/Users/janvogt/Desktop/Git_Clones/SolarFlow-SmartEnergyManagement"

echo "🔄 Starte Sync von ${REMOTE}..."

# Datalogs-Ordner synchronisieren (löscht lokal Dateien, die remote nicht mehr existieren)
echo "📂 Synchronisiere Datalogs..."
rsync -avz --delete "${REMOTE}:${REMOTE_BASE}/Datalogs/" "${LOCAL_BASE}/Datalogs/"

# solar_monitor.log kopieren
echo "📄 Kopiere solar_monitor.log..."
rsync -avz "${REMOTE}:${REMOTE_BASE}/solar_monitor.log" "${LOCAL_BASE}/solar_monitor.log"

# devices.json kopieren
echo "📄 Kopiere devices.json..."
rsync -avz "${REMOTE}:${REMOTE_BASE}/devices.json" "${LOCAL_BASE}/devices.json"

echo "✅ Sync abgeschlossen."
