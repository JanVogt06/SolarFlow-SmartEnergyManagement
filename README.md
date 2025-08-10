# Smart Energy Manager

<p align="center">
  <img src="assets/logo_without-background.png" alt="Smart Energy Manager Logo" width="512">
</p>

<p align="center">
  <strong>🌞 Intelligentes Energie-Management-System für Fronius Solaranlagen</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#verwendung">Verwendung</a> •
  <a href="#gerätesteuerung">Gerätesteuerung</a> •
  <a href="#architektur">Architektur</a>
</p>

---

## 📋 Überblick

Der **Smart Energy Manager** ist ein fortschrittliches Python-basiertes Energie-Management-System für Fronius Wechselrichter. Es maximiert Ihren Solarstrom-Eigenverbrauch durch intelligente Gerätesteuerung und bietet dabei umfassende Analyse- und Visualisierungsmöglichkeiten.

### 🎯 Hauptziele
- **Maximaler Eigenverbrauch** durch intelligente Lastverteilung
- **Automatische Gerätesteuerung** basierend auf Überschussenergie
- **Echte Hardware-Integration** (z.B. Philips Hue)
- **Echtzeit-Visualisierung** mit modernem Live-Display
- **Umfassende Datenanalyse** für optimale Kosteneinsparungen

## ✨ Features

### 🖥️ Modernes Live-Display
- **Rich Live Display** mit automatischen Updates
- Farbcodierte Echtzeitanzeige aller relevanten Werte
- Übersichtliche Panels für Leistungsdaten, Kennzahlen und Gerätesteuerung
- Fallback auf klassische Anzeige bei Bedarf

![Live Display Image](assets/live-display-demo.png)

### 🌞 Solar-Monitoring
- **Echtzeit-Überwachung** aller Leistungsflüsse
- Automatische Erkennung von **Batteriespeichern**
- Berechnung von:
  - Eigenverbrauch und Autarkiegrad
  - Verfügbarem Überschuss
  - Netzeinspeisung und -bezug
  - Batterie-Lade-/Entladeleistung

### 🔌 Intelligente Gerätesteuerung
- **10-stufiges Prioritätssystem** für optimale Lastverteilung
- **Philips Hue Integration** für echte Hardware-Steuerung
- Zeitbasierte Einschränkungen (z.B. "nur tagsüber")
- Hysterese-Funktionalität gegen häufiges Schalten
- Berücksichtigung von:
  - Mindest- und Maximallaufzeiten
  - Einschalt- und Ausschalt-Schwellwerten
  - Mehreren Zeitfenstern pro Gerät

### 💡 Hardware-Integration
- **Philips Hue Bridge** Unterstützung
- Automatische Geräteerkennung
- Synchronisation zwischen virtuellem und realem Status
- Sauberer Startzustand (alle Geräte aus)

### 📊 Datenerfassung & Analyse
- **Multi-Format Logging**:
  - CSV-Dateien (konfigurierbar)
  - SQLite-Datenbank
  - Separate Logs für Solar-, Geräte- und Statistikdaten
- **Automatische Statistiken**:
  - Tagesstatistiken mit Kostenberechnung
  - Min/Max-Werte für alle Parameter
  - Energie-Akkumulation
- **Kostenoptimierung**:
  - Tag-/Nachttarif-Unterstützung
  - Einspeisevergütung
  - ROI-Berechnung

### 🎨 Flexible Anzeigemodi
- **Rich Live Display** (Standard) - Modernes Terminal-UI
- **Klassische Anzeige** - Traditionelle Ausgabe
- **Simple Mode** - Einzeilig für kleine Displays
- **Multiline Compact** - Kompakte Übersicht
- Konfigurierbare Farben und Schwellwerte

## 🚀 Installation

### Systemvoraussetzungen
- Python 3.8 oder höher
- Fronius Wechselrichter mit aktivierter Solar API
- Optional: Philips Hue Bridge für Hardware-Steuerung
- Terminal mit Farbunterstützung (für optimale Darstellung)

### Schnellinstallation

1. **Repository klonen**
   ```bash
   git clone https://github.com/yourusername/smart-energy-manager.git
   cd smart-energy-manager
   ```

2. **Automatische Installation**
   
   Das Programm prüft beim Start automatisch alle Abhängigkeiten:
   ```bash
   python main.py
   ```
   
   Bei fehlenden Paketen wird eine automatische Installation angeboten.

3. **Manuelle Installation** (optional)
   ```bash
   pip install requests rich phue
   # oder
   pip install -r requirements.txt
   ```

### Erste Konfiguration

1. **Fronius IP-Adresse ermitteln**
   ```bash
   # Im Router nachsehen oder:
   ping fronius.local
   ```

2. **Testlauf starten**
   ```bash
   python main.py --ip <FRONIUS_IP>
   ```

3. **Geräte konfigurieren** (optional)
   ```bash
   # devices.json anpassen (siehe Beispiele unten)
   ```

## 📖 Verwendung

### Basis-Befehle

```bash
# Standard-Start mit Live-Display und Gerätesteuerung
python main.py

# Mit spezifischer Fronius IP
python main.py --ip 192.168.1.100

# Simple Mode für SSH/kleine Displays
python main.py --simple

# Klassische Anzeige ohne Live-Updates
python main.py --no-live
```

### Erweiterte Optionen

```bash
# Hue-Integration aktivieren
python main.py --enable-hue --hue-ip 192.168.1.50

# Angepasste Update-Intervalle
python main.py --interval 10 --daily-stats-interval 900

# Kostenparameter
python main.py --electricity-price 0.35 --feed-in-tariff 0.08

# Debug-Modus
python main.py --log-level DEBUG
```

### Umgebungsvariablen

Alternativ zur Kommandozeile können Umgebungsvariablen verwendet werden:

```bash
export FRONIUS_IP="192.168.1.100"
export ENABLE_HUE="True"
export HUE_BRIDGE_IP="192.168.1.50"
export UPDATE_INTERVAL="5"
```

## ⚙️ Gerätesteuerung

### Konfigurationsdatei (devices.json)

```json
[
  {
    "name": "Hue Steckdose Waschmaschine",
    "description": "Smarte Steckdose für Waschmaschine",
    "power_consumption": 2000,
    "priority": 3,
    "min_runtime": 30,
    "max_runtime_per_day": 180,
    "switch_on_threshold": 2200,
    "switch_off_threshold": 1800,
    "allowed_time_ranges": [
      ["08:00", "20:00"]
    ]
  },
  {
    "name": "Hue Lampe Büro",
    "description": "Bürobeleuchtung bei Überschuss",
    "power_consumption": 20,
    "priority": 8,
    "min_runtime": 5,
    "max_runtime_per_day": 0,
    "switch_on_threshold": 100,
    "switch_off_threshold": 50,
    "allowed_time_ranges": [
      ["07:00", "22:00"]
    ]
  },
  {
    "name": "Poolpumpe",
    "description": "Filterpumpe für Pool",
    "power_consumption": 750,
    "priority": 6,
    "min_runtime": 120,
    "max_runtime_per_day": 480,
    "switch_on_threshold": 1000,
    "switch_off_threshold": 500,
    "allowed_time_ranges": [
      ["10:00", "18:00"]
    ]
  }
]
```

### Prioritätssystem

| Priorität | Kategorie | Verwendung | Beispiele |
|-----------|-----------|------------|-----------|
| 1 | Kritisch | Unverzichtbare Geräte | Kühlschrank, Server |
| 2-3 | Sehr hoch | Wichtige Alltagsgeräte | Waschmaschine, Geschirrspüler |
| 4-5 | Hoch | Regelmäßig genutzt | Warmwasserbereiter |
| 6-7 | Mittel | Flexible Nutzung | Poolpumpe, Klimaanlage |
| 8-9 | Niedrig | Optionale Verbraucher | Zusatzbeleuchtung |
| 10 | Optional | Nur bei viel Überschuss | Elektroheizung |

### Steuerungslogik im Detail

1. **Einschaltbedingungen**:
   - Überschuss ≥ Einschalt-Schwellwert
   - Gerät ist in erlaubtem Zeitfenster
   - Maximale Tageslaufzeit nicht erreicht
   - Hysterese-Zeit abgelaufen

2. **Ausschaltbedingungen**:
   - Überschuss < Ausschalt-Schwellwert
   - Außerhalb des Zeitfensters
   - Maximale Laufzeit erreicht
   - Mindestlaufzeit wurde eingehalten

3. **Hysterese**:
   - Verhindert "Flackern" bei schwankender Erzeugung
   - Standard: 5 Minuten zwischen Schaltvorgängen
   - Pro Gerät konfigurierbar

## 📊 Ausgabe-Beispiel

### Standard-Anzeige

```
============================================================
Zeitstempel:         2025-07-26 14:32:15
============================================================
PV-Erzeugung:              4,235 W
Hausverbrauch:             1,842 W
Einspeisung:               2,393 W
Batterie-Ladestand:         85.2 %
------------------------------------------------------------
Eigenverbrauch:            1,842 W
Autarkiegrad:              100.0 %
Verfügbarer Überschuss:    2,393 W
============================================================

GERÄTESTEUERUNG:
------------------------------------------------------------
Gesteuerter Verbrauch:          0 W
Aktueller Überschuss:       2,393 W

Gerät                Priorität  Leistung Status       Laufzeit heute
---------------------------------------------------------------------------
Waschmaschine                3     2000W AUS              0h 0m
Poolpumpe                    7      750W EIN             2h 15m
```

### Tagesstatistik

```
============================================================
TAGESSTATISTIK              26.07.2025
============================================================

Energie heute:
PV-Produktion:              24.83 kWh
Verbrauch:                  18.42 kWh
Eigenverbrauch:             15.31 kWh
Einspeisung:                 9.52 kWh
Netzbezug:                   3.11 kWh
  → Tagtarif:                2.14 kWh
  → Nachttarif:              0.97 kWh

Kostenberechnung:
Stromkosten (Netzbezug):     1.14 €
Einspeisevergütung:          0.78 €
Eingesparte Kosten:          6.23 €
------------------------------------------------------------
GESAMTNUTZEN:                7.01 €

Kosten ohne Solar:           7.37 €
Einsparungsquote:           95.1 %
```


## 🔧 Troubleshooting

### Häufige Probleme

**Keine Verbindung zum Wechselrichter**
- Prüfen Sie die IP-Adresse: `ping <FRONIUS_IP>`
- Stellen Sie sicher, dass die Solar API aktiviert ist
- Firewall-Einstellungen prüfen

**Hue Bridge findet keine Geräte**
- Beim ersten Start den Knopf auf der Bridge drücken
- Gerätenamen in devices.json müssen exakt mit Hue-Namen übereinstimmen
- Bridge und Geräte müssen im gleichen Netzwerk sein

**Live Display funktioniert nicht**
- Terminal unterstützt möglicherweise keine ANSI-Codes
- Mit `--no-live` auf klassische Anzeige wechseln
- Windows: Windows Terminal verwenden

**Geräte schalten zu häufig**
- Hysterese-Zeit erhöhen: `--device-hysteresis 10`
- Schwellwerte anpassen (größerer Abstand zwischen Ein/Aus)

## 📝 Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert - siehe [LICENSE](LICENSE) für Details.

---

<p align="center">
  Made with ❤️ for sustainable energy management<br>
  <sub>Optimiere deinen Eigenverbrauch und schone die Umwelt! 🌍</sub>
</p>