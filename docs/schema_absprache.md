# Schema und Zeitformat: Vorschlag von B an C

Bitte bestaetigen oder Aenderungen hier eintragen. Massgeblich ist danach `src/schema.sql`.

## Zeitformat
- Alle Zeitpunkte als `TIMESTAMPTZ` (ISO 8601 mit Zeitzone, z. B. `2026-03-29T03:05:00+02:00`).
- Die Ist-Daten sind Lokalzeit (Europe/Zurich) und werden beim Laden umgerechnet; die Sommerzeitumstellung am 29.3.2026 ist damit abgedeckt.
- Betriebstag als `DATE`.
- Wetterdaten: C prueft, ob MeteoSchweiz UTC liefert, und speichert sie ebenfalls als `TIMESTAMPTZ`. Vorschlag: `zeitpunkt` = Ende des Messintervalls (Stundenwert).

## Namen
- Tabellen und Spalten klein, Deutsch, `snake_case`, keine Umlaute (`verspaetung`, nicht `Verspätung`).
- Haltestellen-ID heisst ueberall `bpuic` (Text, weil v2 auch SLOIDs enthaelt).
- Wetterstation-ID heisst `station_abk` (MeteoSchweiz-Kuerzel).

## Was B von C braucht
- Haltestellenliste der Ostschweiz als CSV: `bpuic, sloid, name, kanton, lat, lon, hoehe_m`, Ablage `data/stammdaten/haltestellen_ostschweiz.csv`.
- Die Wetterspalten in `wettermessung` sind ein Vorschlag; C legt sie fest.

## Dateinamen
- Ist-Daten roh gefiltert: `data/raw/istdaten/YYYY-MM-DD_IstDaten_ostschweiz.csv`
- Datenbank: `data/oev_wetter.duckdb` (nicht im Repo)
