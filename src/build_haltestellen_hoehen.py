"""Fehlende Haltestellenhoehen aus dem Gelaendemodell ergaenzen (lokaler Cache).

Quellen (APA 7):
Bundesamt fuer Landestopografie swisstopo. (2026). Height: GeoAdmin API.
https://api3.geo.admin.ch/services/sdiservices.html#height
pyproj contributors. (2026). pyproj documentation. https://pyproj4.github.io/pyproj/
Gelaendehoehen sind Naeherungen, keine vermessenen Bahnsteighoehen.
"""
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pandas as pd
from pyproj import Transformer
from ingest_wetter import download

ROOT = Path(__file__).resolve().parent.parent


def main():
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    stops = pd.read_csv(ROOT / 'data/stammdaten/haltestellen_ostschweiz.csv', dtype={'bpuic': str})
    project = Transformer.from_crs(4326, 2056, always_xy=True)
    east, north = project.transform(stops.lon.to_numpy(), stops.lat.to_numpy())
    jobs = list(zip(stops.bpuic, east, north))

    def height(job):
        stop, x, y = job
        url = f'https://api3.geo.admin.ch/rest/services/height?easting={x:.2f}&northing={y:.2f}&sr=2056'
        path = download(url, ROOT / f'data/raw/stammdaten/hoehen/{stop}.json')
        return float(json.loads(path.read_text(encoding='utf-8'))['height'])

    heights = []
    # Vier gleichzeitige, gecachte Punktabfragen statt einer weiteren Datenplattform.
    with ThreadPoolExecutor(max_workers=4) as pool:
        for i, value in enumerate(pool.map(height, jobs), 1):
            heights.append(value)
            if i % 250 == 0:
                logging.info('%s / %s Hoehen geladen', i, len(jobs))
    result = stops[['bpuic']].copy()
    result['hoehe_m'] = heights
    result.to_csv(ROOT / 'data/stammdaten/haltestellen_hoehen.csv', index=False)
    logging.info('%s Gelaendehoehen gespeichert', len(result))


if __name__ == '__main__':
    main()
