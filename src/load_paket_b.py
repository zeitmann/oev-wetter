"""Vorhandene Parquet-Uebergabe von B in das gemeinsame Schema laden.

Quelle (APA 7): DuckDB Foundation. (2026). DuckDB documentation: Parquet import.
https://duckdb.org/docs/data/parquet/overview
"""
import argparse
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parent.parent


def main():
    # Parameter: Ordner der B-Uebergabe (Parquet), Zieldatenbank und --force zum Ersetzen.
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', type=Path, default=ROOT / 'data/raw/paket-b-daten')
    parser.add_argument('--db', type=Path, default=ROOT / 'data/oev_wetter.duckdb')
    parser.add_argument('--force', action='store_true', help='B-Tabellen vollstaendig ersetzen')
    args = parser.parse_args()
    # Zielordner der Datenbank anlegen, falls er noch fehlt.
    args.db.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(args.db)) as con:
        # Gemeinsames Schema von B anlegen (CREATE TABLE IF NOT EXISTS, also wiederholbar).
        con.execute((ROOT / 'src/schema.sql').read_text(encoding='utf-8'))
        # Zeitstempel in der Sitzung einheitlich in UTC; gespeichert sind sie als TIMESTAMPTZ.
        con.execute("SET TimeZone='UTC'")
        # Drei Tabellen der Uebergabe; halt ist nach betriebstag partitioniert (Hive-Ordner).
        for table, pattern in [('haltestelle', 'haltestelle.parquet'),
                               ('halt', 'halt/*/*.parquet'), ('ingest_log', 'ingest_log.parquet')]:
            path = (args.input_dir / pattern).resolve().as_posix()
            # Parquet zuerst in eine temporaere Tabelle lesen, um die erwartete Zeilenzahl zu kennen.
            con.execute('CREATE OR REPLACE TEMP TABLE import_b AS SELECT * FROM read_parquet(?, hive_partitioning=true)', [path])
            expected = con.execute('SELECT count(*) FROM import_b').fetchone()[0]
            # Im ingest_log stehen auch Wetter-Eintraege von C; verglichen werden nur die Ist-Daten.
            condition = " WHERE quelle='istdaten'" if table == 'ingest_log' else ''
            current = con.execute(f'SELECT count(*) FROM {table}{condition}').fetchone()[0]
            # Idempotenz: Sind die Daten schon vollstaendig da, wird die Tabelle uebersprungen.
            # Eine abweichende Zeilenzahl deutet auf eine unvollstaendige Uebergabe hin -> Abbruch.
            if current and not args.force:
                if current != expected:
                    raise ValueError(f'{table}: {current:,} vorhandene statt {expected:,} erwartete Zeilen. '
                                     'Mit --force die vollstaendige B-Uebergabe laden.')
                # Wetter-Logs werden beim erneuten Aufbau nicht angefasst.
                print(f'{table}: bereits vorhanden ({current:,}); --force ersetzt die B-Daten')
                continue
            # Loeschen und Einfuegen in einer Transaktion: bei einem Fehler bleibt der alte Stand erhalten.
            con.execute('BEGIN')
            try:
                if table == 'ingest_log':
                    con.execute("DELETE FROM ingest_log WHERE quelle='istdaten'")
                else:
                    con.execute(f'DELETE FROM {table}')
                con.execute(f'INSERT INTO {table} BY NAME SELECT * FROM import_b')
                con.execute('COMMIT')
            except Exception:
                con.execute('ROLLBACK')
                raise
            print(f'{table}: {expected:,} Zeilen geladen')


if __name__ == '__main__':
    main()
