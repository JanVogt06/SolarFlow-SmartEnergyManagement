# SolarFlow Smart Energy Management

<p align="center">
  <img src="assets/logo_without-background.png" alt="SolarFlow Logo" width="512">
</p>

<p align="center">
  <strong>☀️ Intelligentes Energie-Management für Ihre Solaranlage</strong><br>
  <sub>Maximieren Sie Ihren Eigenverbrauch • Sparen Sie Stromkosten • Schonen Sie die Umwelt</sub>
</p>

<p align="center">
  <a href="https://github.com/JanVogt06/SolarFlow-SmartEnergyManagement/releases/latest">
    <img src="https://img.shields.io/github/v/release/JanVogt06/SolarFlow-SmartEnergyManagement?style=for-the-badge&label=Download" alt="Download">
  </a>
  <a href="https://janvogt06.github.io/SolarFlow-SmartEnergyManagement/">
    <img src="https://img.shields.io/badge/Dokumentation-Website-blue?style=for-the-badge" alt="Dokumentation">
  </a>
  <a href="https://github.com/JanVogt06/SolarFlow-SmartEnergyManagement/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/JanVogt06/SolarFlow-SmartEnergyManagement?style=for-the-badge" alt="Lizenz">
  </a>
</p>

---

## 🎯 Was ist SolarFlow?

SolarFlow ist ein benutzerfreundliches Energie-Management-System für **Fronius Solaranlagen**. Es hilft Ihnen, Ihren selbst erzeugten Solarstrom optimal zu nutzen und dadurch Stromkosten zu sparen.

### Das macht SolarFlow für Sie:
- 📊 **Zeigt Ihre Solarproduktion in Echtzeit** im Browser
- 🔌 **Schaltet Geräte automatisch ein** wenn genug Solarstrom da ist
- 💰 **Berechnet Ihre Ersparnis** und zeigt Tagesstatistiken
- 📱 **Funktioniert auf jedem Gerät** mit Webbrowser (PC, Tablet, Smartphone)
- 🏠 **Steuert smarte Geräte** wie Philips Hue Steckdosen

## 🚀 Schnellstart (5 Minuten)

### 1️⃣ Programm herunterladen

Laden Sie die passende Version für Ihr System herunter:

| System | Download | Hinweis |
|--------|----------|---------|
| **Windows** | [⬇️ SolarFlow-windows-x64.exe](https://github.com/JanVogt06/SolarFlow-SmartEnergyManagement/releases/latest/download/SolarFlow-windows-x64.exe) | Doppelklick zum Starten |
| **macOS** | [⬇️ SolarFlow-macos-x64](https://github.com/JanVogt06/SolarFlow-SmartEnergyManagement/releases/latest/download/SolarFlow-macos-x64) | Terminal: `chmod +x` dann starten |
| **Linux** | [⬇️ SolarFlow-linux-x64](https://github.com/JanVogt06/SolarFlow-SmartEnergyManagement/releases/latest/download/SolarFlow-linux-x64) | Terminal: `chmod +x` dann starten |

### 2️⃣ Programm starten

**Windows:**
- Doppelklick auf `SolarFlow-windows-x64.exe`
- Falls Windows warnt: "Weitere Informationen" → "Trotzdem ausführen"

**macOS/Linux:**
```bash
# Datei ausführbar machen (nur beim ersten Mal)
chmod +x SolarFlow-*

# Programm starten
./SolarFlow-*
```

### 3️⃣ Browser öffnet automatisch

Das Web-Dashboard öffnet sich automatisch unter: **http://localhost:8000**

Falls nicht, öffnen Sie einen Browser und geben Sie die Adresse manuell ein.

### 4️⃣ Fronius IP-Adresse eingeben

Starten Sie das SolarFlow Backend mit der IP-Adresse Ihrer Fronius Anlage:

```bash python main.py --ip```

Oder verwenden Sie die Executable:

```bash SolarFlow-windows-x64.exe --ip```

Beispiele:

```bash
python main.py --ip 192.168.1.100
```
```bash
SolarFlow-windows-x64.exe --ip 192.168.178.99
```

## 🐳 Mit Docker starten

Statt der Executable lässt sich SolarFlow auch als Container betreiben — praktisch für
einen Raspberry Pi, NAS oder Server, der ohnehin durchläuft. Der Quellcode wird dafür
nicht gebraucht, eine Datei genügt.

### Ohne Checkout, nur mit `docker pull`

`docker-compose.yml` in einem leeren Verzeichnis anlegen:

```yaml
services:
  solarflow:
    image: ghcr.io/janvogt06/solarflow:latest
    container_name: solarflow
    restart: unless-stopped
    ports:
      - "${SOLARFLOW_PORT:-8000}:8000"
    environment:
      # IP-Adresse des Fronius Wechselrichters
      - FRONIUS_IP=192.168.178.90
      # Philips Hue (optional)
      - ENABLE_HUE=False
      - HUE_BRIDGE_IP=192.168.178.26
    volumes:
      # Einstellungen, Geräte, Logs, Datenbank und Hue-Token
      - solarflow-data:/data
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/status').read()"]
      interval: 30s
      timeout: 5s
      retries: 3

volumes:
  solarflow-data:
```

Dann:

```bash
docker compose pull && docker compose up -d
```

Danach ist das Dashboard unter http://localhost:8000 erreichbar, von anderen Geräten im
Netzwerk über die Adresse des Hosts, zum Beispiel `http://192.168.1.20:8000`.

Statt `latest` lässt sich eine Version festnageln (`:1.2.0`), wenn Sie selbst entscheiden
möchten, wann aktualisiert wird. Die `docker-compose.yml` in diesem Repository trägt
zusätzlich `build: .` für die lokale Entwicklung; auf einer Maschine ohne Quellcode ist
dieser Schlüssel nutzlos und `--build` würde fehlschlagen, dort also weglassen.

### Aus einem Checkout

```bash
docker compose up -d --build
```

### Port ändern

Ohne die Compose-Datei anzufassen:

```bash
SOLARFLOW_PORT=9000 docker compose up -d
```

Soll das Dashboard nur vom Host selbst erreichbar sein, das Port-Mapping auf
`"127.0.0.1:${SOLARFLOW_PORT:-8000}:8000"` ändern.

### Daten und Einstellungen

Alles Veränderliche liegt im Container unter `/data` und damit im Volume
`solarflow-data` — es übersteht Neustarts und Updates:

| Pfad | Inhalt |
| --- | --- |
| `/data/settings.json` | Im Dashboard geänderte Einstellungen |
| `/data/devices.json` | Gerätekonfiguration |
| `/data/solar_monitor.log` | Logdatei |
| `/data/Datalogs/` | CSV-Logs und `solar_energy.db` |
| `/data/.python_hue` | Token der Hue Bridge |

Ein Blick hinein:

```bash
docker compose exec solarflow cat /data/settings.json
```

Fronius-IP, Hue-Bridge, Strompreise und Schwellwerte lassen sich auch nach dem Start im
Tab **Einstellungen** ändern; die Umgebungsvariablen der Compose-Datei sind nur die
Startwerte. Sämtliche in [Erweiterte Einstellungen](#️-erweiterte-einstellungen)
genannten Optionen sind zusätzlich als Umgebungsvariablen setzbar.

Wer die frühere Compose-Datei mit den einzelnen Bind-Mounts (`./devices.json`,
`./settings.json`, …) benutzt hat, kopiert die vorhandenen Dateien einmalig ins Volume:

```bash
docker compose cp devices.json solarflow:/data/devices.json
docker compose cp settings.json solarflow:/data/settings.json
docker compose cp .python_hue solarflow:/data/.python_hue
docker compose restart
```

### Aktualisieren

```bash
docker compose pull && docker compose up -d
```

## 📦 Releases

Ein Tag, der mit `v` beginnt, baut ein Multi-Architektur-Image (`linux/amd64` und
`linux/arm64`), veröffentlicht es unter `ghcr.io/janvogt06/solarflow` als `<version>`,
`<major>.<minor>` und `latest`, erstellt die Executables für Windows, macOS und Linux
und legt daraus ein GitHub-Release an.

## 📸 So sieht's aus

### Web-Dashboard
![Dashboard Screenshot](assets/dashboard-screenshot.png)
*Modernes Web-Dashboard mit Live-Daten Ihrer Solaranlage*

### Terminal-Ansicht (optional)
![Live Display](assets/live-display-demo.png)
*Zusätzliche Terminal-Ansicht für Technik-Interessierte*

## ✨ Hauptfunktionen

### 📊 Live-Monitoring
- **Echtzeitdaten** von Ihrem Fronius Wechselrichter
- **Übersichtliche Grafiken** für:
  - Aktuelle Solarproduktion
  - Hausverbrauch
  - Einspeisung ins Netz
  - Batteriestand (falls vorhanden)
- **Tagesstatistiken** mit Kostenberechnung

### 🔌 Intelligente Gerätesteuerung
- **Automatisches Ein-/Ausschalten** von Geräten bei Solarüberschuss
- **Prioritätssystem**: Wichtige Geräte werden zuerst eingeschaltet
- **Zeitsteuerung**: Geräte nur zu bestimmten Zeiten (z.B. Poolpumpe nur tagsüber)
- **Philips Hue Integration**: Steuert echte Smart-Home-Geräte
- **Manueller Modus**: Schalten Sie ein Gerät selbst — in der Weboberfläche oder in der
  Hue-App — pausiert die Automatik für dieses Gerät (Standard: 30 Minuten)
- **Erreichbarkeits-Erkennung**: Nicht eingesteckte Hue-Geräte werden als
  „Nicht erreichbar" angezeigt statt fälschlich als eingeschaltet

### 💰 Kostenanalyse
- **Tägliche Ersparnis** in Euro
- **Eigenverbrauchsquote** und Autarkiegrad
- **Vergleich**: Was hätte der Strom ohne Solar gekostet?
- **Einspeisevergütung** wird berücksichtigt

## ⚙️ Erweiterte Einstellungen

### Einstellungen im Browser

Im Tab **Einstellungen** lassen sich Fronius-IP, Hue-Bridge, Strompreise, Einspeisevergütung
sowie Hysterese-, Manuell- und Batterie-Schwellwerte ändern. Die Werte greifen sofort und
landen in `settings.json`; alles, was dort nicht steht, kommt weiterhin aus den
Umgebungsvariablen.

### Geräte konfigurieren

SolarFlow kann Ihre Haushaltsgeräte intelligent steuern. Erstellen Sie eine `devices.json` Datei:

```json
[
  {
    "name": "Waschmaschine",
    "power_consumption": 2000,
    "priority": 3,
    "switch_on_threshold": 2200,
    "switch_off_threshold": 1800,
    "allowed_time_ranges": [["08:00", "20:00"]]
  },
  {
    "name": "Poolpumpe", 
    "power_consumption": 750,
    "priority": 6,
    "switch_on_threshold": 1000,
    "switch_off_threshold": 500,
    "allowed_time_ranges": [["10:00", "18:00"]]
  }
]
```

### Kommandozeilen-Optionen

Für erfahrene Nutzer gibt es zusätzliche Startoptionen:

```bash
# Mit direkter IP-Angabe starten
SolarFlow --ip 192.168.178.90

# Ohne Web-Interface (nur Terminal)
SolarFlow --no-api

# Mit angepasstem Update-Intervall (Sekunden)
SolarFlow --interval 10
```

## 🔗 Nützliche Links

- 🌐 **Web-Dashboard**: http://localhost:8000 (nach dem Start)
- 📚 **API-Dokumentation**: http://localhost:8000/docs
- 🏠 **Projekt-Website**: [janvogt06.github.io/SolarFlow-SmartEnergyManagement](https://janvogt06.github.io/SolarFlow-SmartEnergyManagement/)
- 🐛 **Probleme melden**: [GitHub Issues](https://github.com/JanVogt06/SolarFlow-SmartEnergyManagement/issues)

## 💡 Häufige Fragen

<details>
<summary><b>Wie finde ich die IP-Adresse meines Fronius Wechselrichters?</b></summary>

1. **Im Router nachschauen**: 
   - Router-Oberfläche öffnen (meist `192.168.1.1` oder `192.168.178.1`)
   - Nach "Verbundene Geräte" oder "DHCP-Clients" suchen
   - Nach "Fronius" oder "Solar" suchen

2. **Am Wechselrichter-Display**:
   - Menü → Einstellungen → Netzwerk → IP-Adresse

3. **Mit der Fronius Solar.web App**:
   - In der App ist die lokale IP sichtbar
</details>

<details>
<summary><b>Funktioniert SolarFlow mit meinem Wechselrichter?</b></summary>

SolarFlow funktioniert mit allen **Fronius Wechselrichtern**, die die Solar API unterstützen:
- Fronius Symo
- Fronius Primo  
- Fronius GEN24
- Fronius Tauro
- Und weitere...

Die Solar API ist bei den meisten Fronius Wechselrichtern ab Baujahr 2013 verfügbar.
</details>

<details>
<summary><b>Kann ich SolarFlow von unterwegs nutzen?</b></summary>

Standardmäßig läuft SolarFlow nur in Ihrem Heimnetzwerk. Für Zugriff von außen:
- VPN zu Ihrem Heimnetzwerk einrichten
- Oder Port-Weiterleitung im Router (Sicherheitsrisiko beachten!)
</details>

<details>
<summary><b>Was kostet SolarFlow?</b></summary>

**Nichts!** SolarFlow ist komplett kostenlos und Open Source. Sie können es beliebig nutzen und sogar den Quellcode anpassen.
</details>

## 🛠️ Für Entwickler

<details>
<summary><b>Von Quellcode ausführen</b></summary>

```bash
# Repository klonen
git clone https://github.com/JanVogt06/SolarFlow-SmartEnergyManagement.git
cd SolarFlow-SmartEnergyManagement

# Abhängigkeiten installieren
pip install -r requirements.txt

# Starten
python SolarFlow.py --ip <FRONIUS_IP>
```
</details>

<details>
<summary><b>Eigene Builds erstellen</b></summary>

```bash
# PyInstaller installieren
pip install pyinstaller

# Executable erstellen
pyinstaller SolarFlow.spec --clean
```
</details>

## 🤝 Unterstützung & Beitrag

- **Probleme?** [Issue erstellen](https://github.com/JanVogt06/SolarFlow-SmartEnergyManagement/issues/new)
- **Fragen?** [Discussions](https://github.com/JanVogt06/SolarFlow-SmartEnergyManagement/discussions)
- **Verbesserungen?** Pull Requests sind willkommen!

## 📄 Lizenz

Dieses Projekt steht unter der MIT-Lizenz - siehe [LICENSE](LICENSE) für Details.

---

<p align="center">
  <b>⭐ Gefällt Ihnen SolarFlow?</b><br>
  Geben Sie dem Projekt einen Stern auf GitHub!<br><br>
  <sub>Made with ❤️ für nachhaltige Energienutzung</sub>
</p>