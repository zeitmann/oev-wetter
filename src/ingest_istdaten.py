"""
ingest_istdaten.py: Ingestion der Ist-Daten v2 (opentransportdata.swiss) in DuckDB.

Gruppe 4, DAENG HS26, Paket B (AP 3 Ingestion, AP 4 Storage).

Ablauf pro Betriebstag (siehe auch README, Abschnitt Ingestion):
  1. Ueberspringen, wenn der Tag laut Tabelle ingest_log schon erfolgreich
     geladen wurde (Idempotenz). Mit --force wird der Tag neu geladen.
  2. Tagesdatei beschaffen: zuerst lokal in --input-dir suchen, sonst
     herunterladen (mit Wiederholung bei Netzwerkfehlern).
  3. Datei blockweise (streamend) mit DuckDB lesen und filtern:
     nur Bahn und Bus (PRODUKT_ID) und nur Haltestellen der Ostschweiz
     (Liste aus --stops). Die Datei wird nie ganz in den Speicher geladen.
  4. Gefilterte Rohdaten unveraendert (gleiche Spalten, gleiches Format) als
     CSV in data/raw/istdaten/ ablegen.
  5. In der Datenbank den Tag zuerst loeschen und dann neu einfuegen, alles in
     einer Transaktion. Erneutes Ausfuehren erzeugt so keine Duplikate.
  6. Zeilen vor und nach dem Filter, Dauer und Fehler in ingest_log und im
     Logfile festhalten.

Zeitformat: Die Ist-Daten enthalten Lokalzeit (Europe/Zurich) ohne Zeitzone.
Beim Laden werden alle Zeitpunkte als TIMESTAMPTZ gespeichert, die Umstellung
auf Sommerzeit am 29.3.2026 wird dabei von DuckDB (ICU) korrekt behandelt.

Beispiele:
  # einen Tag ohne Haltestellenfilter testen (nur Bahn/Bus)
  python src/ingest_istdaten.py --start 2026-01-15 --end 2026-01-15 --no-stop-filter
  # ganzer Zeitraum mit Haltestellenliste von Paket C
  python src/ingest_istdaten.py --start 2026-01-01 --end 2026-03-31 --stops data/stammdaten/haltestellen_ostschweiz.csv

Quellen (APA 7):
  DuckDB Foundation. (2026). DuckDB documentation: CSV import.
      https://duckdb.org/docs/data/csv/overview
  DuckDB Foundation. (2026). DuckDB documentation: Timestamp with time zone functions.
      https://duckdb.org/docs/sql/functions/timestamptz
  Python Software Foundation. (2026). logging: Logging facility for Python.
      https://docs.python.org/3/library/logging.html
  SBB AG, Geschaeftsstelle Systemaufgaben Kundeninformation. (2026). Ist-Daten v2
      [Datensatz]. Open-Data-Plattform Mobilitaet Schweiz.
      https://data.opentransportdata.swiss/dataset/ist-daten-v2
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
import time
import urllib.request
import zipfile
from datetime import date, timedelta
from pathlib import Path

import duckdb

# ---------------------------------------------------------------------------
# Konstanten und Pfade
# ---------------------------------------------------------------------------

# Projektwurzel = Ordner oberhalb von src/
ROOT = Path(__file__).resolve().parent.parent

DEFAULT_DB = ROOT / "data" / "oev_wetter.duckdb"
DEFAULT_RAW_DIR = ROOT / "data" / "raw" / "istdaten"
DEFAULT_DOWNLOAD_DIR = ROOT / "data" / "raw" / "istdaten" / "download"
SCHEMA_FILE = ROOT / "src" / "schema.sql"
LOG_FILE = ROOT / "data" / "raw" / "logs" / "ingest_istdaten.log"

# CKAN-API des Datensatzes: liefert die Liste der Tagesdateien mit Download-URL.
CKAN_PACKAGE_URL = (
    "https://data.opentransportdata.swiss/api/3/action/package_show?id=ist-daten-v2"
)

# Monatsarchiv (geprueft am 20.10.2026 auf
# https://archive.opentransportdata.swiss/actual_data_archive.htm): v2 gibt es ab
# Juli 2025 als ein Zip pro Monat (ca. 1.3 bis 1.4 GB) mit einer CSV pro Tag.
DEFAULT_ARCHIVE_TEMPLATE = (
    "https://archive.opentransportdata.swiss/istdaten/{year}/ist-daten-v2-{year}-{month:02d}.zip"
)

# Dateiname der Tagesdatei, wie er in der CKAN-Liste vorkommt (z. B. 2026-02-28_IstDaten.csv)
DAILY_FILE_PATTERN = "{d}_IstDaten.csv"

# Nur diese Produkte werden behalten, Vergleich in Grossbuchstaben, weil die Daten
# sowohl 'Bus' als auch 'BUS' enthalten. Zahnradbahnen (z. B. Rorschach-Heiden)
# zaehlen zur Bahn. Zuordnung zur Gruppe Bahn/Bus fuer Hypothese H2:
PRODUKT_GRUPPE = {"ZUG": "Bahn", "ZAHNRADBAHN": "Bahn", "BUS": "Bus"}

# Spalten, die das Skript zwingend braucht (Namen laut Datensatz-Dokumentation).
# Fehlt eine, bricht der Tag mit einer klaren Fehlermeldung ab.
REQUIRED_COLUMNS = [
    "BETRIEBSTAG", "FAHRT_BEZEICHNER", "BETREIBER_ABK", "PRODUKT_ID",
    "LINIEN_ID", "LINIEN_TEXT", "VERKEHRSMITTEL_TEXT", "ZUSATZFAHRT_TF",
    "FAELLT_AUS_TF", "BPUIC", "HALTESTELLEN_NAME", "ANKUNFTSZEIT",
    "AN_PROGNOSE", "AN_PROGNOSE_STATUS", "ABFAHRTSZEIT", "AB_PROGNOSE",
    "AB_PROGNOSE_STATUS", "DURCHFAHRT_TF", "SLOID",
]

# Zeitformate in den Ist-Daten: Soll-Zeiten ohne Sekunden, Prognosen mit Sekunden.
# Zur Sicherheit werden beide Formate (und ISO) fuer alle Zeitspalten versucht.
TS_FORMATS = "['%d.%m.%Y %H:%M:%S', '%d.%m.%Y %H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M']"
DATE_FORMATS = "['%d.%m.%Y', '%Y-%m-%d']"

# 7-stellige Haltestellennummer aus BPUIC: In v2 ist BPUIC oft 9-stellig
# (Haltestelle + 2 Ziffern Kante/Gleis, z. B. 850978002 -> 8509780).
STOP_KEY = "CASE WHEN length(BPUIC) = 9 THEN left(BPUIC, 7) ELSE BPUIC END"

# Rangfolge, falls derselbe Halt doppelt geliefert wird (ca. 1900 Zeilen pro Tag,
# einmal ohne und einmal mit Prognose): die Zeile mit der besten Information gewinnt.
STATUS_RANG = """CASE AB_PROGNOSE_STATUS WHEN 'REAL' THEN 1 WHEN 'GESCHAETZT' THEN 2
    WHEN 'PROGNOSE' THEN 3 WHEN 'UNBEKANNT' THEN 4 ELSE 5 END"""

log = logging.getLogger("ingest_istdaten")


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def setup_logging() -> None:
    """Logging gleichzeitig in die Konsole und in ein Logfile schreiben."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s", "%Y-%m-%dT%H:%M:%S%z")
    for handler in (logging.StreamHandler(), logging.FileHandler(LOG_FILE, encoding="utf-8")):
        handler.setFormatter(fmt)
        log.addHandler(handler)
    log.setLevel(logging.INFO)


def daterange(start: date, end: date):
    """Alle Tage von start bis end (beide inklusive)."""
    for i in range((end - start).days + 1):
        yield start + timedelta(days=i)


def download(url: str, target: Path, retries: int = 4) -> Path:
    """Datei herunterladen, bei Netzwerkfehlern mit exponentiellem Backoff wiederholen.

    Es wird zuerst in eine .part-Datei geschrieben und erst am Schluss umbenannt,
    damit ein abgebrochener Download nie als vollstaendige Datei gilt.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    part = target.with_suffix(target.suffix + ".part")
    for attempt in range(1, retries + 1):
        try:
            log.info("Download %s (Versuch %d)", url, attempt)
            with urllib.request.urlopen(url, timeout=120) as resp, open(part, "wb") as out:
                while chunk := resp.read(1 << 20):  # 1 MB Bloecke
                    out.write(chunk)
            part.rename(target)
            return target
        except OSError as exc:  # URLError ist eine Unterklasse von OSError
            wait = 2 ** attempt
            log.warning("Download fehlgeschlagen (%s), neuer Versuch in %d s", exc, wait)
            time.sleep(wait)
    raise RuntimeError(f"Download nach {retries} Versuchen fehlgeschlagen: {url}")


_ckan_cache: dict[str, str] | None = None


def ckan_daily_urls() -> dict[str, str]:
    """Liste der Tagesdateien aus der CKAN-API: {Dateiname: Download-URL}."""
    global _ckan_cache
    if _ckan_cache is None:
        with urllib.request.urlopen(CKAN_PACKAGE_URL, timeout=60) as resp:
            package = json.load(resp)
        _ckan_cache = {
            Path(r["url"]).name: r["url"] for r in package["result"]["resources"] if r.get("url")
        }
    return _ckan_cache


def fetch_day(d: date, input_dir: Path | None, download_dir: Path, archive_template: str) -> Path:
    """Pfad zur (ungefilterten) Tagesdatei liefern, falls noetig herunterladen.

    Reihenfolge: lokale Datei -> Tagesdatei aus CKAN -> Monats-Zip aus dem Archiv.
    """
    global _ckan_cache
    name = DAILY_FILE_PATTERN.format(d=d.isoformat())
    for folder in filter(None, (input_dir, download_dir)):
        if (folder / name).exists():
            return folder / name

    # 1) aktuelle Tagesdateien (CKAN haelt nur die letzten Wochen/Monate)
    try:
        urls = ckan_daily_urls()
        if name in urls:
            return download(urls[name], download_dir / name)
    except OSError as exc:
        _ckan_cache = {}  # nicht fuer jeden Tag erneut versuchen
        log.warning("CKAN-Abfrage fehlgeschlagen, nutze Archiv: %s", exc)

    # 2) Monatsarchiv: Zip einmal pro Monat laden, gesuchten Tag entpacken
    zip_url = archive_template.format(year=d.year, month=d.month)
    zip_path = download_dir / Path(zip_url).name
    if not zip_path.exists():
        download(zip_url, zip_path)
    with zipfile.ZipFile(zip_path) as zf:
        members = [m for m in zf.namelist() if m.endswith(name)]
        if not members:
            raise FileNotFoundError(f"{name} nicht in {zip_path.name} gefunden")
        # zuerst in eine .part-Datei entpacken und erst danach umbenennen, damit
        # ein abgebrochenes Entpacken nie als vollstaendige Tagesdatei gilt
        part = download_dir / (name + ".part")
        with zf.open(members[0]) as src, open(part, "wb") as out:
            while chunk := src.read(1 << 20):
                out.write(chunk)
        part.rename(download_dir / name)
    return download_dir / name


def csv_source(path: Path) -> str:
    """DuckDB-Ausdruck zum streamenden Lesen der Tagesdatei.

    all_varchar: alles zuerst als Text lesen, die Typumwandlung passiert
    kontrolliert beim Laden (try_strptime, TRY_CAST). So bricht das Einlesen
    nicht an einzelnen unsauberen Zeilen ab.
    """
    return (
        f"read_csv('{path.as_posix()}', delim=';', header=true, all_varchar=true, "
        f"quote='\"', encoding='utf-8')"
    )


def check_columns(con: duckdb.DuckDBPyConnection, src: str) -> None:
    """Pruefen, ob alle benoetigten Spalten vorhanden sind (Schema-Drift erkennen)."""
    cols = {row[0] for row in con.execute(f"DESCRIBE SELECT * FROM {src}").fetchall()}
    missing = [c for c in REQUIRED_COLUMNS if c not in cols]
    if missing:
        raise ValueError(f"Spalten fehlen in der Tagesdatei: {missing}; vorhanden: {sorted(cols)}")


def ts(col: str) -> str:
    """SQL-Ausdruck: Text in Lokalzeit -> TIMESTAMPTZ (Europe/Zurich)."""
    return f"timezone('Europe/Zurich', try_strptime(NULLIF({col}, ''), {TS_FORMATS}))"


# ---------------------------------------------------------------------------
# Verarbeitung eines Tages
# ---------------------------------------------------------------------------

def process_day(con, d: date, args, stop_filter: bool, filter_id: str) -> None:
    t0 = time.time()
    raw_path = fetch_day(d, args.input_dir, args.download_dir, args.archive_template)
    src = csv_source(raw_path)
    check_columns(con, src)

    # Filterbedingung: Bahn/Bus und optional Haltestellen der Ostschweiz.
    # Verglichen wird die 7-stellige Haltestellennummer (siehe STOP_KEY).
    produkte = ", ".join(f"'{p}'" for p in PRODUKT_GRUPPE)
    where = f"upper(PRODUKT_ID) IN ({produkte})"
    if stop_filter:
        where += f" AND {STOP_KEY} IN (SELECT bpuic FROM stops_filter)"

    # Gefilterte Rohdaten unveraendert (alle Spalten als Text) ablegen
    args.raw_dir.mkdir(parents=True, exist_ok=True)
    filtered = args.raw_dir / f"{d.isoformat()}_IstDaten_ostschweiz.csv"
    con.execute(
        f"COPY (SELECT * FROM {src} WHERE {where}) "
        f"TO '{filtered.as_posix()}' (HEADER, DELIMITER ';')"
    )

    rows_raw = con.execute(f"SELECT count(*) FROM {src}").fetchone()[0]
    fsrc = csv_source(filtered)

    # Laden in einer Transaktion: Tag loeschen, neu einfuegen, Log schreiben
    con.execute("BEGIN TRANSACTION")
    try:
        con.execute("DELETE FROM halt WHERE betriebstag = ?", [d])
        con.execute(f"""
            INSERT INTO halt
            WITH dedup AS (
                -- 1) exakte Doppel (gleiche Fahrt, Kante und Soll-Zeiten) entfernen
                SELECT * FROM {fsrc}
                QUALIFY row_number() OVER (
                    PARTITION BY BETRIEBSTAG, FAHRT_BEZEICHNER, BPUIC, ANKUNFTSZEIT, ABFAHRTSZEIT
                    ORDER BY {STATUS_RANG}) = 1
            )
            SELECT
                try_strptime(BETRIEBSTAG, {DATE_FORMATS})::DATE,
                FAHRT_BEZEICHNER,
                BPUIC,
                -- 2) laufende Nummer, falls die Fahrt die Kante mehrmals anfaehrt
                row_number() OVER (
                    PARTITION BY BETRIEBSTAG, FAHRT_BEZEICHNER, BPUIC
                    ORDER BY coalesce(ANKUNFTSZEIT, ABFAHRTSZEIT)) AS halt_nr,
                {STOP_KEY},
                NULLIF(SLOID, ''),
                HALTESTELLEN_NAME,
                BETREIBER_ABK,
                -- 'BUS' und 'Bus' vereinheitlichen
                CASE upper(PRODUKT_ID) WHEN 'BUS' THEN 'Bus' ELSE PRODUKT_ID END,
                CASE WHEN upper(PRODUKT_ID) = 'BUS' THEN 'Bus' ELSE 'Bahn' END,
                VERKEHRSMITTEL_TEXT,
                LINIEN_ID,
                LINIEN_TEXT,
                TRY_CAST(ZUSATZFAHRT_TF AS BOOLEAN),
                TRY_CAST(FAELLT_AUS_TF AS BOOLEAN),
                TRY_CAST(DURCHFAHRT_TF AS BOOLEAN),
                {ts('ANKUNFTSZEIT')} AS an_soll,
                {ts('AN_PROGNOSE')}  AS an_ist,
                NULLIF(AN_PROGNOSE_STATUS, ''),
                {ts('ABFAHRTSZEIT')} AS ab_soll,
                {ts('AB_PROGNOSE')}  AS ab_ist,
                NULLIF(AB_PROGNOSE_STATUS, ''),
                -- Verspaetung in Minuten = Ist minus Soll
                epoch(an_ist - an_soll) / 60.0,
                epoch(ab_ist - ab_soll) / 60.0,
                '{raw_path.name}'
            FROM dedup
        """)
        rows_loaded = con.execute("SELECT count(*) FROM halt WHERE betriebstag = ?", [d]).fetchone()[0]
        con.execute(
            "INSERT OR REPLACE INTO ingest_log "
            "(quelle, betriebstag, status, zeilen_roh, zeilen_gefiltert, dauer_s, meldung, geladen_am, filter) "
            "VALUES ('istdaten', ?, 'ok', ?, ?, ?, ?, current_timestamp, ?)",
            [d, rows_raw, rows_loaded, round(time.time() - t0, 1), raw_path.name, filter_id],
        )
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise

    log.info("%s: %d Zeilen roh, %d nach Filter, %.1f s", d, rows_raw, rows_loaded, time.time() - t0)

    # Ungefilterte Tagesdatei (400-620 MB) wieder loeschen, ausser --keep-full
    if not args.keep_full and raw_path.parent == args.download_dir:
        raw_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Hauptprogramm
# ---------------------------------------------------------------------------

def main() -> None:
    p = argparse.ArgumentParser(description="Ist-Daten v2 gefiltert in DuckDB laden.")
    p.add_argument("--start", type=date.fromisoformat, required=True, help="erster Tag, YYYY-MM-DD")
    p.add_argument("--end", type=date.fromisoformat, required=True, help="letzter Tag, YYYY-MM-DD")
    p.add_argument("--db", type=Path, default=DEFAULT_DB)
    p.add_argument("--stops", type=Path, help="CSV mit Spalte 'bpuic' (Haltestellen Ostschweiz)")
    p.add_argument("--no-stop-filter", action="store_true", help="nur Bahn/Bus filtern (Test)")
    p.add_argument("--input-dir", type=Path, help="Ordner mit bereits heruntergeladenen Tagesdateien")
    p.add_argument("--download-dir", type=Path, default=DEFAULT_DOWNLOAD_DIR)
    p.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    p.add_argument("--archive-template", default=DEFAULT_ARCHIVE_TEMPLATE)
    p.add_argument("--force", action="store_true", help="bereits geladene Tage neu laden")
    p.add_argument("--keep-full", action="store_true", help="ungefilterte Tagesdateien behalten")
    args = p.parse_args()

    if not args.stops and not args.no_stop_filter:
        p.error("--stops angeben oder fuer einen Test --no-stop-filter setzen")

    setup_logging()
    args.db.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(args.db))
    con.execute("SET TimeZone = 'Europe/Zurich'")  # Anzeige der TIMESTAMPTZ in Lokalzeit
    con.execute(SCHEMA_FILE.read_text(encoding="utf-8"))

    stop_filter = not args.no_stop_filter
    if stop_filter:
        con.execute(
            "CREATE OR REPLACE TEMP TABLE stops_filter AS "
            # nur die ersten 7 Ziffern, falls C 9-stellige Nummern liefert
            "SELECT DISTINCT left(CAST(bpuic AS VARCHAR), 7) AS bpuic "
            f"FROM read_csv('{args.stops.as_posix()}', header=true)"
        )
        log.info("Haltestellenfilter: %d Haltestellen", con.execute("SELECT count(*) FROM stops_filter").fetchone()[0])
        # Haltestellenliste auch als Stammdatentabelle ablegen (fuer Joins in Paket C)
        con.execute(
            "INSERT OR REPLACE INTO haltestelle "
            # gleicher 7-stelliger Schluessel wie halt.bpuic_haltestelle; mehrere Zeilen
            # derselben Haltestelle (Kanten) werden zu einer zusammengefasst
            "SELECT DISTINCT ON (left(bpuic, 7)) left(bpuic, 7), sloid, name, kanton, "
            "TRY_CAST(lat AS DOUBLE), TRY_CAST(lon AS DOUBLE), TRY_CAST(hoehe_m AS DOUBLE) "
            f"FROM read_csv('{args.stops.as_posix()}', header=true, all_varchar=true) "
            "ORDER BY left(bpuic, 7), length(bpuic)"
        )

    # Kennung des Filters: Ein Tag gilt nur als erledigt, wenn er mit demselben
    # Filter geladen wurde. Sonst (z. B. erst Test ohne Filter, dann mit Liste)
    # wird er neu geladen, damit nie verschiedene Filter gemischt werden.
    if stop_filter:
        ids = [r[0] for r in con.execute("SELECT bpuic FROM stops_filter ORDER BY bpuic").fetchall()]
        filter_id = "stops:" + hashlib.sha256(",".join(ids).encode()).hexdigest()[:12]
    else:
        filter_id = "keiner"
    done = {r[0] for r in con.execute(
        "SELECT betriebstag FROM ingest_log WHERE quelle = 'istdaten' AND status = 'ok' AND filter = ?",
        [filter_id]).fetchall()}

    failed = []
    for d in daterange(args.start, args.end):
        if d in done and not args.force:
            log.info("%s: bereits geladen, uebersprungen", d)
            continue
        try:
            process_day(con, d, args, stop_filter, filter_id)
        except Exception as exc:  # Fehler protokollieren und mit dem naechsten Tag weitermachen
            log.error("%s: Fehler: %s", d, exc)
            failed.append(d)
            con.execute(
                "INSERT OR REPLACE INTO ingest_log (quelle, betriebstag, status, meldung, geladen_am, filter) "
                "VALUES ('istdaten', ?, 'fehler', ?, current_timestamp, ?)",
                [d, str(exc)[:1000], filter_id],
            )

    con.close()
    if failed:
        log.error("Fehlende Tage (%d): %s", len(failed), ", ".join(map(str, failed)))
        sys.exit(1)  # Exit-Code ungleich 0, damit ein unvollstaendiger Lauf auffaellt


if __name__ == "__main__":
    main()
