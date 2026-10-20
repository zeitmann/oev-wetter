# Projektarbeit Teil 1: Arbeitspakete A, B, C

Stand: 20.10.2026

## Überblick

Bis zur Abgabe von Teil 1 am 27.10.2026, 23:59 Uhr, teilen wir die Arbeit in drei Pakete (A, B, C) mit je ca. 13 bis 15 Stunden auf. Jede Person übernimmt ein Paket und präsentiert den dazugehörigen Teil.

**Thema:** Beeinflusst das Wetter die Verspätungen von Bahn und Bus in der Ostschweiz, und unterscheidet sich der Effekt nach Verkehrsmittel und Tageszeit? Teil 2 ergänzt ein Web-Dashboard.

- Region: Kantone Thurgau, St. Gallen, Appenzell (AR/AI)
- Verkehrsmittel: Bahn und Bus
- Zeitraum: 1. Januar bis 31. März 2026
- Daten: Ist-Daten v2 (opentransportdata.swiss), Wetterdaten MeteoSchweiz
- Repo: [github.com/zeitmann/oev-wetter](https://github.com/zeitmann/oev-wetter)
- Abgabe: kommentierter Code, Daten und Präsentationsfolien über einen separaten Abgabe-Branch, Link in Moodle
- Kolloquium (Referat, 15 Min., Pass/Fail): 28.10. oder 4.11., 18:00 Uhr, Raum SW 111
- Bewertung: 5 Bereiche (Konzeptionalisierung, Lifecycle-Entwurf, Ingestion, Storage, Transformation Teil 1), je nach 9 Kriterien

| Paket | Inhalt | Aufwand (Schätzung) | Referatsteil (ca. 5 Min.) |
| --- | --- | --- | --- |
| A: Konzept und Rahmen | AP 2, AP 6, AP 7 | ca. 13 h | Problemstellung, Forschungsfrage, Hypothesen, Lifecycle |
| B: Daten rein | AP 1 (Ist-Daten), AP 3 (Ist-Daten), AP 4 | ca. 13 h | Ist-Daten, Ingestion, Storage, Datenmodell |
| C: Daten verknüpfen | AP 1 (Wetter, Haltestellen), AP 3 (Wetter), AP 5 | ca. 15 h | Wetterdaten, Bereinigung, Join, Resultate, Limitationen |

## Paket A: Konzept und Rahmen

Paket A legt fest, was wir untersuchen und wie, und führt am Ende alle Teile zur Abgabe zusammen. Es liefert die Operationalisierung, auf die Paket C wartet, und ist deshalb am Anfang zeitkritisch.

### AP 2: Konzeptionalisierung

- [ ] Problemstellung und Ausgangslage schreiben: Warum ist das Thema relevant, wer nutzt das Ergebnis (Pendler, ÖV-Betreiber, Planer)?
- [ ] Forschungsfrage finalisieren: Wie stark beeinflusst das Wetter die Pünktlichkeit des öV in der Ostschweiz, und unterscheidet sich der Effekt nach Verkehrsmittel und Tageszeit?
- [ ] Hypothesen ausformulieren: H1 starker Niederschlag und Schnee erhöhen die mittlere Verspätung, H2 der Effekt ist beim Bus stärker als bei der Bahn, H3 in der Hauptverkehrszeit verstärkt er sich.
- [ ] Begriffe operationalisieren und schriftlich festlegen:
    - Verspätung: Ist minus Soll in Minuten; Entscheid, ob Ankunft oder Abfahrt, und ab wie vielen Minuten ein Halt als verspätet gilt.
    - Starker Niederschlag: Schwelle in mm pro Stunde oder Quantile; dazu Schneefall und Temperatur unter 0 °C.
    - Hauptverkehrszeit: feste Zeitfenster am Morgen und Abend.
- [ ] Methodik pro Hypothese bestimmen, z. B. Rangkorrelation (Spearman) oder Gruppenvergleich (Mann-Whitney), weil Verspätungen meist schief verteilt sind; optional Regression mit Wechselwirkung. Signifikanzniveau festlegen.
- [ ] Limitationen benennen: Wetterstation ist nicht am Halt, Verspätungen haben viele Ursachen, Echtzeitdaten fehlen teilweise, der Zeitraum umfasst nur drei Monate eines einzigen Winters.

Ergebnis: 3 bis 4 Folien Konzept und ein Abschnitt im README.

### AP 6: Lifecycle-Entwurf

- [ ] Grobentwurf früh erstellen: Diagramm mit Generation, Ingestion, Storage, Transformation, Serving und den Unterströmungen (Bezeichnungen wie in den Kursfolien zum Lebenszyklus).
- [ ] Pro Phase eintragen: Quelle, Werkzeug, Entscheidung.
- [ ] Serving als Entwurf skizzieren: Web-Dashboard mit Karte, Zeitreihen und Wetterfiltern (Technologie darf noch offen sein).
- [ ] Diagramm finalisieren, sobald B den Storage-Entscheid und C die Transformationsschritte geliefert haben.

Ergebnis: 1 bis 2 Folien mit Lifecycle-Diagramm.

### AP 7: Abgabe und Präsentation

- [ ] Foliengerüst für das gesamte Referat anlegen (Problem, Hypothesen, Lifecycle, Quellen, Ingestion, Storage, Datenmodell, EDA und Bereinigung, Resultate, Limitationen). Die drei Beispielpräsentationen auf Moodle dienen als Massstab.
- [ ] Folien von B und C einsammeln und vereinheitlichen; Redezeit auf je ca. 5 Minuten aufteilen.
- [ ] README finalisieren, inklusive Rohdaten-Link.
- [ ] Quellenangaben im Code und in den Folien prüfen (APA 7 nach SML-Zitierleitfaden).
- [ ] Code-Stand abstimmen und einfrieren, dann den Abgabe-Branch erstellen; danach bleibt er unverändert.
- [ ] Prüfende (MariaPelli, vp-82) als Collaborators hinzufügen, falls das Repo privat ist.
- [ ] Branch-Link in Moodle hinterlegen (Abgabe Gruppe 4, Teil 1).
- [ ] Probelauf des Referats mit Zeitmessung (15 Minuten) mit allen drei.

### Zu berücksichtigen (Paket A)

- **Für C:** Die Operationalisierung (Verspätung, starker Niederschlag, Hauptverkehrszeit) und die Methodik pro Hypothese müssen früh feststehen, weil C sie im Hypothesentest umsetzt.
- **Von B:** Storage-Entscheid und Datenmodell fliessen in das Lifecycle-Diagramm und in die Folien ein.
- **Von C:** Resultate und Limitationen kommen erst spät. Reserviert dafür Zeit vor dem Einfrieren des Branches.
- **Engpass:** Wenn A früher fertig ist, unterstützt A Paket B bei Ingestion oder Storage, weil B auf dem kritischen Pfad liegt.
- **Referat:** Jede Person präsentiert einen eigenständigen Teil. A präsentiert Problemstellung, Forschungsfrage, Hypothesen und Lifecycle.

## Paket B: Daten rein

Paket B bringt die Ist-Daten gefiltert und wiederholbar in eine Datenbank und liegt auf dem kritischen Pfad: Ohne laufende Ingestion und Schema kann C die Daten nicht verknüpfen. Deshalb zuerst einen einzelnen Tag zum Laufen bringen, dann auf den ganzen Zeitraum skalieren.

### AP 1: Datenquelle Ist-Daten erkunden

- [ ] Datensatz Ist-Daten v2 auf opentransportdata.swiss und das Archiv finden. Prüfen, ab welchem Datum v2 verfügbar ist, ob also der 1. Januar 2026 abgedeckt ist. Falls nicht: Vorgängerdatensatz (v1) für die fehlenden Tage prüfen, die Struktur kann leicht abweichen.
- [ ] Eine Tagesdatei laden und ansehen: Spalten, Trennzeichen, Zeichencodierung, Zeitformat, Grösse (nach den Datensatzseiten grob 400 bis 620 MB pro Tag für die ganze Schweiz).
- [ ] Wichtige Spalten verstehen und dokumentieren, z. B. Betriebstag, Linie, Verkehrsmittel, Haltestelle, Soll- und Ist-Zeit, Prognose-Status (REAL, GESCHAETZT, PROGNOSE). Die genauen Namen aus der Dokumentation des Datensatzes übernehmen.
- [ ] Quellenprofil schreiben: Herkunft, Lizenz (Quellenangabe ist Pflicht), Format, Aktualisierung, Zugang, Limitationen, plus APA-Eintrag.

Ergebnis: Quellenprofil auf einer Folie und im README.

### AP 3: Ingestion Ist-Daten

- [ ] Download-Skript in `src/` für die Tagesdateien vom 1.1. bis 31.3.2026, mit Start- und Enddatum als Parameter.
- [ ] Beim Einlesen direkt filtern (in Blöcken, nicht die ganze Datei in den Speicher laden): nur Ostschweiz (TG, SG, AR, AI) und nur Bahn und Bus. Für 90 Tage ohne Filter wären es grob 35 bis 55 GB, prüft den freien Speicherplatz.
- [ ] Wiederholbar (idempotent) bauen: Bereits verarbeitete Tage werden übersprungen; erneutes Ausführen erzeugt keine Duplikate.
- [ ] Logging und Fehlerbehandlung: pro Tag Zeilen vor und nach dem Filter, Dauer, Fehler; Wiederholung bei Netzwerkfehlern; fehlende Tage dokumentieren.
- [ ] Gefilterte Rohdaten unverändert in `data/raw/` ablegen (nicht ins Repo) und 1 bis 3 Tage als Sample in `data/sample/`.
- [ ] Mit A klären, wo die vollständigen Rohdaten extern liegen (Teams, SharePoint) und den Link in der README eintragen.

Ergebnis: Skripte, Rohdaten, Beschreibung des Ablaufs für die Folien.

### AP 4: Storage

- [ ] Anforderungen aus den geplanten Abfragen ableiten: Join über Zeit und Ort, Aggregationen pro Stunde, Linie und Verkehrsmittel, spätere Abfragen für das Dashboard.
- [ ] Optionen mit Kriterien vergleichen, z. B. relational (PostgreSQL, SQLite, DuckDB) und MongoDB: Datenstruktur, Abfragen, Skalierbarkeit (auch für den Ausbau auf mehr Kantone), Setup-Aufwand, Teamkenntnisse, Eignung für Teil 2. Entscheid schriftlich begründen.
- [ ] Datenmodell entwerfen: Haltestellen, Fahrten bzw. Halte, Wetterstationen, Wettermessungen, Zuordnung Haltestelle zu Station. Schlüssel, Datentypen und Zeitzone festlegen; ER-Diagramm zeichnen.
- [ ] Implementieren: Schema anlegen, Ladeskript schreiben, Indizes für Zeit und Haltestelle setzen.
- [ ] Nachweis erbringen: Beispielabfragen (z. B. Anzahl Halte pro Tag, mittlere Verspätung pro Linie) und Setup-Anleitung im README, damit alle die Datenbank lokal nachbauen können.

Ergebnis: Evaluationstabelle, ER-Diagramm, funktionierende Datenbank, Ladeskript.

### Zu berücksichtigen (Paket B)

- **Von C:** B braucht die Liste der Ostschweizer Haltestellen (ID, Name, Koordinaten, Kanton) für den Filter. C liefert sie früh aus den Haltestellen-Stammdaten. Bis dahin kann B einen einzelnen Tag ungefiltert testen.
- **Mit C:** Schema, Spaltennamen und Zeitformat am ersten Tag abstimmen (z. B. ISO 8601 mit Zeitzone). C legt die Wetter-Spalten fest, B baut das Schema für beide Quellen.
- **Für C:** So schnell wie möglich einen Tag in die Datenbank laden, damit C Join und Analyse testen kann.
- **Für A:** Storage-Entscheid, Datenmodell und Ingestion-Ablauf fliessen in Lifecycle-Diagramm und Folien.
- **Quellen:** Code-Vorlagen und Datenquellen direkt im Code nach APA 7 angeben.
- **Referat:** B präsentiert Ist-Daten, Ingestion, Storage-Evaluation und Datenmodell.

## Paket C: Daten verknüpfen

Paket C holt die Wetter- und Haltestellendaten, verknüpft sie mit den Ist-Daten und prüft die Hypothesen. C liefert B früh die Haltestellenliste und kann mit einem einzelnen Tag arbeiten, bis B die ganze Pipeline liefert.

### AP 1: Wetter und Haltestellen erkunden

- [ ] Wetterquellen vergleichen (MeteoSchweiz Open Data mit SwissMetNet über die STAC-API, alternativ Open-Meteo) und eine auswählen. Prüfen, in welcher Kategorie die Daten von 2026 liegen und welches Format sie haben.
- [ ] Verfügbare Parameter und Auflösung klären: Niederschlag, Temperatur, Wind, Schnee; 10-Minuten- oder Stundenwerte. Nicht jede Station misst alles, das gehört in die Dokumentation.
- [ ] Stationen in TG, SG, AR und AI auflisten: ID, Name, Koordinaten, Höhe, gemessene Parameter.
- [ ] Haltestellen-Stammdaten finden und die Haltestellen der vier Kantone herausfiltern: ID, Name, Koordinaten, Kanton.
- [ ] Quellenprofile schreiben (Herkunft, Lizenz, Format, Zugang, Limitationen) mit APA-Einträgen. Bei MeteoSchweiz ist die Quellenangabe Pflicht.
- [ ] Optional: Feiertage und Schulferien als Kontrollvariable prüfen.

Ergebnis: Quellenprofile, Stationsliste, Haltestellenliste.

### AP 3: Ingestion Wetter

- [ ] Skript in `src/` für die Wetterdaten vom 1.1. bis 31.3.2026 der gewählten Stationen, mit Start- und Enddatum als Parameter.
- [ ] Wiederholbar (idempotent) bauen, mit Logging und Fehlerbehandlung; Lücken in den Messreihen dokumentieren.
- [ ] Stationsdaten (Koordinaten, Höhe) mitladen, sie werden für den räumlichen Join gebraucht.
- [ ] Zeitzone prüfen: Sind die Wetterzeiten in UTC oder Lokalzeit? Die Ist-Daten liegen in Lokalzeit.
- [ ] Rohdaten unverändert in `data/raw/` ablegen (nicht ins Repo), ein Sample in `data/sample/`.

Ergebnis: Skripte, Rohdaten, Beschreibung des Ablaufs für die Folien.

### AP 5: Transformation Teil 1

- [ ] Explorative Analyse (EDA): Verteilung der Verspätungen, fehlende Werte, Ausreisser, Anteil echter Messwerte gegenüber geschätzten und prognostizierten, aufgeteilt nach Verkehrsmittel, Kanton und Tageszeit. Kurzer Datenqualitätsbericht.
- [ ] Bereinigen: Zeitzonen und Sommerzeitumstellung (am 29.3.2026, also innerhalb des Zeitraums), Duplikate, Datentypen, unplausible Werte. Festlegen und dokumentieren, wie Fahrten ohne Echtzeitdaten und ausgefallene Fahrten behandelt werden.
- [ ] Räumlicher Join: jede Haltestelle der nächsten passenden Wetterstation zuordnen (Distanz aus Koordinaten, maximale Distanz festlegen, Höhenunterschied beachten).
- [ ] Zeitlicher Join: den Zeitpunkt jedes Halts auf den Wetter-Zeitstempel abbilden (z. B. auf die Stunde).
- [ ] Abgeleitete Variablen nach der Operationalisierung von A bilden: verspätet ja oder nein, Niederschlagsklasse, Hauptverkehrszeit.
- [ ] Hypothesentests H1 bis H3 mit der von A festgelegten Methodik durchführen. Wegen der grossen Datenmenge wird fast alles signifikant, deshalb neben dem p-Wert auch die Effektstärke angeben.
- [ ] Visualisieren und interpretieren; erste Antwort auf die Forschungsfrage formulieren und die Limitationen benennen.
- [ ] Bereinigten Datensatz so ablegen, wie mit B abgestimmt (Tabelle in der Datenbank oder Datei).

Ergebnis: kommentierte Notebooks in `notebooks/`, bereinigter Datensatz, Befunde zu H1 bis H3.

### Zu berücksichtigen (Paket C)

- **Für B:** Die Haltestellenliste der Ostschweiz zuerst liefern, B braucht sie für den Filter in der Ingestion.
- **Mit B:** Schema, Spaltennamen und Zeitformat am ersten Tag abstimmen; die Wetter-Spalten legt C fest.
- **Von A:** Operationalisierung und Methodik pro Hypothese müssen feststehen, bevor die Hypothesentests laufen. Bis dahin Join und EDA vorbereiten.
- **Von B:** Bis die Daten in der Datenbank liegen, mit einem einzelnen Tag testen.
- **Für A:** Resultate und Limitationen rechtzeitig vor dem Einfrieren des Branches liefern, sie kommen zuletzt in die Folien.
- **Quellen:** Datenquellen und Code-Vorlagen direkt im Code nach APA 7 angeben.
- **Referat:** C präsentiert Wetterdaten, Bereinigung, Join, Resultate und Limitationen.

## Übergaben und gemeinsame Regeln

Die drei Pakete hängen an fünf Übergaben; wenn eine davon hängt, wartet jemand anderes. Die Reihenfolge ist: Schema und Zeitformat zuerst, dann Haltestellenliste, dann ein Tag in der Datenbank, dann die Operationalisierung, am Ende Resultate und Folien.

| Von | An | Was | Wann |
| --- | --- | --- | --- |
| B und C | gemeinsam | Schema, Spaltennamen, Zeitformat, Dateinamen | am ersten Tag |
| C | B | Haltestellenliste der Ostschweiz (ID, Name, Koordinaten, Kanton) | so früh wie möglich |
| B | C | ein Tag in der Datenbank, dann der ganze Zeitraum | sobald die Ingestion läuft |
| A | C | Operationalisierung und Methodik pro Hypothese | vor den Hypothesentests |
| B und C | A | Storage-Entscheid, Datenmodell, Resultate, Limitationen | vor dem Einfrieren des Branches |

### Gemeinsame Regeln

- Zeitformat: ISO 8601 mit Zeitzone (Vorschlag), einheitlich in allen Tabellen. Beachten: Die Sommerzeitumstellung am 29.3.2026 liegt im Zeitraum.
- Quellen im Code: Am Dateianfang als Kommentar nach APA 7 (SML-Zitierleitfaden), auch für Code-Vorlagen.
- Ordner: `data/raw/` (nicht im Repo), `data/sample/`, `notebooks/`, `src/`.
- Rohdaten gehören nicht ins Repo; nur ein Sample, der Rest extern mit Link in der README.
- Der Abgabe-Branch wird erst am Schluss von A erstellt und danach nicht mehr verändert.

### Noch in der Gruppe zu klären

- [ ] Wer übernimmt welches Paket (A, B, C)?
- [ ] Branch-Vorgehen: auf `main` arbeiten oder je Person auf eigenem Branch?
- [ ] Konkrete Schema- und Spaltennamenkonventionen.
- [ ] Ablageort der Rohdaten (Teams, SharePoint).
- [ ] Prüfende (MariaPelli, vp-82) als Collaborators hinzufügen, falls das Repo privat bleibt.
- [ ] Kurzer Call zum Start, damit alle die Übergaben und Fristen kennen.