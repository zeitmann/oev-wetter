# Übergabe Paket C an Paket A und B

Enis · Gruppe 4 · Stand: 26.10.2026, Status der Abgabe aktualisiert am 27.10.2026 (Timon) · Teil 1

## Was umgesetzt ist

MeteoSchweiz-Stundenwerte für Januar–März 2026 (inklusive Randtagen),
Haltestellenhöhen, EDA/Bereinigung, räumlicher und zeitlicher Join sowie H1–H3.
DuckDB, bestehende Spaltennamen und Bs Ingestion-Muster werden weiterverwendet.
Es wurde keine zusätzliche Datenbank oder Dashboard-Infrastruktur eingeführt.

## Datenqualität und Bereinigung

| Schritt | Ausgeschlossene / verbleibende Halte |
| --- | ---: |
| B liefert | 17’073’238 |
| Ankunft/Zeitdifferenz fehlt | −1’036’477 |
| Kein gemessener Ankunftswert | −4’361’986 |
| Ausfall (nach vorigen Filtern) | −904 |
| Durchfahrt (nach vorigen Filtern) | −195 |
| Unplausible Verspätung | −2’504 |
| Bereinigt vor Wetterzuordnung | 11’671’172 |
| Keine geeignete Wetterstation | −44’243 |
| **Final mit Wetter** | **11’626’929** |

Die Ausschlüsse werden der Reihe nach gezählt. Beispielsweise stehen die 904 Ausfälle
nicht für sämtliche Ausfälle der Rohdaten. Ankunftsstatus REAL vor Bereinigung:
**Bahn 89,72 %, Bus 65,94 %**. Die Anteile enthalten auch Halte ohne Soll-Ankunft
und sind deshalb nicht mit dem Anteil innerhalb auswertbarer Ankünfte gleichzusetzen.
Details: CSV-Dateien `qualitaet_*`, `bereinigung.csv`, `join_bilanz.csv`.

13 Wetterstationen im Untersuchungsgebiet, 10 mit geeigneten Kernparametern.
2’540 von 2’587 Haltestellen innerhalb 30 km und 500 m Höhendifferenz zugeordnet.
Für die zugeordneten, bereinigten Halte fehlen keine Kern-Wetterwerte.
Die Niederschlagsschwelle beträgt **> 1,7 mm pro Stunde**.

## Befunde zu H1–H3

| Hypothese | Ergebnis | Interpretation |
| --- | --- | --- |
| H1: mehr Verspätung bei starkem Niederschlag | 1,613 statt 1,393 Min.; **+0,221 Min. ≈ 13,2 Sek.**; rang-biserial r = 0,070; p < 0,001 | Richtung gestützt, kleiner Zusammenhang |
| H2: stärker beim Bus | Bus +0,212 Min., Bahn +0,214 Min.; Interaktion **−0,0017 Min.**, 95%-KI [−0,0299; 0,0264], p = 0,904 | Nicht gestützt |
| H3: stärker in der HVZ | HVZ +0,208 Min., NVZ +0,268 Min.; Interaktion **−0,0603 Min.**, 95%-KI [−0,0816; −0,0389], p < 0,001 | Nicht gestützt; beobachtete Richtung umgekehrt |

Bei starkem Niederschlag sind **15,50 %** der Halte mindestens drei Minuten verspätet,
gegenüber **12,36 %** sonst: rund **+3,14 Prozentpunkte**. Der Vergleich umfasst
137’355 Halte mit starkem Niederschlag und 11’489’574 sonstige Halte.

Ergänzend Schnee/Frost: +0,029 Min. ≈ 1,7 Sek., rang-biserial r = 0,014,
p < 0,001. Dieser schwache Zusammenhang betrifft je nach Station vorhandene
Schneedecke oder Niederschlag bei Frost, **keine einheitlich gemessene Schneefallvariable**.

Antwort auf die Forschungsfrage: Im untersuchten Winterquartal hängt starker
Niederschlag mit etwas höheren Ankunftsverspätungen zusammen. Eine stärkere
Wirkung beim Bus oder in der HVZ zeigen diese Auswertungen nicht. Die insgesamt
höhere Verspätung während der HVZ ist von einer Verstärkung des Wettereffekts
zu unterscheiden. Die Daten belegen keine Kausalität.

## Limitationen

- 90 Tage eines Winters; keine Verallgemeinerung auf andere Jahre/Jahreszeiten.
- Halte derselben Fahrt teilen Ursachen und sind nicht unabhängig. Die Tests
  verwenden wie vereinbart Halt-Ebene und klassische Standardfehler; p-Werte und
  Konfidenzintervalle können zu optimistisch sein. Effektgrösse stärker gewichten.
- Messlücken in den ÖV-Daten sind beim Bus deutlich häufiger; Ausfälle und
  unplausible Extremverspätungen sind ausgeschlossen. Es wird die Pünktlichkeit
  beobachteter, auswertbarer Halte untersucht, nicht die gesamte Zuverlässigkeit.
- Stationen repräsentieren das Wetter am Halt nur näherungsweise. Gelände-/Stationshöhe
  und Distanzgrenzen verbessern die Zuordnung, ersetzen keine Messung vor Ort.
- 47 Haltestellen ohne geeignete Station; stationäre Niederschlags-/Temperaturparameter
  fehlen bei drei der 13 Stationen vollständig. Keine automatische Auffüllung.
- Schneeindikatoren unterscheiden sich nach Station; Schneehöhe ist kein Schneefall.
- Baustellen, Störungen, Nachfrage, lokale Wetterlagen und Schulferien werden nicht
  kontrolliert. Kommunale Feiertage und zusätzliche betriebliche Ruhetage fehlen.

## Dateien und Übergabe an A

- Quellenprofil/Parameter: `docs/quellenprofil_wetter.md`.
- Verfahrensbeschreibung: `docs/transformation.md`; Spalten wie `src/schema.sql`.
- Ausgeführte Notebooks: `notebooks/01_bereinigung_join.ipynb`, `02_hypothesen.ipynb`.
- Grafiken und exakte Kennzahlen: `docs/ergebnisse/`.
- Fertige Vortragsfolien: `docs/präsentation/folien_paket_c.pptx` mit Sprechernotizen und
  `docs/präsentation/folien_paket_c.pdf` (fünf Vortragsfolien plus Quellenanhang).
- Bereinigte Daten: DuckDB-Tabellen `analyse_halt`, `analyse_stunde`, zusätzlich
  `data/processed/analyse_halt.parquet` und `analyse_stunde.parquet` (nicht im Repo).
- Nachbau: Befehle im README. Wetter-/Höhenrohdaten und abgeleitete Vollbestände
  liegen als `paket_c_daten.zip` (Quellen, Ergebnisse und LIESMICH) im OneDrive-Ordner
  `oev-wetter-daten`, Link im README.
- APA-Quellen in README und Code ergänzt; Lifecycle mit Umsetzung von C aktualisiert.
- Paket C ist in `main` (Pull Request #4, 27.10.2026).

## Abschluss der Gruppenabgabe

1. Erledigt (27.10.2026): C-Datenpaket liegt im gemeinsamen OneDrive-Ordner
   `oev-wetter-daten`, der Link steht im README. Zugriff mit ZHAW-Konto geprüft.
2. Erledigt (27.10.2026): Projektdateien von C sind gepusht und in `main` gemergt
   (Pull Request #4); Vollbestände unter `data/raw/` und `data/processed/` bleiben
   ausserhalb von Git.
3. Teilweise erledigt: Die Folien von A und C liegen in `docs/präsentation/`
   (`folien_paket_a.*`, `folien_paket_c.*`, im gleichen Stil). Offen: Folien von B,
   die gemeinsame Reihenfolge und die Gesamtredezeit von 15 Minuten (Kolloquium 4.11.2026).
4. Offen: A erstellt den Abgabe-Branch erst aus dem vollständigen Stand von `main`.
   Danach den Stand nicht mehr verändern.
5. Offen: A hinterlegt den Branch-Link in Moodle (Frist 27.10.2026, 23:59) und prüft
   den Zugriff auf Code, Daten und Präsentation.

Die Einrichtung des Notebook-Kernels für andere Rechner steht jetzt im README.

## Folienvorlage für ca. fünf Minuten

**Folie 1 — Wetterdaten und Zuordnung (ca. 50 Sek.)**

Quelle: MeteoSchweiz SwissMetNet, fertige Stundenwerte in UTC. 13 Stationen,
10 geeignet; Zuordnung nach Distanz und Höhe, 2’540 Haltestellen.
Zeitlicher Join nach Soll-Ankunft und Ende des Wetterintervalls.

**Folie 2 — Bereinigung und Datenqualität (ca. 55 Sek.)**

17,07 Mio. → 11,63 Mio. Halte. Nur gemessene Ankünfte, keine Ausfälle/Durchfahrten,
−10 bis +60 Minuten. Unterschiedliche REAL-Anteile bei Bahn und Bus.
Grafik: `docs/ergebnisse/verspaetungsverteilung.png`.

**Folie 3 — H1 und H2 (ca. 75 Sek.)**

Starker Niederschlag: +13 Sekunden, Verspätungsanteil +3,14 Prozentpunkte.
Bus und Bahn zeigen fast denselben Unterschied.
Grafik: `wetter_verkehrsmittel.png`; Kennzahlen aus Tabelle oben.

**Folie 4 — H3: Hauptverkehrszeit (ca. 1 Min.)**

HVZ verstärkt den Wettereffekt nicht: +0,208 Min. gegenüber +0,268 Min. in der NVZ.
Höhere allgemeine Verspätung ist nicht dasselbe wie ein stärkerer Wettereffekt.
Grafik: `wetter_hvz.png`.

**Folie 5 — Einordnung und Grenzen (ca. 1 Min.)**

Kleiner beobachteter Wetterzusammenhang, keine Kausalität. Fehlende Echtzeitwerte,
abhängige Halte, räumliche Näherung, ein Winter. Bereinigte Tabellen und
Stundenaggregation liegen für Teil 2 vor.

Quellen auf den Folien: MeteoSchweiz (2026), SBB/SKI (2026), swisstopo (2026);
vollständige APA-Einträge in README und Quellenprofil.
Die sechste Folie enthält den Quellenanhang und zählt nicht zur Vortragszeit.
