# Schema und Zeitformat: Umsetzung von B und C

Paket C verwendet die vorgeschlagenen Wetterspalten unveraendert. Massgeblich ist `src/schema.sql`.

## Zeitformat
- Alle Zeitpunkte als `TIMESTAMPTZ` (ISO 8601 mit Zeitzone, z. B. `2026-03-29T03:05:00+02:00`).
- Die Ist-Daten sind Lokalzeit (Europe/Zurich) und werden beim Laden umgerechnet; die Sommerzeitumstellung am 29.3.2026 ist damit abgedeckt.
- Betriebstag als `DATE`.
- Wetterdaten: MeteoSchweiz liefert UTC; Speicherung als `TIMESTAMPTZ`. `zeitpunkt` = Ende des Messintervalls (Stundenwert).

## Namen
- Tabellen und Spalten klein, Deutsch, `snake_case`, keine Umlaute (`verspaetung`, nicht `Verspätung`).
- Haltestellen-ID: In den Ist-Daten ist `BPUIC` meist 9-stellig (mit Kante). Fuer Joins gilt die 7-stellige Haltestellennummer: in `halt` heisst sie `bpuic_haltestelle`, in `haltestelle` und `haltestelle_station` `bpuic` (Text).
- Wetterstation-ID heisst `station_abk` (MeteoSchweiz-Kuerzel).

## Haltestellen
- Haltestellenliste der Ostschweiz: von B selbst erstellt (`src/build_haltestellen.py`, 2587 Haltestellen), liegt unter `data/stammdaten/haltestellen_ostschweiz.csv` mit den Spalten `bpuic` (7-stellig), `sloid, name, kanton, lat, lon, hoehe_m` (Hoehe noch leer; C ergaenzt sie bei Bedarf).
- Die vorgeschlagenen Wetterspalten werden von C unveraendert verwendet.

## Umsetzung Paket C (26.10.2026)
- MeteoSchweiz-Stundenwerte: `rre150h0` -> `niederschlag_mm`, `tre200h0` -> `temperatur_c`,
  `htoauths` -> `schneehoehe_cm`, `fu3010h0` -> `wind_kmh`. Einheiten entsprechen dem Schema.
- `zeitpunkt` bleibt das Ende des Messintervalls in UTC (`TIMESTAMPTZ`). Der Join verwendet
  die Soll-Ankunft im Intervall `(zeitpunkt - 1 Stunde, zeitpunkt]`.
- Fehlende Haltestellenhoehen werden aus swisstopos Gelaendemodell ergaenzt;
  separate Ergaenzungsdatei: `data/stammdaten/haltestellen_hoehen.csv`.
- `haltestelle_station`: naechste Station mit Kernparametern, maximal 30 km und 500 m Hoehendifferenz.
- Bereinigtes Ergebnis in `analyse_halt`, Stundenaggregation in `analyse_stunde`;
  beide zusaetzlich lokal unter `data/processed/` als Parquet. Details: `docs/transformation.md`.

## Dateinamen
- Ist-Daten roh gefiltert: `data/raw/istdaten/YYYY-MM-DD_IstDaten_ostschweiz.csv`
- Datenbank: `data/oev_wetter.duckdb` (nicht im Repo)
