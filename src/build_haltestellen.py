"""
build_haltestellen.py: Haltestellenliste der Ostschweiz (TG, SG, AR, AI) erstellen.

Gruppe 4, DAENG HS26, Paket B (Filter fuer die Ingestion der Ist-Daten).

Ablauf:
  1. Haltestellen mit Koordinaten aus dem GTFS-Fahrplan (stops.txt) lesen.
     Verwendet werden die Elternstationen mit 7-stelliger Nummer; Kanten bzw.
     Gleise werden in der Ingestion ueber die ersten 7 Ziffern der BPUIC zugeordnet.
  2. Kantonsgrenzen aus swissBOUNDARIES3D (swisstopo) laden.
  3. Raeumlicher Join (Punkt in Polygon): jede Haltestelle erhaelt ihren Kanton.
  4. Nur TG, SG, AR, AI behalten und als CSV ablegen:
     data/stammdaten/haltestellen_ostschweiz.csv (Spalten wie mit C abgestimmt:
     bpuic, sloid, name, kanton, lat, lon, hoehe_m).

Die Hoehe ist in GTFS nicht enthalten (hoehe_m bleibt leer); C kann sie bei
Bedarf fuer den Hoehenvergleich mit den Wetterstationen ergaenzen.

Beispiel:
  python src/build_haltestellen.py --gtfs data/raw/stammdaten/GTFS_FP2026_20260211.zip

Quellen (APA 7):
  Bundesamt fuer Landestopografie swisstopo. (2026). swissBOUNDARIES3D [Datensatz].
      https://www.swisstopo.admin.ch/de/landschaftsmodell-swissboundaries3d
  GeoPandas developers. (2026). GeoPandas documentation: Spatial joins.
      https://geopandas.org/en/stable/docs/user_guide/mergingdata.html
  SBB AG, Geschaeftsstelle Systemaufgaben Kundeninformation. (2026). Fahrplan 2026
      (GTFS2020) [Datensatz]. Open-Data-Plattform Mobilitaet Schweiz.
      https://archive.opentransportdata.swiss/timetable_gtfs.htm
"""

from __future__ import annotations

import argparse
import json
import logging
import urllib.request
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "data" / "stammdaten" / "haltestellen_ostschweiz.csv"
DEFAULT_BOUNDARY_DIR = ROOT / "data" / "raw" / "stammdaten"

# STAC-Katalog von swisstopo: liefert die aktuelle Ausgabe von swissBOUNDARIES3D
STAC_ITEMS = "https://data.geo.admin.ch/api/stac/v0.9/collections/ch.swisstopo.swissboundaries3d/items"

KANTONE = {"TG", "SG", "AR", "AI"}

# Kantonsnummer (BFS) -> Kuerzel; swissBOUNDARIES3D fuehrt die Nummer im Feld KANTONSNUM
KANTON_NR = {17: "SG", 15: "AR", 16: "AI", 20: "TG"}

log = logging.getLogger("build_haltestellen")


def download_boundaries(target_dir: Path) -> Path:
    """Neueste swissBOUNDARIES3D-GeoPackage ueber den STAC-Katalog laden (falls noch nicht vorhanden)."""
    with urllib.request.urlopen(STAC_ITEMS, timeout=60) as resp:
        items = json.load(resp)["features"]
    # Assets aller Ausgaben sammeln, GeoPackage bevorzugen, neueste Ausgabe zuerst
    assets = [
        a["href"] for item in sorted(items, key=lambda i: i["id"], reverse=True)
        for a in item["assets"].values() if "gpkg" in a["href"].lower()
    ]
    if not assets:
        raise RuntimeError("Keine GeoPackage-Datei im STAC-Katalog gefunden")
    url = assets[0]
    target = target_dir / Path(url).name
    if not target.exists():
        log.info("Download %s", url)
        target_dir.mkdir(parents=True, exist_ok=True)
        # in .part-Datei laden und erst nach vollstaendigem Download umbenennen
        part = target.with_name(target.name + ".part")
        urllib.request.urlretrieve(url, part)
        part.rename(target)
    if target.suffix == ".zip":  # GeoPackage kann gezippt geliefert werden
        with zipfile.ZipFile(target) as zf:
            gpkg = next(m for m in zf.namelist() if m.endswith(".gpkg"))
            zf.extract(gpkg, target_dir)
            return target_dir / gpkg
    return target


def load_cantons(gpkg: Path) -> gpd.GeoDataFrame:
    """Kantonspolygone (LV95) aus dem GeoPackage lesen, mit Spalte 'kanton'."""
    import pyogrio

    layer = next(name for name, _ in pyogrio.list_layers(gpkg) if "kantons" in name.lower())
    cantons = gpd.read_file(gpkg, layer=layer)
    cantons["kanton"] = cantons["kantonsnummer" if "kantonsnummer" in cantons else "KANTONSNUM"].map(KANTON_NR)
    return cantons[cantons["kanton"].notna()][["kanton", "geometry"]]


def load_stops(gtfs_zip: Path) -> gpd.GeoDataFrame:
    """Haltestellen aus GTFS stops.txt.

    Verwendet werden die Elternstationen (location_type = 1, stop_id 'Parent8506174'):
    Sie entsprechen genau der 7-stelligen Haltestellennummer in den Ist-Daten
    (Abdeckung am 15.1.2026: 22 498 von 22 508 Schweizer Haltestellen).
    """
    with zipfile.ZipFile(gtfs_zip) as zf, zf.open("stops.txt") as f:
        stops = pd.read_csv(f, dtype=str, encoding="utf-8-sig")
    stops = stops[stops["location_type"] == "1"].copy()
    stops["bpuic"] = stops["stop_id"].str.removeprefix("Parent")
    stops = stops[stops["bpuic"].str.fullmatch(r"85\d{5}")]
    stops = stops.rename(columns={"stop_name": "name", "original_stop_id": "sloid"})
    stops["lat"] = stops["stop_lat"].astype(float)
    stops["lon"] = stops["stop_lon"].astype(float)
    return gpd.GeoDataFrame(
        stops[["bpuic", "sloid", "name", "lat", "lon"]],
        geometry=gpd.points_from_xy(stops["lon"], stops["lat"]),
        crs="EPSG:4326",
    )


def main() -> None:
    p = argparse.ArgumentParser(description="Haltestellenliste Ostschweiz erstellen.")
    p.add_argument("--gtfs", type=Path, required=True, help="GTFS-Zip aus dem Fahrplanarchiv")
    p.add_argument("--boundaries", type=Path, help="swissBOUNDARIES3D GeoPackage (sonst Download)")
    p.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    gpkg = args.boundaries or download_boundaries(DEFAULT_BOUNDARY_DIR)
    cantons = load_cantons(gpkg)
    stops = load_stops(args.gtfs).to_crs(cantons.crs)  # beide in LV95 rechnen

    # Punkt-in-Polygon: Haltestellen ausserhalb der vier Kantone fallen weg
    joined = gpd.sjoin(stops, cantons, how="inner", predicate="within")
    out = joined[["bpuic", "sloid", "name", "kanton", "lat", "lon"]].drop_duplicates("bpuic")
    out["hoehe_m"] = pd.NA
    out = out.sort_values(["kanton", "name"])

    args.out.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False, encoding="utf-8")
    log.info("%d Haltestellen geschrieben: %s", len(out), out["kanton"].value_counts().to_dict())


if __name__ == "__main__":
    main()
