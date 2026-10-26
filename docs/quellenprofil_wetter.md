# Quellenprofil Wetter und ergänzende Höhen (Paket C, AP 1)

Stand: 26.10.2026. Quelle der Wetterdaten: MeteoSchweiz.

## Kurzer Quellenvergleich

| Kriterium | MeteoSchweiz SwissMetNet | Open-Meteo Historical Weather |
| --- | --- | --- |
| Datenart | Stationsmessungen mit Stationsmetadaten | Reanalyse-/Modelldaten, unter Einbezug von Messungen |
| Zugriff | Öffentliche CSV-Dateien über STAC | Öffentliche HTTP-API für Koordinaten |
| Auflösung | Fertige Stundenwerte, zusätzlich 10 Minuten | Stundenwerte, räumliches Modellraster |
| Eignung | Passt zur geplanten Stationszuordnung und zum vorhandenen Schema | Einfacher punktweiser Abruf, aber anderer räumlicher Ansatz |

Entscheid: **MeteoSchweiz**, weil tatsächliche Stationsmessungen und gemeinsame
Tabellen bereits vorgesehen sind. Fertige Stundenwerte vermeiden eine eigene
Aggregation aus 10-Minuten-Werten. Keine zusätzliche Wetterquelle wird gemischt.

## Quellenprofil

| Merkmal | Umsetzung / Befund |
| --- | --- |
| Herkunft | Bundesamt für Meteorologie und Klimatologie MeteoSchweiz, SwissMetNet |
| Zugang | STAC: https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-smn |
| Format | CSV, Semikolon, Windows-1252, Dezimalpunkt; Datum `dd.mm.yyyy HH:MM` |
| Zeit | UTC; Stundenzeitstempel ist das Ende des Messintervalls |
| Zeitraum | 1.1.–31.3.2026; Randtage für über Mitternacht laufende Betriebstage werden mitgeladen |
| Ablage an diesem Stand | 2026 unter `recent`; ältere Jahre unter `historical`. Das Skript prüft auch passende historische Dekaden und entfernt Überlappungen. |
| Parameter | `rre150h0`: Niederschlag in mm; `tre200h0`: Temperatur in °C; `fu3010h0`: Wind in km/h; `htoauths`: aktuelle Schneehöhe in cm |
| Metadaten | Stations-, Parameter- und Dateninventar-CSV werden unverändert mitgespeichert |
| Lizenz | Freie Nutzung; bei Weitergabe/Wiedergabe ist die Quellenangabe Pflicht: **Quelle: MeteoSchweiz** |
| Fehlwerte | Leere Werte bleiben fehlend; keine Ersetzung durch 0, keine Interpolation |

In TG, SG, AR und AI sind **13 Stationen** verzeichnet, davon keine direkt in AR.
Die Kantonsgrenze beschränkt den Stationspool, nicht die Zuordnung eines Halts innerhalb
der vier Kantone. `data/stammdaten/wetterstationen.csv` enthält die vollständige Liste.
`docs/ergebnisse/wetterqualitaet.csv` weist die tatsächlich vorhandenen Werte je
Station und Parameter aus. Quinten (QUI), Schmerikon (SCM) und Steckborn (STK)
liefern hier weder Niederschlag noch Temperatur und werden nicht zugeordnet.
Die übrigen zehn Stationen erfüllen die Mindestabdeckung von 90 % für beide Kernparameter.

Schneehöhe liegt nur für einen Teil der Stationen vor. Sie misst eine **Schneedecke**,
keinen aktuellen Schneefall. Diese Unterscheidung wird in der Auswertung beibehalten.

## Haltestellen und Höhen

Bs bestehende Haltestellenliste wird weiterverwendet. Die fehlenden Höhen wurden
für alle 2’587 Koordinaten mit dem GeoAdmin-Höhendienst von swisstopo ergänzt.
WGS84-Koordinaten werden dafür mit pyproj nach LV95 umgerechnet. Rohantworten liegen
gecacht in `data/raw/stammdaten/hoehen/`, die kleine Ergänzungstabelle unter
`data/stammdaten/haltestellen_hoehen.csv`. Es handelt sich um Gelände-, nicht um
vermessene Bahnsteig- oder Brückenhöhen.

## Quellen (APA 7)

Bundesamt für Meteorologie und Klimatologie MeteoSchweiz. (2026). *Automatische Wetterstationen: Messwerte* [Datensatz]. https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-smn

Bundesamt für Meteorologie und Klimatologie MeteoSchweiz. (2026). *Download data*. https://opendatadocs.meteoswiss.ch/general/download

Open-Meteo. (2026). *Historical Weather API*. https://open-meteo.com/en/docs/historical-weather-api

Bundesamt für Landestopografie swisstopo. (2026). *Height: GeoAdmin API* [Höhendienst]. https://api3.geo.admin.ch/services/sdiservices.html#height
