# Quellenprofil Ist-Daten v2 (Paket B, AP 1)

Stand: 20.10.2026. Zahlen aus der Tagesdatei vom 15.1.2026 (ganze Schweiz, ungefiltert).

| Merkmal | Befund |
| --- | --- |
| Herkunft | SKI (Geschaeftsstelle Systemaufgaben Kundeninformation, SBB AG) im Auftrag des BAV, Open-Data-Plattform Mobilitaet Schweiz |
| Inhalt | Effektiv gefahrene Fahrten des Vortags: pro Fahrt und Halt Soll-Zeit und Ist-Zeit bzw. letzte Prognose. Fahrten ganz ohne Echtzeitdaten fehlen. |
| Zugang | Monatsarchiv `https://archive.opentransportdata.swiss/istdaten/{Jahr}/ist-daten-v2-{Jahr}-{Monat}.zip`, frei ohne Login |
| Abdeckung | v2 ab Juli 2025, also 1.1. bis 31.3.2026 vollstaendig (Monats-Zips 2026-01 bis 2026-03 je 1.3 bis 1.4 GB) |
| Format | CSV, Trennzeichen `;`, UTF-8, Kopfzeile; eine Datei pro Tag (`YYYY-MM-DD_IstDaten.csv`, 420 bis 650 MB) |
| Umfang | 15.1.2026: 2 603 407 Zeilen, 155 294 Fahrten, 41 260 BPUIC |
| Zeitformat | Lokalzeit ohne Zeitzone: Soll `dd.mm.yyyy HH:MM`, Ist/Prognose `dd.mm.yyyy HH:MM:SS`. Eine Tagesdatei enthaelt auch Zeiten vom Vorabend und naechsten Morgen (Betriebstag) |
| Lizenz | Nutzungsbedingungen opentransportdata.swiss, Quellenangabe Pflicht |
| Aktualisierung | taeglich (Vortag), Monatsarchiv jeweils am 1. des Folgemonats |

## Spalten (22)

`BETRIEBSTAG, FAHRT_BEZEICHNER, BETREIBER_ID, BETREIBER_ABK, BETREIBER_NAME, PRODUKT_ID, LINIEN_ID, LINIEN_TEXT, UMLAUF_ID, VERKEHRSMITTEL_TEXT, ZUSATZFAHRT_TF, FAELLT_AUS_TF, BPUIC, HALTESTELLEN_NAME, ANKUNFTSZEIT, AN_PROGNOSE, AN_PROGNOSE_STATUS, ABFAHRTSZEIT, AB_PROGNOSE, AB_PROGNOSE_STATUS, DURCHFAHRT_TF, SLOID`

`SLOID` ist neu gegenueber v1.

## Auffaelligkeiten (wichtig fuer Bereinigung durch C)

- **PRODUKT_ID** uneinheitlich: `Bus` (2.08 Mio.) und `BUS` (71 000), dazu `Zug`, `Zahnradbahn`, `Tram`, `Metro`, `Schiff`. Beim Laden wird `BUS` zu `Bus` vereinheitlicht; Zahnradbahn zaehlt zur Bahn.
- **BPUIC** ist meist 9-stellig (Haltestelle + 2 Ziffern Kante/Gleis, z. B. `850978002` = Haltestelle `8509780`). Fuer den Join mit den Haltestellen-Stammdaten gilt die 7-stellige Nummer (`bpuic_haltestelle`).
- **Prognose-Status** (Abfahrt): REAL 84 %, GESCHAETZT 5 %, PROGNOSE 4 %, UNBEKANNT unter 1 %, leer 6 %.
- **Nach dem Filter (Ostschweiz, 1.1. bis 31.3.2026)**: 17.07 Mio. Halte (Bahn 1.75 Mio., Bus 15.32 Mio.). Echte Messwerte (REAL) bei der Bahn 97 %, beim Bus nur 69 %. Das ist fuer H2 (Bahn vs. Bus) relevant.
- **Doppelte Halte**: ca. 1 900 Zeilen pro Tag sind doppelt (einmal ohne, einmal mit Prognose). Beim Laden bleibt die Zeile mit dem besten Status. Weitere Fahrten fahren dieselbe Kante mehrmals an (Ringlinien), sie bleiben als `halt_nr` 2, 3 erhalten.
- **Ausfaelle und Zusatzfahrten**: 14 400 Zeilen `FAELLT_AUS_TF = true`, 16 400 Zusatzfahrten.
- **Unplausible Ist-Zeiten**: einzelne Ist-Zeiten liegen genau einen Tag vor dem Soll (Verspaetung ca. -1440 Min.), wenige sind um Jahre verschoben. Rund 850 Halte sind mehr als 10 Min. zu frueh, 200 mehr als 60 Min. zu spaet. Diese Werte bleiben in der Datenbank unveraendert und muessen in der Bereinigung (AP 5) behandelt werden, sonst verzerren sie Mittelwerte stark.

## Quelle (APA 7)

SBB AG, Geschaeftsstelle Systemaufgaben Kundeninformation. (2026). *Ist-Daten v2* [Datensatz]. Open-Data-Plattform Mobilitaet Schweiz. https://archive.opentransportdata.swiss/actual_data_archive.htm
