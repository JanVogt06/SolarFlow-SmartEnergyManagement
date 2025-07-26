# Smart Energy Manager

<p align="center">
  <img src="assets/logo_without-background.png" alt="Smart Energy Manager Logo" width="512">
</p>

<p align="center">
  <strong>Intelligentes Energie-Management-System für Fronius Solaranlagen</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#verwendung">Verwendung</a> •
  <a href="#konfiguration">Konfiguration</a> •
  <a href="#gerätesteuerung">Gerätesteuerung</a> •
  <a href="#dokumentation">Dokumentation</a>
</p>

---

## 📋 Überblick

Der **Smart Energy Manager** ist ein Python-basiertes Energie-Management-System, das speziell für Fronius Wechselrichter entwickelt wurde. Es überwacht Ihre Solaranlage in Echtzeit und steuert elektrische Verbraucher intelligent basierend auf der verfügbaren Überschussenergie. Dies maximiert Ihren Eigenverbrauch und reduziert Ihre Stromkosten erheblich.

### 🎯 Hauptziele
- **Maximierung des Eigenverbrauchs** durch intelligente Lastverteilung
- **Kostenoptimierung** durch zeitbasierte Tarife und Einspeisevergütung
- **Automatisierung** von Verbrauchern basierend auf Solarenergie
- **Detaillierte Analyse** durch umfangreiches Logging und Statistiken

## ✨ Features

### 🌞 Solar-Monitoring
- **Echtzeit-Überwachung** aller relevanten Leistungsdaten
- Unterstützung für **Batteriespeicher** (automatische Erkennung)
- Berechnung von Eigenverbrauch, Autarkiegrad und Überschuss
- Farbcodierte Anzeige basierend auf konfigurierbaren Schwellwerten

### 🔌 Intelligente Gerätesteuerung
- **Prioritätsbasierte Steuerung** (10 Prioritätsstufen)
- Berücksichtigung von Mindest- und Maximallaufzeiten
- **Zeitbasierte Einschränkungen** (z.B. Waschmaschine nur tagsüber)
- **Hysterese-Funktionalität** verhindert häufiges Ein-/Ausschalten
- Unterstützung für beliebig viele Geräte

### 📊 Datenerfassung & Analyse
- **CSV-Logging** mit konfigurierbarem Format
- **SQLite-Datenbank** für langfristige Speicherung
- Tages-, Wochen- und Monatsstatistiken
- **Kostenberechnung** mit Tag-/Nachttarifen
- Export-Funktionen für weitere Analysen

### 💰 Kostenoptimierung
- Berechnung der eingesparten Stromkosten
- Berücksichtigung von Einspeisevergütung
- **ROI-Berechnung** (Return on Investment)
- Unterstützung für zeitbasierte Stromtarife

### 🖥️ Flexible Anzeige
- Detaillierte Konsolen-Ausgabe mit Farbunterstützung
- **Simple Mode** für kleine Displays (einzeilig)
- Periodische Tagesstatistiken
- Konfigurierbare Anzeigeschwellwerte

## 🚀 Installation

### Voraussetzungen
- Python 3.8 oder höher
- Fronius Wechselrichter mit aktivierter Solar API
- Netzwerkverbindung zum Wechselrichter

### Schnellstart

1. **Repository klonen**
   ```bash
   git clone https://github.com/yourusername/smart-energy-manager.git
   cd smart-energy-manager
   ```

2. **Abhängigkeiten installieren**
   
   Das Programm prüft automatisch beim Start, ob alle benötigten Pakete installiert sind und bietet eine automatische Installation an:
   ```bash
   python main.py
   ```
   
   Oder manuell:
   ```bash
   pip install requests
   ```

3. **Konfiguration anpassen**
   ```bash
   # IP-Adresse des Fronius Wechselrichters setzen
   python main.py --ip 192.168.178.100
   ```

## 📖 Verwendung

### Basis-Verwendung (Beispiele)

```bash
# Standard-Ausführung mit automatischer Gerätesteuerung
python main.py

# Mit spezifischer IP-Adresse
python main.py --ip 192.168.178.100

# Mit angepasstem Update-Intervall (10 Sekunden)
python main.py --interval 10

# Simple Mode für kleine Displays
python main.py --simple

# Ohne Farben (für Terminals ohne ANSI-Support)
python main.py --no-colors
```

### Erweiterte Optionen (Beispiele)

```bash
# Kostenparameter setzen
python main.py --electricity-price 0.35 --feed-in-tariff 0.08

# Logging deaktivieren
python main.py --no-logging

# Gerätesteuerung deaktivieren
python main.py --disable-devices

# Alle Optionen anzeigen
python main.py --help
```

## ⚙️ Konfiguration

### Umgebungsvariablen

Die Konfiguration kann über Umgebungsvariablen erfolgen:

```bash
export FRONIUS_IP="192.168.178.100"
export UPDATE_INTERVAL="5"
export ELECTRICITY_PRICE="0.40"
export ENABLE_DEVICE_CONTROL="True"
```

### Kommandozeilen-Argumente

Alle Konfigurationsoptionen können über Kommandozeilen-Argumente überschrieben werden:

| Kategorie | Option | Beschreibung | Standard |
|-----------|--------|--------------|----------|
| **Verbindung** | `--ip` | IP-Adresse des Wechselrichters | 192.168.178.90 |
| | `--timeout` | API-Timeout in Sekunden | 5 |
| **Timing** | `--interval` | Update-Intervall in Sekunden | 5 |
| | `--daily-stats-interval` | Statistik-Anzeigeintervall in Sekunden | 1800 (30 Min) |
| | `--device-log-interval` | Intervall für Geräte-Status-Logging in Sekunden | 60 |
| **Anzeige** | `--no-colors` | Deaktiviert farbige Ausgabe | False |
| | `--simple` | Verwendet vereinfachte Anzeige (eine Zeile) | False |
| | `--no-daily-stats` | Deaktiviert die periodische Anzeige der Tagesstatistiken | False |
| | `--surplus-display` | Überschuss Anzeige-Schwellwert in Watt | 0 |
| **Kosten** | `--electricity-price` | Strompreis in EUR/kWh | 0.40 |
| | `--electricity-price-night` | Nachtstrompreis in EUR/kWh | 0.30 |
| | `--feed-in-tariff` | Einspeisevergütung in EUR/kWh | 0.082 |
| | `--night-tariff-start` | Beginn Nachttarif | 22:00 |
| | `--night-tariff-end` | Ende Nachttarif | 06:00 |
| **Logging** | `--no-logging` | Deaktiviert CSV-Datenlogging | False |
| | `--log-file` | Pfad zur Log-Datei | solar_monitor.log |
| | `--log-level` | Log-Level (DEBUG/INFO/WARNING/ERROR) | INFO |
| | `--no-daily-stats-logging` | Deaktiviert das CSV-Logging der Tagesstatistiken | False |
| | `--no-database-logging` | Deaktiviert das Datenbank-Logging | False |
| | `--no-device-logging` | Deaktiviert das Geräte-Logging komplett | False |
| **CSV-Format** | `--csv-delimiter` | CSV Trennzeichen (,/;/\t/\|) | ; |
| | `--csv-encoding` | CSV Encoding (utf-8/latin-1/cp1252/iso-8859-1) | utf-8 |
| | `--csv-decimal` | Dezimaltrennzeichen (./,) | , |
| | `--csv-english` | Verwendet englische CSV-Header statt deutsche | False |
| | `--csv-no-info` | Keine Info-Zeile unter CSV-Header | False |
| **Verzeichnisse** | `--data-log-dir` | Hauptverzeichnis für Log-Dateien | Datalogs |
| | `--solar-data-dir` | Unterverzeichnis für Solardaten | Solardata |
| | `--daily-stats-dir` | Unterverzeichnis für Tagesstatistiken | Dailystats |
| | `--device-log-dir` | Unterverzeichnis für Geräte-Logs | Devicelogs |
| | `--database-log-dir` | Verzeichnis für Datenbank-Logs | Datalogs/solar_energy.db |
| **Schwellwerte** | `--battery-idle` | Batterie Idle-Schwellwert in Watt | 10 |
| | `--battery-soc-high` | Batterie SOC Schwellwert für grün in % | 80 |
| | `--battery-soc-medium` | Batterie SOC Schwellwert für gelb in % | 30 |
| | `--autarky-high` | Autarkie Schwellwert für grün in % | 75 |
| | `--autarky-medium` | Autarkie Schwellwert für gelb in % | 50 |
| **Gerätesteuerung** | `--disable-devices` | Deaktiviert die intelligente Gerätesteuerung | False |
| | `--device-config` | Pfad zur Gerätekonfigurationsdatei | devices.json |
| | `--device-hysteresis` | Hysterese-Zeit in Minuten für Geräteschaltungen | 5 |
| **System** | `--skip-check` | Überspringe automatische Dependency-Prüfung | False |
| | `--version` | Zeigt Versionsinformationen | - |

## 🔧 Gerätesteuerung

### Gerätekonfiguration

Geräte werden in der Datei `devices.json` konfiguriert:

```json
[
  {
    "name": "Waschmaschine",
    "description": "Waschmaschine im Keller",
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
    "name": "Poolpumpe",
    "description": "Filterpumpe für Pool",
    "power_consumption": 750,
    "priority": 7,
    "min_runtime": 60,
    "max_runtime_per_day": 480,
    "switch_on_threshold": 1000,
    "switch_off_threshold": 500,
    "allowed_time_ranges": [
      ["09:00", "18:00"]
    ]
  }
]
```

### Prioritätsstufen

| Priorität | Bezeichnung | Verwendung |
|-----------|-------------|------------|
| 1 | Kritisch | Wichtige Geräte (z.B. Kühlschrank) |
| 2-3 | Hoch | Häufig benötigte Geräte |
| 4-6 | Mittel | Standard-Verbraucher |
| 7-8 | Niedrig | Optionale Verbraucher |
| 9-10 | Optional | Nur bei viel Überschuss |

### Steuerungslogik

1. **Einschalten**: Geräte werden nach Priorität eingeschaltet, wenn genügend Überschuss vorhanden ist
2. **Hysterese**: 5 Minuten Wartezeit zwischen Schaltvorgängen (konfigurierbar)
3. **Zeitfenster**: Geräte laufen nur in erlaubten Zeiträumen
4. **Laufzeiten**: Mindest- und Maximallaufzeiten werden beachtet

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

## 🔒 Sicherheit

- Keine Authentifizierung erforderlich (lokales Netzwerk)
- Nur lesender Zugriff auf Fronius API
- Keine Steuerung des Wechselrichters
- Gerätesteuerung nur über externe Schnittstellen

## 📝 Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert. Siehe [LICENSE](LICENSE) für Details.

---

<p align="center">
  Made with ❤️ for sustainable energy management
</p>