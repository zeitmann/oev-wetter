# ÖV-Pünktlichkeit und Wetter (Ostschweiz)

**Forschungsfrage:** Wie stark beeinflusst das Wetter die Pünktlichkeit des
öffentlichen Verkehrs in der Ostschweiz, und unterscheidet sich der Effekt
nach Verkehrsmittel (Bahn/Bus) und Tageszeit?

## Scope (Teil 1)
- Region: Kantone Thurgau, St. Gallen, Appenzell Ausserrhoden/Innerrhoden
- Verkehrsmittel: Bahn und Bus
- Zeitraum: 1. Januar bis 31. März 2026
- Quellen: Ist-Daten v2 (opentransportdata.swiss), MeteoSchweiz Open Data

## Skalierung (Ausblick)
Funktioniert die Pipeline in der Ostschweiz zuverlässig, wird geprüft, ob
sie auf weitere Kantone, die Deutschschweiz oder die ganze Schweiz
ausgebaut werden kann (insb. Datenmenge, Storage, Laufzeit).

## Projektstruktur
- `data/raw/`: Rohdaten (nicht im Repo, siehe Abschnitt Rohdaten)
- `data/sample/`: kleine Stichprobe der Daten
- `notebooks/`: Jupyter-Notebooks (Analyse, Auswertung)
- `src/`: Python-Skripte (Ingestion, Storage, Transformation)

## Setup Datenbank (Paket B)
Storage: DuckDB, Begruendung in `docs/storage_evaluation.md`, Schema in `src/schema.sql`.
Quellenprofil der Ist-Daten: `docs/quellenprofil_istdaten.md`.

```bash
pip install -r requirements.txt
# 1) Haltestellenliste Ostschweiz (TG, SG, AR, AI) aus GTFS-Fahrplan und swissBOUNDARIES3D
#    (GTFS-Zip vorher aus https://archive.opentransportdata.swiss/timetable_gtfs.htm laden)
python src/build_haltestellen.py --gtfs data/raw/stammdaten/GTFS_FP2026_20260211.zip
# 2) Ist-Daten 1.1. bis 31.3.2026 laden (laedt die Monats-Zips selbst herunter)
python src/ingest_istdaten.py --start 2026-01-01 --end 2026-03-31 --stops data/stammdaten/haltestellen_ostschweiz.csv
```

Das Skript ist idempotent: bereits geladene Tage werden uebersprungen (`--force` laedt neu).
Log: `data/raw/logs/ingest_istdaten.log` und Tabelle `ingest_log`.
Die Haltestellenliste liegt im Repo unter `data/stammdaten/haltestellen_ostschweiz.csv`,
ein gefilterter Beispieltag unter `data/sample/2026-01-15_IstDaten_ostschweiz.csv.gz`.

## Rohdaten
Die gefilterten Ist-Daten (90 Tage, Ostschweiz, Parquet, 305 MB) liegen auf OneDrive (nur mit ZHAW-Konto):
[oev-wetter-daten](https://zhaw-my.sharepoint.com/:f:/g/personal/kermoala_students_zhaw_ch/IgDMrlyl0G0qQqezxXcxQNQiAQnjVM4nKlivkW6XdSoz_R8?e=VZaW7q)
Anleitung zum Einlesen in DuckDB: `LIESMICH.md` im Ordner.
Im Repo liegt nur ein Sample unter `data/sample/`.

## Quellen
Zitierstandard: APA 7 (SML-Zitierleitfaden).
