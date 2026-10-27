# Transformation Teil 1 (Paket C, AP 5)

Stand: 26.10.2026. Definitionen aus `docs/konzept.md`; Umsetzung in
`src/transform.py` und `src/analyse.py`, ausgeführte Darstellung in `notebooks/`.

## Ingestion und Wiederholbarkeit

Bs Parquet-Übergabe wird mit `load_paket_b.py` übernommen; vorhandene B-Tabellen
werden übersprungen. `--force` ersetzt sie vollständig, Wetter-Logs bleiben erhalten.
`ingest_wetter.py` verwendet dieselben Muster wie B: CLI mit Start-/Enddatum,
unveränderte Rohdateien, begrenzte Wiederholungen bei Downloadfehlern, `.part`-Dateien,
Logfile und gemeinsames DuckDB-Schema. Bereits vorhandene Rohdateien werden wiederverwendet;
`--force` lädt sie neu. Messungen werden anhand `(station_abk, zeitpunkt)` ersetzt,
dadurch entstehen keine Duplikate. Fehler landen im Log und brechen den Lauf ab;
ein unvollständiger Stationsabruf wird nicht als erfolgreicher Gesamtlauf gespeichert.

## Bereinigung und Datenqualität

EDA erfolgt **vor** dem Filtern, nach Verkehrsmittel, Kanton und lokaler Stunde.
Fehlende Ankunft, Ankunftsstatus, Ausfälle, Durchfahrten und Ausreisser werden gezählt.
Bs Abfahrtsquoten werden nicht als Ankunftsquoten übernommen.

Die Ausschlüsse sind sequenziell und überschneidungsfrei: fehlende Ankunft/Zeitdifferenz,
kein `REAL`, Ausfall, Durchfahrt, Verspätung ausserhalb −10 bis +60 Minuten,
fehlende Haltestelle. Bereits von B behandelte Duplikate werden nicht erneut anhand
von Fahrt und Haltestelle gelöscht: wiederholte Halte einer Ringlinie sind gültig.
Quelldaten bleiben erhalten; `analyse_halt` wird neu erzeugt.

## Räumlicher Join

Die nächste **geeignete** Station wird über die Haversine-Distanz (WGS84) bestimmt:
mindestens 90 % der erwarteten Stunden mit Niederschlag und Temperatur,
maximal **30 km** Entfernung und **500 m** absolute Höhendifferenz. Das sind
transparente Projektgrenzen, keine meteorologisch validierten Schwellen:
30 km begrenzt die Extrapolation im dünneren Stationsnetz, 500 m vermeidet grobe
Fehlzuordnungen zwischen Tal und Hochgebirge. Beide Grenzen sind CLI-Parameter.
Stunden-Erwartungswerte berücksichtigen den 23-Stunden-Tag am 29.3.2026.

Alle 2’587 Haltestellen werden geprüft, 2’540 zugeordnet, 47 bleiben ohne geeignete
Station. Keine Zuordnung über eine ungeeignete Station oder automatische Auffüllung.
IDs bleiben Text: `halt.bpuic_haltestelle = haltestelle_station.bpuic`.
Ergebnis: Tabelle `haltestelle_station`, zusätzlich kleine CSV derselben Zuordnung.

## Zeitlicher Join und Merkmale

- Alle Vergleiche in UTC mit `TIMESTAMPTZ`; Bs bereits normalisierte Zeiten werden
  nicht erneut lokalisiert. Tageszeit/Wochentag werden mit `Europe/Zurich` bestimmt.
- Zuordnung nach **Soll-Ankunft**: Wetterstunde mit Intervall `(t−1h, t]`.
  Beispiel: 10:30 UTC → Wetterzeit 11:00 UTC; genau 10:00 UTC → 10:00 UTC.
  Für diese rückblickende Zusammenhangsanalyse ist der Stundenendwert geeignet;
  für eine Echtzeitprognose wäre er zum Haltzeitpunkt noch nicht vollständig bekannt.
- `verspaetet`: Ankunftsverspätung ≥ 3 Minuten.
- `starker_niederschlag`: strikt über dem 90. Perzentil aller positiven
  Niederschlagsstunden der geeigneten Stationen im gesamten gewählten Zeitraum.
  Schwelle für den finalen Lauf: **1,7 mm**. Berechnung **vor** dem Halt-Join.
- Klassen: trocken = 0; mässig = > 0 bis einschliesslich Schwelle; stark = darüber.
- `schnee_frost`: vorhandene Schneehöhe > 0 hat gemäss A Vorrang (Schneedecke);
  sonst Ersatzindikator Niederschlag > 0 und Temperatur < 0 °C.
  `schnee_definition` hält die unterschiedliche Bedeutung fest. Keine Aussage über
  beobachteten aktuellen Schneefall aus der Schneehöhe ableiten.
- HVZ: Montag–Freitag, [06:00,09:00) und [16:00,19:00) lokal, kantonale gesetzliche
  Feiertage ausgenommen (`holidays`, Kategorie PUBLIC). Die verwendeten Feiertage
  stehen in `data/stammdaten/feiertage.csv`. Kommunale Sonderregelungen,
  Schulferien und zusätzliche betriebliche Ruhetage werden nicht modelliert.
- Fehlende Stationen oder Kernmesswerte werden in `join_bilanz.csv` ausgewiesen;
  sie werden nicht als trocken klassifiziert und gelangen nicht in `analyse_halt`.

## Statistik und Ergebnisablage

H1: zweiseitiger Mann-Whitney-U-Test mit Bindungskorrektur (asymptotisch),
rang-biseriale Korrelation `2U/(n1*n0)-1`, Differenz der Mittelwerte und
Verspätungsanteile. Der Rangtest prüft Verteilungsunterschiede, nicht direkt die
Gleichheit der Mittelwerte; deshalb werden die Mittelwerte zusätzlich berichtet.
Schneedecke/Frostniederschlag wird ergänzend nach demselben Vorgehen ausgewertet.

H2/H3: getrennte Gruppenvergleiche und je eine lineare Regression auf **allen**
bereinigten Halten, ohne Stichprobe: `Verspätung ~ 1 + Starkregen + Gruppe +
Starkregen*Gruppe`, einmal Gruppe Bus (Referenz Bahn), einmal HVZ (Referenz NVZ).
Berichtet werden Interaktionskoeffizient und klassisches 95%-Konfidenzintervall.
α = 0,05. Halte sind abhängig; klassische p-Werte/Intervalle unterschätzen unter
Umständen die Unsicherheit und werden vorsichtig interpretiert. Ein als 0
gespeicherter p-Wert bedeutet numerischen Unterlauf, nicht eine Wahrscheinlichkeit von exakt null.

`analyse_halt` enthält die bereinigten Halte samt Zuordnung/Merkmalen;
`analyse_stunde` aggregiert nach UTC-Stunde, Linie, Verkehrsmittel, Kanton, Station,
HVZ und Wetterklasse. Beide liegen in DuckDB und als lokale Parquet-Dateien in
`data/processed/`. Die Auswertung auf Halt-Ebene bleibt die festgelegte Hauptanalyse.
Die Stundenaggregation bereitet Teil 2 vor; ein weiterer Kontrolltest ist optional.

## Quellen (APA 7)

Wallroth, T. (2026). *Konzeptionalisierung (AP 2)*. Projektinterne Dokumentation, `docs/konzept.md`.

DuckDB Foundation. (2026). *DuckDB documentation*. https://duckdb.org/docs/

The SciPy community. (2026). *scipy.stats.mannwhitneyu*. https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.mannwhitneyu.html

Seabold, S., & Perktold, J. (2010). Statsmodels: Econometric and statistical modeling with Python. *Proceedings of the 9th Python in Science Conference*.

Vacanza contributors. (2026). *Switzerland: holidays documentation*. https://holidays.readthedocs.io/en/latest/auto_gen_docs/switzerland/
