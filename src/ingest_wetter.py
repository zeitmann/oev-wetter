"""SwissMetNet-Stundenwerte fuer Paket C laden (wie Paket B: CLI, Log, DuckDB).

Quellen (APA 7):
Bundesamt fuer Meteorologie und Klimatologie MeteoSchweiz. (2026).
Automatische Wetterstationen: Messwerte [Datensatz]. Quelle: MeteoSchweiz.
https://opendatadocs.meteoswiss.ch/a-data-groundbased/a1-automatic-weather-stations
MeteoSchweiz. (2026). Download data. https://opendatadocs.meteoswiss.ch/general/download
DuckDB Foundation. (2026). DuckDB documentation. https://duckdb.org/docs/
"""
import argparse
import json
import logging
import ssl
import time
import urllib.request
from datetime import date, timedelta
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
BASE = 'https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn'
STAC = 'https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-smn/items'
PARAMETER = {'rre150h0': 'niederschlag_mm', 'tre200h0': 'temperatur_c',
             'htoauths': 'schneehoehe_cm', 'fu3010h0': 'wind_kmh'}
log = logging.getLogger('ingest_wetter')


def download(url, target, force=False):
    """Rohdatei unveraendert aufbewahren; unterbrochene Downloads nicht verwenden."""
    if target.exists() and not force:
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    # TLS 1.2 funktioniert auch im Schul-/Windows-Netz; Zertifikate werden geprueft.
    context = ssl.create_default_context()
    context.maximum_version = ssl.TLSVersion.TLSv1_2
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=90, context=context) as response:
                part = target.with_suffix(target.suffix + '.part')
                part.write_bytes(response.read())
            part.replace(target)
            return target
        except OSError:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def ingest(start, end, db, force=False):
    if end < start:
        raise ValueError('Enddatum liegt vor dem Startdatum')
    raw = ROOT / 'data/raw/wetter'
    (ROOT / 'data/raw/logs').mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s',
                        handlers=[logging.StreamHandler(), logging.FileHandler(
                            ROOT / 'data/raw/logs/ingest_wetter.log', encoding='utf-8')])
    for filename in ['ogd-smn_meta_stations.csv', 'ogd-smn_meta_parameters.csv',
                     'ogd-smn_meta_datainventory.csv']:
        download(f'{BASE}/{filename}', raw / filename, force)
    meta = pd.read_csv(raw / 'ogd-smn_meta_stations.csv', sep=';', encoding='cp1252')
    stations = meta.loc[meta.station_canton.isin(['TG', 'SG', 'AR', 'AI'])].copy()
    station_frame = stations.rename(columns={
        'station_abbr': 'station_abk', 'station_name': 'name', 'station_canton': 'kanton',
        'station_coordinates_wgs84_lat': 'lat', 'station_coordinates_wgs84_lon': 'lon',
        'station_height_masl': 'hoehe_m'})[['station_abk', 'name', 'kanton', 'lat', 'lon', 'hoehe_m']]
    # Betriebstage koennen Halte vor/nach Mitternacht enthalten: Randtage mitladen.
    lower = pd.Timestamp(start - timedelta(days=1), tz='Europe/Zurich').tz_convert('UTC')
    upper = pd.Timestamp(end + timedelta(days=2), tz='Europe/Zurich').tz_convert('UTC')
    manifest, quality, frames = [], [], []
    started = time.monotonic()
    con = duckdb.connect(str(db))
    try:
        con.execute((ROOT / 'src/schema.sql').read_text(encoding='utf-8'))
        con.execute("SET TimeZone='UTC'")
        for station in station_frame.station_abk:
            log.info('Station %s', station)
            item_path = download(f'{STAC}/{station.lower()}', raw / f'{station.lower()}.json', force)
            assets = json.loads(item_path.read_text(encoding='utf-8'))['assets']
            selected = []
            for name, asset in assets.items():
                if '_h_recent.csv' in name:
                    selected.append((name, asset['href']))
                elif '_h_historical_' in name:
                    period = name.rsplit('_', 1)[1].replace('.csv', '').split('-')
                    if int(period[0]) <= upper.year and int(period[1]) >= lower.year:
                        selected.append((name, asset['href']))
            pieces = []
            # recent kommt zuletzt und hat Vorrang bei ueberlappenden Zeitpunkten.
            for name, url in sorted(selected):
                path = download(url, raw / name, force)
                manifest.append({'station_abk': station, 'datei': name, 'url': url})
                source = pd.read_csv(path, sep=';', encoding='cp1252')
                source['zeitpunkt'] = pd.to_datetime(source.reference_timestamp,
                    format='%d.%m.%Y %H:%M', utc=True, errors='raise')
                source = source.loc[source.zeitpunkt.between(lower, upper)]
                if source.empty:
                    continue
                frame = pd.DataFrame({'zeitpunkt': source.zeitpunkt})
                frame['station_abk'] = station
                for original, column in PARAMETER.items():
                    frame[column] = pd.to_numeric(source[original], errors='coerce') if original in source else float('nan')
                pieces.append(frame)
            if not pieces:
                raise ValueError(f'{station}: keine Stundenwerte fuer den Zeitraum')
            frame = pd.concat(pieces).drop_duplicates(['station_abk', 'zeitpunkt'], keep='last')
            # Offensichtlich unmoegliche Werte werden fehlend, nie zu trocken/0 imputiert.
            for column in ['niederschlag_mm', 'schneehoehe_cm', 'wind_kmh']:
                frame.loc[frame[column] < 0, column] = float('nan')
            frame.loc[~frame.temperatur_c.between(-60, 60), 'temperatur_c'] = float('nan')
            expected = len(pd.date_range(lower, upper, freq='h'))
            quality.append({'station_abk': station, 'stunden_erwartet': expected,
                            'stunden_vorhanden': len(frame), 'fehlende_zeitstempel': expected-len(frame),
                            **{f'{c}_vorhanden': int(frame[c].notna().sum()) for c in PARAMETER.values()}})
            frames.append(frame)
        weather = pd.concat(frames, ignore_index=True)
        con.register('stations_import', station_frame)
        con.register('wetter_import', weather)
        con.execute('BEGIN')
        con.execute('INSERT OR REPLACE INTO wetterstation BY NAME SELECT * FROM stations_import')
        con.execute('INSERT OR REPLACE INTO wettermessung BY NAME SELECT * FROM wetter_import')
        day = start
        while day <= end:
            count = int((weather.zeitpunkt.dt.tz_convert('Europe/Zurich').dt.date == day).sum())
            con.execute('''INSERT OR REPLACE INTO ingest_log
                (quelle, betriebstag, status, zeilen_gefiltert, dauer_s, meldung, filter)
                VALUES ('wetter', ?, 'ok', ?, ?, ?, ?)''',
                [day, count, time.monotonic()-started, 'Stationsluecken: docs/ergebnisse/wetterqualitaet.csv',
                 ','.join(sorted(station_frame.station_abk))])
            day += timedelta(days=1)
        con.execute('COMMIT')
        out = ROOT / 'docs/ergebnisse'
        out.mkdir(parents=True, exist_ok=True)
        station_frame.to_csv(ROOT / 'data/stammdaten/wetterstationen.csv', index=False)
        pd.DataFrame(quality).to_csv(out / 'wetterqualitaet.csv', index=False)
        pd.DataFrame(manifest).to_csv(out / 'wetterquellen.csv', index=False)
        sample = weather.loc[weather.zeitpunkt.between(pd.Timestamp(start, tz='UTC'),
                           pd.Timestamp(start + timedelta(days=1), tz='UTC'), inclusive='left')]
        sample.to_csv(ROOT / 'data/sample/wetter_stunden.csv', index=False)
        log.info('%s Stationen, %s Messzeitpunkte gespeichert', len(station_frame), len(weather))
    except Exception as exc:
        log.exception('Wetter-Ingestion fehlgeschlagen: %s', exc)
        raise
    finally:
        con.close()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--start', type=date.fromisoformat, default=date(2026, 1, 1))
    p.add_argument('--end', type=date.fromisoformat, default=date(2026, 3, 31))
    p.add_argument('--db', type=Path, default=ROOT / 'data/oev_wetter.duckdb')
    p.add_argument('--force', action='store_true', help='Rohdateien erneut herunterladen')
    args = p.parse_args()
    ingest(args.start, args.end, args.db, args.force)


if __name__ == '__main__':
    main()
