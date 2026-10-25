# ÖV-Pünktlichkeit und Wetter (Ostschweiz)

**Forschungsfrage:** Wie stark beeinflusst das Wetter die Pünktlichkeit des
öffentlichen Verkehrs in der Ostschweiz, und unterscheidet sich der Effekt
nach Verkehrsmittel (Bahn/Bus) und Tageszeit?

## Scope (Teil 1)
- Region: Kantone Thurgau, St. Gallen, Appenzell Ausserrhoden/Innerrhoden
- Verkehrsmittel: Bahn und Bus
- Zeitraum: 1. Januar bis 31. März 2026
- Quellen: Ist-Daten v2 (opentransportdata.swiss), MeteoSchweiz Open Data

## Konzept (Paket A)
Volltext mit Problemstellung, Operationalisierung, Methodik und Limitationen: `docs/konzept.md`.
Lifecycle-Entwurf (Phasen, Unterströmungen, Serving): `docs/lifecycle.md`.

| Hypothese | Aussage |
| --- | --- |
| H1 | Bei starkem Niederschlag oder Schnee ist die mittlere Verspätung höher als sonst. |
| H2 | Der Effekt ist beim Bus stärker als bei der Bahn. |
| H3 | Der Effekt ist in der Hauptverkehrszeit stärker als ausserhalb. |

Festlegungen: Verspätung = Ankunftsverspätung pro Halt in Minuten, verspätet ab 3 Minuten (nach SBB AG, o. J.), nur gemessene Werte im Fenster −10 bis +60 Minuten; starker Niederschlag = Stundensumme über dem 90. Perzentil der Niederschlagsstunden; Hauptverkehrszeit = Mo–Fr 6–9 und 16–19 Uhr. Tests: Mann-Whitney-U (H1), Regression mit Wechselwirkung (H2, H3), α = 0,05, immer mit Effektstärke.

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
Zitierstandard: APA 7 (SML-Zitierleitfaden). Weitere Quellen und Code-Vorlagen stehen als Kommentar am Anfang der jeweiligen Datei.

**Daten**

- SBB AG, Geschäftsstelle Systemaufgaben Kundeninformation. (2026). *Ist-Daten v2* [Datensatz]. Open-Data-Plattform Mobilität Schweiz. https://archive.opentransportdata.swiss/actual_data_archive.htm
- SBB AG, Geschäftsstelle Systemaufgaben Kundeninformation. (2026). *Fahrplan 2026 (GTFS)* [Datensatz]. Open-Data-Plattform Mobilität Schweiz. https://archive.opentransportdata.swiss/timetable_gtfs.htm
- Bundesamt für Landestopografie swisstopo. (2026). *swissBOUNDARIES3D* [Datensatz]. https://www.swisstopo.admin.ch
- [MeteoSchweiz: Wetterdaten, APA-Eintrag von Paket C ergänzen, Quellenangabe laut Lizenz]

**Literatur und Werkzeuge**

- Reis, J., & Housley, M. (2022). *Fundamentals of data engineering*. O'Reilly Media.
- SBB AG. (o. J.). *So misst die SBB die Pünktlichkeit* [Webseite]. https://company.sbb.ch/de/unternehmen/verantwortung/kunden/puenktlichkeit.html
- DuckDB Foundation. (2026). *DuckDB documentation*. https://duckdb.org/docs/
