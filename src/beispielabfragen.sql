-- =============================================================================
-- beispielabfragen.sql: Nachweis, dass die Datenbank funktioniert (Paket B, AP 4)
--
-- Ausfuehren:  duckdb data/oev_wetter.duckdb < src/beispielabfragen.sql
--   oder in Python: duckdb.connect('data/oev_wetter.duckdb').sql(open(...).read())
-- Hinweis: Die Verspaetungen sind noch unbereinigt (siehe docs/quellenprofil_istdaten.md);
-- deshalb wird hier der Median statt des Mittelwerts gezeigt.
--
-- Quelle (APA 7):
-- DuckDB Foundation. (2026). DuckDB documentation: Aggregate functions.
--     https://duckdb.org/docs/sql/functions/aggregates
-- =============================================================================

SET TimeZone = 'Europe/Zurich';

-- 1) Ingestion-Protokoll: Zeilen vor und nach dem Filter pro Tag, Fehler
SELECT betriebstag, status, zeilen_roh, zeilen_gefiltert, dauer_s
FROM ingest_log
ORDER BY betriebstag;

-- 2) Anzahl Halte pro Tag und Verkehrsmittel
SELECT betriebstag, verkehrsmittel_gruppe, count(*) AS halte
FROM halt
GROUP BY ALL
ORDER BY betriebstag, verkehrsmittel_gruppe;

-- 3) Median der Abfahrtsverspaetung pro Linie (nur echte Messwerte, nur Linien mit vielen Halten)
SELECT linien_text, verkehrsmittel_gruppe, count(*) AS halte,
       round(median(ab_verspaetung_min), 2) AS median_verspaetung_min
FROM halt
WHERE ab_status = 'REAL'
GROUP BY ALL
HAVING count(*) > 5000
ORDER BY median_verspaetung_min DESC
LIMIT 15;

-- 4) Verspaetung pro Stunde und Kanton (Grundlage fuer den Join mit stuendlichen Wetterdaten)
SELECT date_trunc('hour', h.ab_soll) AS stunde, s.kanton,
       count(*) AS halte,
       round(median(h.ab_verspaetung_min), 2) AS median_verspaetung_min
FROM halt h
JOIN haltestelle s ON s.bpuic = h.bpuic_haltestelle
WHERE h.ab_status = 'REAL'
GROUP BY ALL
ORDER BY stunde, s.kanton
LIMIT 24;
