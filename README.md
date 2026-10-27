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
| H1 | Bei starkem Niederschlag ist die mittlere Verspätung höher als sonst. |
| H2 | Der Effekt ist beim Bus stärker als bei der Bahn. |
| H3 | Der Effekt ist in der Hauptverkehrszeit stärker als ausserhalb. |

H1 wird mit starkem Niederschlag getestet, Schnee/Frost (Schneedecke oder Niederschlag bei Frost) läuft als ergänzende Variable mit.

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
Im selben Ordner liegt das Datenpaket von Paket C, `paket_c_daten.zip` (148 MB): Wetter- und Höhenrohdaten, Stammdaten sowie die bereinigten Ergebnisse `analyse_halt.parquet` und `analyse_stunde.parquet`. Aufbau und Nachbau: `LIESMICH_PAKET_C.txt` im Archiv.
Im Repo liegt nur ein Sample unter `data/sample/`.

Die vollständigen, ungefilterten Rohdaten sind öffentlich und ohne Login verfügbar:
- Ist-Daten v2 (Monatsarchive, ganze Schweiz): https://archive.opentransportdata.swiss/actual_data_archive.htm.
  `src/ingest_istdaten.py` lädt sie selbst herunter (siehe Abschnitt Setup Datenbank).
- Wetter (MeteoSchweiz SwissMetNet): https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-smn.
  `src/ingest_wetter.py` lädt sie selbst herunter.
- Fahrplan GTFS und swissBOUNDARIES3D für die Haltestellenliste: siehe Abschnitt Quellen.

## Wetter, Transformation und Analyse (Paket C)

Vorhandene Übergabe von B verwenden: `halt.zip` nach `data/raw/paket-b-daten/`
entpacken (`halt/betriebstag=.../*.parquet`), `haltestelle.parquet` und
`ingest_log.parquet` daneben ablegen. Die Ist-Daten müssen nicht neu heruntergeladen werden.

```bash
pip install -r requirements.txt
python src/load_paket_b.py
python src/ingest_wetter.py --start 2026-01-01 --end 2026-03-31
python src/build_haltestellen_hoehen.py
python src/transform.py --start 2026-01-01 --end 2026-03-31
python src/analyse.py
python -m unittest discover -s tests -v
```

Eine virtuelle Umgebung (z. B. `.venv/`) wird nicht versioniert.
Die Skripte sind wiederholbar: B-Tabellen werden übersprungen, Wetterdaten anhand
ihres Schlüssels ersetzt und Analyseergebnisse neu aufgebaut. `--force` lädt die
jeweilige Quelle neu. Für Wetter und Höhen ist beim ersten Lauf Internet nötig.

Ausgeführte Notebooks: `notebooks/01_bereinigung_join.ipynb` und
`notebooks/02_hypothesen.ipynb`. Sie zeigen Methodik, Datenqualität und Ergebnisse;
die wiederverwendbaren Schritte liegen wie bei Paket B in `src/`.

### Notebooks auf einem anderen Rechner ausführen

Python 3.12 verwenden und `pip install -r requirements.txt` ausführen.
Anschliessend mit **demselben Python** den im Notebook eingetragenen Kernel anlegen:

```bash
python -m ipykernel install --user --name oev-wetter --display-name "Python (oev-wetter)"
```

In VS Code oder Jupyter den Kernel **Python (oev-wetter)** auswählen und zuerst
`01_bereinigung_join.ipynb`, danach `02_hypothesen.ipynb` ausführen. In VS Code kann
alternativ direkt die Python-Umgebung mit den installierten Abhängigkeiten gewählt werden.
Die gespeicherten Ausgaben sind auch ohne erneute Berechnung lesbar. Die getesteten
Paketversionen stehen unter `docs/ergebnisse/umgebung.txt`.

### Präsentation und Datenübergabe

Fertige Folien für C: `docs/präsentation/folien_paket_c.pptx` mit Sprechernotizen und
`docs/präsentation/folien_paket_c.pdf`. Fünf Vortragsfolien für etwa fünf Minuten, dazu eine
Quellenfolie im Anhang. Sie können in die gemeinsame Präsentation übernommen werden.
Optional neu erzeugen: `pip install python-pptx` und `python src/build_folien.py`.
Der PDF-Export stammt aus PowerPoint.

Das Datenpaket `data/processed/paket_c_daten.zip` ist für die externe Übergabe fertig.
Es enthält die vollständigen Wetter-/Höhenquellen und bereinigten Ergebnisse, aber
nicht erneut Bs bereits separat bereitgestellte Ist-Daten. Archiv in die Projektwurzel
entpacken; die enthaltene LIESMICH erläutert die Struktur. Das Archiv liegt im OneDrive-Ordner
`oev-wetter-daten` (Link im Abschnitt «Rohdaten», nur mit ZHAW-Konto).

- Wetterquelle und Vergleich: `docs/quellenprofil_wetter.md`.
- Bereinigung, Zuordnung und Definitionen: `docs/transformation.md`.
- Ergebnisse, Limitationen und Folienvorlage: `docs/uebergabe_paket_c.md`.
- Kleine Ergebnistabellen und Grafiken: `docs/ergebnisse/`.
- Bereinigte Daten: Tabelle `analyse_halt` in `data/oev_wetter.duckdb` und
  `data/processed/analyse_halt.parquet` (lokal, nicht im Repo).
- Stundenaggregation für Teil 2: `analyse_stunde`, ebenso als Parquet.

Stand der Auswertung: 11’626’929 Halte mit Wetterzuordnung. Bei starkem Niederschlag
liegt die mittlere Ankunftsverspätung um 0,221 Minuten höher. H2 (stärkerer Effekt
beim Bus) wird nicht gestützt; H3 (stärker in der HVZ) zeigt die entgegengesetzte
Richtung. Das sind Zusammenhänge im untersuchten Zeitraum, keine Kausaleffekte.
Die Roh- und Analysedaten von Paket C liegen als `paket_c_daten.zip` im OneDrive-Ordner
`oev-wetter-daten` (unveränderte Wetter-/Höhenquellen, bereinigte Parquet-Dateien und LIESMICH).

## Präsentation Kolloquium (Teil 1)

Gesamtpräsentation der Gruppe: `docs/präsentation/praesentation_gruppe4_teil1.pptx` (mit Sprechernotizen)
und `docs/präsentation/praesentation_gruppe4_teil1.pdf`. Ablauf: Paket A (Timon, Folien 1–6),
Paket B (Aladin, Folien 7–12), Paket C (Enis, Folien 13–17), Ausblick (Folie 18), danach Anhang
mit Quellen und möglichen Fragen. Je ca. 5 Minuten pro Person, danach 7 Minuten Diskussion.
Die Einzelfolien liegen daneben (`folien_paket_a/b/c`). Neu erzeugen:

```bash
pip install python-pptx
python src/build_folien_paket_a.py
python src/build_folien_paket_b.py
python src/build_folien.py
python src/build_praesentation.py
```

## Quellen
Zitierstandard: APA 7 (SML-Zitierleitfaden). Weitere Quellen und Code-Vorlagen stehen als Kommentar am Anfang der jeweiligen Datei.

**Daten**

- SBB AG, Geschäftsstelle Systemaufgaben Kundeninformation. (2026). *Ist-Daten v2* [Datensatz]. Open-Data-Plattform Mobilität Schweiz. https://archive.opentransportdata.swiss/actual_data_archive.htm
- SBB AG, Geschäftsstelle Systemaufgaben Kundeninformation. (2026). *Fahrplan 2026 (GTFS)* [Datensatz]. Open-Data-Plattform Mobilität Schweiz. https://archive.opentransportdata.swiss/timetable_gtfs.htm
- Bundesamt für Landestopografie swisstopo. (2026). *swissBOUNDARIES3D* [Datensatz]. https://www.swisstopo.admin.ch
- Bundesamt für Meteorologie und Klimatologie MeteoSchweiz. (2026). *Automatische Wetterstationen: Messwerte* [Datensatz]. https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-smn (Quelle: MeteoSchweiz).
- Bundesamt für Landestopografie swisstopo. (2026). *Height: GeoAdmin API* [Höhendienst]. https://api3.geo.admin.ch/services/sdiservices.html#height

**Literatur und Werkzeuge**

- Reis, J., & Housley, M. (2022). *Fundamentals of data engineering*. O'Reilly Media.
- SBB AG. (o. J.). *So misst die SBB die Pünktlichkeit* [Webseite]. https://company.sbb.ch/de/unternehmen/verantwortung/kunden/puenktlichkeit.html
- DuckDB Foundation. (2026). *DuckDB documentation*. https://duckdb.org/docs/
