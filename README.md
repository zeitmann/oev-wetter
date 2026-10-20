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

```bash
pip install -r requirements.txt
# Test: ein Tag, nur Bahn/Bus, ohne Haltestellenfilter
python src/ingest_istdaten.py --start 2026-01-15 --end 2026-01-15 --no-stop-filter
# ganzer Zeitraum, gefiltert auf die Ostschweiz
python src/ingest_istdaten.py --start 2026-01-01 --end 2026-03-31 --stops data/stammdaten/haltestellen_ostschweiz.csv
```

Das Skript ist idempotent: bereits geladene Tage werden uebersprungen (`--force` laedt neu).
Log: `data/raw/logs/ingest_istdaten.log` und Tabelle `ingest_log`.

## Rohdaten
Die vollständigen Rohdaten liegen extern: <Link folgt>
Im Repo liegt nur ein Sample unter `data/sample/`.

## Quellen
Zitierstandard: APA 7 (SML-Zitierleitfaden).
