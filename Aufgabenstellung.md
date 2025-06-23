# Abschlussprojekt: Smart Energy Manager

## Aufgabenstellung:

Mit der zunehmenden Verbreitung von Photovoltaik-Anlagen und steigenden Strompreisen wird es immer wichtiger, den selbst erzeugten Solarstrom optimal zu nutzen. Ein intelligentes Energie-Management-System kann dabei helfen, elektrische Verbraucher automatisch dann einzuschalten, wenn genügend Überschussenergie vorhanden ist, und diese bei Bedarf wieder abzuschalten. Dies maximiert den Eigenverbrauch und reduziert die Stromkosten erheblich.

Implementiert mit Python ein intelligentes Energie-Management-System, das auf dem bereits vorhandenen Fronius Solar Monitor aufbaut. Das System soll Geräte basierend auf der verfügbaren Solarenergie automatisch steuern können. Im Einzelnen soll das Programm folgendes leisten können:

### Kernfunktionalitäten:
* **Solar-Monitoring**:
  - Echtzeit-Abfrage der Leistungsdaten vom Fronius Wechselrichter über die Solar API
  - Berechnung von Eigenverbrauch, Autarkiegrad und verfügbarem Überschuss 
  - Anzeige von PV-Erzeugung, Hausverbrauch, Netzeinspeisung/Bezug 
  - Unterstützung für Batteriespeicher

* **Geräte-Verwaltung**: Das System soll verschiedene Geräte mit ihren Eigenschaften verwalten können:
  - Name und Beschreibung des Geräts
  - Leistungsaufnahme in Watt
  - Prioritätsstufe (1-10, wobei 1 die höchste Priorität ist)
  - Minimale Laufzeit (wenn eingeschaltet)
  - Maximale Laufzeit pro Tag
  - Einschalt-Schwellwert (minimaler Überschuss)
  - Ausschalt-Schwellwert (kann vom Einschalt-Schwellwert abweichen)

* **Intelligente Steuerlogik**: 
  - Geräte werden basierend auf dem verfügbaren Überschuss und ihrer Priorität ein- oder ausgeschaltet
  - Hysterese-Funktionalität, um häufiges Ein-/Ausschalten zu vermeiden
  - Berücksichtigung von Mindest- und Maximallaufzeiten
  - Zeitbasierte Einschränkungen (z.B. Waschmaschine nur zwischen 8:00 und 20:00 Uhr)

* **Erweiterte Solar-Datenanalyse**:
  - Wetterbasierte Prognose (optional über externe Wetter-API)
  - Tagesstatistiken über optimierten Eigenverbrauch

* **Datenlogging und Statistik**:
  - Erstellung eines CSV-Loggings
  - Tages-/Wochen-/Monatsstatistiken über Eigenverbrauchsoptimierung
  - Berechnung der eingesparten Stromkosten