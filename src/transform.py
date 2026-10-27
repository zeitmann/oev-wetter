"""Paket C: Datenqualitaet, Bereinigung und Wetter-Join in DuckDB.

Quellen (APA 7):
Wallroth, T. (2026). Konzeptionalisierung (AP 2). docs/konzept.md (Projektintern).
DuckDB Foundation. (2026). DuckDB documentation. https://duckdb.org/docs/
MeteoSchweiz. (2026). Download data. https://opendatadocs.meteoswiss.ch/general/download
Vacanza contributors. (2026). holidays documentation. https://holidays.readthedocs.io/
"""
import argparse
import json
from datetime import date
from pathlib import Path

import duckdb
import holidays
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'docs/ergebnisse'
# MeteoSchweiz-Stundenwerte sind rechts geschlossen: (t-1h, t].
WETTER_STUNDE = """date_trunc('hour',h.an_soll) + CASE
    WHEN h.an_soll=date_trunc('hour',h.an_soll) THEN INTERVAL '0 hour'
    ELSE INTERVAL '1 hour' END"""


# Hilfsfunktion: SQL ausfuehren und das Ergebnis als kleine CSV in docs/ergebnisse ablegen.
def save_query(con, sql, name):
    frame = con.execute(sql).df()
    frame.to_csv(OUT / f'{name}.csv', index=False)
    return frame


# Ablauf: Hoehen ergaenzen -> EDA -> Bereinigung -> Stationszuordnung (raeumlicher Join)
# -> Schwelle starker Niederschlag -> Feiertage -> zeitlicher Join -> Ergebnistabellen.
def transform(start, end, db, max_distanz=30.0, max_hoehendiff=500.0):
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db))
    try:
        # Alle Zeitvergleiche in UTC; Tageszeit und Wochentag werden spaeter aus Europe/Zurich abgeleitet.
        con.execute("SET TimeZone='UTC'")
        con.execute('SET threads=4')
        con.execute('SET memory_limit=\'4GB\'')
        # Untersuchungszeitraum als Parameter-Tabelle, damit alle Abfragen denselben Zeitraum nutzen.
        con.execute('CREATE OR REPLACE TEMP TABLE zeitraum AS SELECT ?::DATE AS start, ?::DATE AS ende', [start, end])
        # Schritt 1: Gelaendehoehen der Haltestellen (swisstopo) in die Tabelle haltestelle uebernehmen.
        # Sie werden fuer die Hoehendifferenz zur Wetterstation gebraucht.
        heights = ROOT / 'data/stammdaten/haltestellen_hoehen.csv'
        if not heights.exists():
            raise FileNotFoundError('Zuerst src/build_haltestellen_hoehen.py ausfuehren')
        altitude = pd.read_csv(heights, dtype={'bpuic': str})
        con.register('hoehen_import', altitude)
        con.execute('UPDATE haltestelle SET hoehe_m=h.hoehe_m FROM hoehen_import h WHERE haltestelle.bpuic=h.bpuic')
        # Schritt 2: Basis = alle Halte im Zeitraum mit Kanton und Lokalzeit (Europe/Zurich, Sommerzeit korrekt).
        con.execute('''CREATE OR REPLACE TEMP VIEW basis AS
            SELECT h.*, s.kanton, timezone('Europe/Zurich', h.an_soll) AS an_lokal
            FROM halt h LEFT JOIN haltestelle s ON h.bpuic_haltestelle=s.bpuic
            WHERE betriebstag BETWEEN (SELECT start FROM zeitraum) AND (SELECT ende FROM zeitraum)''')
        # Die EDA sieht auch verworfene Zeilen und den korrekten Ankunftsstatus.
        for dimension in ['verkehrsmittel_gruppe', 'kanton', 'hour(an_lokal)']:
            name = {'verkehrsmittel_gruppe': 'verkehrsmittel', 'kanton': 'kanton',
                    'hour(an_lokal)': 'stunde'}[dimension]
            save_query(con, f'''SELECT {dimension} AS gruppe, count(*) AS halte,
                count(*) FILTER (WHERE an_status='REAL') AS an_real,
                avg(CASE WHEN an_status='REAL' THEN 1.0 ELSE 0.0 END) AS real_anteil,
                count(*) FILTER (WHERE an_soll IS NULL OR an_ist IS NULL) AS ankunft_fehlt,
                count(*) FILTER (WHERE faellt_aus) AS ausfaelle,
                count(*) FILTER (WHERE durchfahrt) AS durchfahrten,
                count(*) FILTER (WHERE an_verspaetung_min NOT BETWEEN -10 AND 60) AS ausreisser
                FROM basis GROUP BY 1 ORDER BY 1''', f'qualitaet_{name}')
        # Ankunftsstatus (REAL, PROGNOSE, GESCHAETZT, UNBEKANNT, leer) pro Verkehrsmittel fuer den Qualitaetsbericht.
        save_query(con, '''SELECT verkehrsmittel_gruppe, coalesce(an_status,'LEER') AS an_status,
            count(*) AS halte FROM basis GROUP BY 1,2 ORDER BY 1,2''', 'ankunftsstatus')
        # Ein Halt erscheint genau einmal in dieser sequenziellen Ausschlussbilanz.
        con.execute('''CREATE OR REPLACE TEMP VIEW klassifiziert AS SELECT *, CASE
            WHEN an_soll IS NULL OR an_ist IS NULL OR an_verspaetung_min IS NULL THEN '1_ankunft_fehlt'
            WHEN an_status IS DISTINCT FROM 'REAL' THEN '2_nicht_gemessen'
            WHEN faellt_aus IS TRUE THEN '3_ausfall'
            WHEN durchfahrt IS TRUE THEN '4_durchfahrt'
            WHEN NOT isfinite(an_verspaetung_min) OR an_verspaetung_min NOT BETWEEN -10 AND 60 THEN '5_unplausibel'
            WHEN kanton IS NULL THEN '6_haltestelle_fehlt'
            ELSE '7_behalten' END AS bereinigung FROM basis''')
        # Bereinigungsbilanz: wie viele Halte in welchem Schritt wegfallen.
        save_query(con, 'SELECT bereinigung, count(*) AS halte FROM klassifiziert GROUP BY 1 ORDER BY 1', 'bereinigung')
        # Kennzahlen der Verspaetung nach der Bereinigung (vor dem Wetter-Join).
        save_query(con, '''SELECT verkehrsmittel_gruppe, count(*) AS halte,
            avg(an_verspaetung_min) AS mittel_min, median(an_verspaetung_min) AS median_min,
            quantile_cont(an_verspaetung_min, .95) AS p95_min,
            avg((an_verspaetung_min>=3)::INT) AS verspaetet_anteil
            FROM klassifiziert WHERE bereinigung='7_behalten' GROUP BY 1''', 'verspaetung_bereinigt')
        # Geeignete Stationen: mindestens 90% der Kernparameter im Analysezeitraum vorhanden.
        con.execute('''CREATE OR REPLACE TEMP TABLE geeignet AS SELECT station_abk FROM wettermessung
            WHERE timezone('Europe/Zurich',zeitpunkt)::DATE BETWEEN
                (SELECT start FROM zeitraum) AND (SELECT ende FROM zeitraum)
            GROUP BY 1 HAVING count(niederschlag_mm)>=0.9 *
                date_diff('hour', timezone('Europe/Zurich',(SELECT start FROM zeitraum)::TIMESTAMP),
                timezone('Europe/Zurich',((SELECT ende FROM zeitraum)+1)::TIMESTAMP))
                AND count(temperatur_c)>=0.9 *
                date_diff('hour', timezone('Europe/Zurich',(SELECT start FROM zeitraum)::TIMESTAMP),
                timezone('Europe/Zurich',((SELECT ende FROM zeitraum)+1)::TIMESTAMP))''')
        # Schritt 3: raeumlicher Join. Haltestellen und geeignete Stationen als Tabellen holen.
        stops = con.execute('SELECT bpuic, lat, lon, hoehe_m FROM haltestelle').df()
        stations = con.execute('SELECT * FROM wetterstation JOIN geeignet USING(station_abk) ORDER BY station_abk').df()
        if stations.empty:
            raise ValueError('Keine geeigneten Wetterstationen')
        # Haversine-Distanz in km zwischen jeder Haltestelle und jeder Station (Matrix).
        a, b = np.radians(stops.lat.to_numpy())[:, None], np.radians(stations.lat.to_numpy())[None, :]
        dlon = np.radians(stops.lon.to_numpy())[:, None] - np.radians(stations.lon.to_numpy())[None, :]
        distance = 2 * 6371.0088 * np.arcsin(np.sqrt(np.clip(
            np.sin((a-b)/2)**2 + np.cos(a)*np.cos(b)*np.sin(dlon/2)**2, 0, 1)))
        # Hoehendifferenz in m; nur Stationen innerhalb max_distanz und max_hoehendiff sind gueltig.
        height_diff = np.abs(stops.hoehe_m.to_numpy()[:, None] - stations.hoehe_m.to_numpy()[None, :])
        valid = np.isfinite(distance) & np.isfinite(height_diff) & (distance<=max_distanz) & (height_diff<=max_hoehendiff)
        # Pro Haltestelle die naechste gueltige Station waehlen; ohne gueltige Station bleibt sie unzugeordnet.
        scores = np.where(valid, distance, np.inf)
        nearest = scores.argmin(axis=1)
        mapped = np.isfinite(scores.min(axis=1))
        mapping = pd.DataFrame({'bpuic': stops.bpuic[mapped].to_numpy(),
            'station_abk': stations.station_abk.to_numpy()[nearest[mapped]],
            'distanz_km': distance[np.arange(len(stops))[mapped],nearest[mapped]],
            'hoehendiff_m': height_diff[np.arange(len(stops))[mapped],nearest[mapped]]})
        # Zuordnung in haltestelle_station ersetzen (Transaktion) und als CSV dokumentieren.
        con.register('zuordnung_import', mapping)
        con.execute('BEGIN')
        con.execute('DELETE FROM haltestelle_station')
        con.execute('INSERT INTO haltestelle_station BY NAME SELECT * FROM zuordnung_import')
        con.execute('COMMIT')
        mapping.to_csv(ROOT / 'data/stammdaten/haltestelle_station.csv', index=False)
        stops.loc[~mapped].to_csv(OUT / 'haltestellen_ohne_station.csv', index=False)
        # Uebersicht pro Station: Anzahl zugeordnete Haltestellen, Distanzen und Hoehendifferenzen.
        save_query(con, '''SELECT s.station_abk,s.name,s.hoehe_m,count(m.bpuic) AS haltestellen,
            avg(distanz_km) AS mittlere_distanz_km,max(distanz_km) AS max_distanz_km,
            max(hoehendiff_m) AS max_hoehendiff_m FROM wetterstation s
            LEFT JOIN haltestelle_station m USING(station_abk) GROUP BY 1,2,3 ORDER BY 1''', 'stationszuordnung')
        # Schritt 4: Schwelle starker Niederschlag = 90. Perzentil der Stunden mit Niederschlag > 0.
        # Quantil auf Stationsstunden, NICHT auf der durch Halte vervielfachten Tabelle.
        q90 = con.execute('''SELECT quantile_cont(niederschlag_mm,.9) FROM wettermessung
            JOIN geeignet USING(station_abk) WHERE niederschlag_mm>0 AND
            timezone('Europe/Zurich',zeitpunkt)::DATE BETWEEN
                (SELECT start FROM zeitraum) AND (SELECT ende FROM zeitraum)''').fetchall()[0][0]
        if q90 is None:
            raise ValueError('Keine Niederschlagsstunden fuer das Quantil')
        # Schritt 5: kantonale Feiertage (TG, SG, AR, AI); sie zaehlen nicht zur Hauptverkehrszeit.
        calendar = []
        for canton in ['TG','SG','AR','AI']:
            for day, name in holidays.country_holidays('CH', subdiv=canton,
                    years=list(range(start.year, end.year+1)), language='de').items():
                calendar.append({'kanton': canton, 'datum': day, 'name': name})
        holiday_frame = pd.DataFrame(calendar)
        holiday_frame.to_csv(ROOT / 'data/stammdaten/feiertage.csv', index=False)
        con.register('feiertage', holiday_frame)
        # Schritt 6: zeitlicher Join. Jeder behaltene Halt erhaelt die Wetterstunde seiner Station
        # (Soll-Ankunft auf das Stundenintervall von MeteoSchweiz abgebildet) und die abgeleiteten
        # Variablen nach Paket A: verspaetet (>= 3 Min.), starker Niederschlag, Niederschlagsklasse,
        # Schnee/Frost und Hauptverkehrszeit.
        con.execute(f'''CREATE OR REPLACE TEMP TABLE verknuepft AS
            SELECT h.betriebstag,h.fahrt_bezeichner,h.bpuic,h.halt_nr,h.bpuic_haltestelle,
                h.kanton,h.linien_id,h.verkehrsmittel_gruppe,h.an_soll,h.an_verspaetung_min,
                (h.an_verspaetung_min>=3) AS verspaetet,
                m.station_abk,m.distanz_km,m.hoehendiff_m,w.zeitpunkt AS wetter_zeitpunkt,
                w.niederschlag_mm,w.temperatur_c,w.schneehoehe_cm,w.wind_kmh,
                (w.niederschlag_mm>?) AS starker_niederschlag,
                CASE WHEN w.niederschlag_mm IS NULL THEN NULL
                     WHEN w.niederschlag_mm=0 THEN 'trocken'
                     WHEN w.niederschlag_mm>? THEN 'stark' ELSE 'maessig' END AS niederschlagsklasse,
                CASE WHEN w.schneehoehe_cm IS NOT NULL THEN w.schneehoehe_cm>0
                     WHEN w.niederschlag_mm IS NULL OR w.temperatur_c IS NULL THEN NULL
                     ELSE w.niederschlag_mm>0 AND w.temperatur_c<0 END AS schnee_frost,
                CASE WHEN w.schneehoehe_cm IS NOT NULL THEN 'Schneedecke'
                     ELSE 'Niederschlag_und_Frost' END AS schnee_definition,
                (isodow(h.an_lokal)<=5 AND (hour(h.an_lokal)>=6 AND hour(h.an_lokal)<9
                    OR hour(h.an_lokal)>=16 AND hour(h.an_lokal)<19) AND f.datum IS NULL) AS hvz
            FROM klassifiziert h LEFT JOIN haltestelle_station m ON h.bpuic_haltestelle=m.bpuic
            LEFT JOIN wettermessung w ON w.station_abk=m.station_abk
                AND w.zeitpunkt={WETTER_STUNDE}
            LEFT JOIN feiertage f ON f.kanton=h.kanton AND f.datum=h.an_lokal::DATE
            WHERE h.bereinigung='7_behalten' ''', [q90,q90])
        # Join-Bilanz: wie viele Halte ohne Station, ohne Wetterzeit oder ohne Kernparameter bleiben.
        save_query(con, '''SELECT CASE WHEN station_abk IS NULL THEN 'keine_geeignete_station'
            WHEN wetter_zeitpunkt IS NULL THEN 'wetterzeit_fehlt'
            WHEN niederschlag_mm IS NULL OR temperatur_c IS NULL THEN 'kernparameter_fehlt'
            ELSE 'analyse' END AS ergebnis,count(*) AS halte FROM verknuepft GROUP BY 1 ORDER BY 1''', 'join_bilanz')
        # Schritt 7: Analysetabelle = nur Halte mit Niederschlag und Temperatur.
        con.execute('''CREATE OR REPLACE TABLE analyse_halt AS SELECT * FROM verknuepft
            WHERE niederschlag_mm IS NOT NULL AND temperatur_c IS NOT NULL''')
        # Gruppenmittel pro Niederschlagsklasse fuer Grafiken und Folien.
        for dimension in ['verkehrsmittel_gruppe', 'kanton', 'hvz']:
            save_query(con, f'''SELECT {dimension},niederschlagsklasse,count(*) AS halte,
                avg(an_verspaetung_min) AS mittel_min,median(an_verspaetung_min) AS median_min,
                avg(verspaetet::INT) AS verspaetet_anteil FROM analyse_halt GROUP BY 1,2 ORDER BY 1,2''', f'gruppen_{dimension}')
        save_query(con, '''SELECT verkehrsmittel_gruppe,floor(an_verspaetung_min) AS minute,count(*) AS halte
            FROM analyse_halt GROUP BY 1,2 ORDER BY 1,2''', 'verspaetungsverteilung')
        save_query(con, '''SELECT betriebstag,verkehrsmittel_gruppe,count(*) AS halte,
            avg(an_verspaetung_min) AS mittel_min,avg(niederschlag_mm) AS niederschlag_mm
            FROM analyse_halt GROUP BY 1,2 ORDER BY 1,2''', 'zeitreihe')
        # Stundenaggregation pro Linie, Station und Wetterlage: Grundlage fuer das Dashboard (Teil 2).
        con.execute('''CREATE OR REPLACE TABLE analyse_stunde AS SELECT
            date_trunc('hour',an_soll) AS stunde,linien_id,verkehrsmittel_gruppe,kanton,station_abk,hvz,
            starker_niederschlag,count(*) AS halte,avg(an_verspaetung_min) AS mittel_min,
            avg(verspaetet::INT) AS verspaetet_anteil FROM analyse_halt GROUP BY ALL''')
        # Beide Ergebnistabellen zusaetzlich als Parquet ablegen (nicht im Repo, siehe README).
        processed = ROOT / 'data/processed'
        processed.mkdir(parents=True,exist_ok=True)
        for table in ['analyse_halt', 'analyse_stunde']:
            path = (processed / f'{table}.parquet').as_posix().replace("'", "''")
            con.execute(f"COPY {table} TO '{path}' (FORMAT PARQUET, COMPRESSION ZSTD)")
        # Verwendete Parameter und Kennzahlen festhalten, damit die Auswertung nachvollziehbar ist.
        parameters = {'start':str(start),'end':str(end),'niederschlag_q90_mm':q90,
                      'max_distanz_km':max_distanz,'max_hoehendiff_m':max_hoehendiff,
                      'geeignete_stationen':stations.station_abk.tolist(),
                      'haltestellen_gesamt':len(stops),'haltestellen_zugeordnet':len(mapping),
                      'halte_analyse':con.execute('SELECT count(*) FROM analyse_halt').fetchone()[0]}
        (OUT / 'parameter.json').write_text(json.dumps(parameters,indent=2),encoding='utf-8')
        print(json.dumps(parameters,indent=2))
        return parameters
    finally:
        con.close()


def main():
    # Kommandozeile: Zeitraum, Datenbank und Grenzen fuer den raeumlichen Join.
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--start',type=date.fromisoformat,default=date(2026,1,1))
    p.add_argument('--end',type=date.fromisoformat,default=date(2026,3,31))
    p.add_argument('--db',type=Path,default=ROOT/'data/oev_wetter.duckdb')
    p.add_argument('--max-distanz',type=float,default=30)
    p.add_argument('--max-hoehendiff',type=float,default=500)
    a=p.parse_args()
    if a.end<a.start or a.max_distanz<=0 or a.max_hoehendiff<=0:
        p.error('Ungueltiger Zeitraum oder Distanz-/Hoehengrenze')
    transform(a.start,a.end,a.db,a.max_distanz,a.max_hoehendiff)


if __name__=='__main__':
    main()
