-- =============================================================================
-- schema.sql: Datenbankschema fuer das Projekt oev-wetter (Gruppe 4, DAENG HS26)
--
-- Zweck:     Legt alle Tabellen in DuckDB an (Ist-Daten, Haltestellen,
--            Wetterstationen, Wettermessungen, Zuordnung, Ingestion-Log).
--            Das Skript ist idempotent (CREATE ... IF NOT EXISTS) und kann
--            beliebig oft ausgefuehrt werden.
-- Zeitzone:  Alle Zeitpunkte sind TIMESTAMPTZ (ISO 8601 mit Zeitzone).
--            Die Ist-Daten liegen in Lokalzeit (Europe/Zurich) vor und werden
--            beim Laden umgerechnet; damit ist die Sommerzeitumstellung am
--            29.3.2026 korrekt abgebildet. Der Betriebstag bleibt ein DATE.
-- Status:    ENTWURF, Spaltennamen der Wettertabellen mit Paket C abstimmen.
--
-- Quellen (APA 7):
-- DuckDB Foundation. (2026). DuckDB documentation: CREATE TABLE statement.
--     https://duckdb.org/docs/sql/statements/create_table
-- SBB AG, Geschaeftsstelle Systemaufgaben Kundeninformation. (2026). Ist-Daten v2
--     [Datensatz]. Open-Data-Plattform Mobilitaet Schweiz.
--     https://data.opentransportdata.swiss/dataset/ist-daten-v2
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Haltestellen (aus Haltestellen-Stammdaten, geliefert von Paket C)
-- Schluessel: BPUIC (Betriebspunkt-Nummer, wie in den Ist-Daten).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS haltestelle (
    bpuic            VARCHAR PRIMARY KEY,     -- 7-stellige Haltestellennummer (= halt.bpuic_haltestelle)
    sloid            VARCHAR,                 -- Schweizer Location-ID (falls vorhanden)
    name             VARCHAR NOT NULL,        -- Haltestellenname
    kanton           VARCHAR(2) NOT NULL,     -- 'TG', 'SG', 'AR' oder 'AI'
    lat              DOUBLE,                  -- Breitengrad (WGS84)
    lon              DOUBLE,                  -- Laengengrad (WGS84)
    hoehe_m          DOUBLE                   -- Hoehe ueber Meer in Metern
);

-- -----------------------------------------------------------------------------
-- Halt: eine Zeile pro Fahrt und Halt (Granularitaet der Ist-Daten).
-- Schluessel: Betriebstag + Fahrt + Kante (BPUIC) + laufende Nummer. Die Nummer
-- ist noetig, weil eine Fahrt dieselbe Kante mehrmals anfahren kann (Ringlinien).
-- In v2 ist BPUIC oft 9-stellig (Haltestelle + 2 Ziffern Kante/Gleis), z. B.
-- 850978002 = Haltestelle 8509780, Kante 02. Fuer Joins mit den Stammdaten dient
-- deshalb die 7-stellige Haltestellennummer bpuic_haltestelle.
-- Kein Fremdschluessel auf haltestelle, damit ein Tag auch ungefiltert
-- (vor Eintreffen der Haltestellenliste) geladen werden kann.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS halt (
    betriebstag          DATE NOT NULL,        -- BETRIEBSTAG
    fahrt_bezeichner     VARCHAR NOT NULL,     -- FAHRT_BEZEICHNER
    bpuic                VARCHAR NOT NULL,     -- BPUIC wie geliefert (7- oder 9-stellig)
    halt_nr              INTEGER NOT NULL,     -- 1, 2, ... falls die Fahrt die Kante mehrmals anfaehrt
    bpuic_haltestelle    VARCHAR NOT NULL,     -- 7-stellige Haltestellennummer (Join auf haltestelle)
    sloid                VARCHAR,              -- SLOID (neu in v2)
    haltestellen_name    VARCHAR,              -- HALTESTELLEN_NAME
    betreiber_abk        VARCHAR,              -- BETREIBER_ABK
    produkt_id           VARCHAR,              -- PRODUKT_ID vereinheitlicht ('Zug', 'Bus', 'Zahnradbahn')
    verkehrsmittel_gruppe VARCHAR,             -- 'Bahn' oder 'Bus' (fuer H2)
    verkehrsmittel       VARCHAR,              -- VERKEHRSMITTEL_TEXT (z. B. 'S', 'IR', 'B')
    linien_id            VARCHAR,              -- LINIEN_ID
    linien_text          VARCHAR,              -- LINIEN_TEXT
    zusatzfahrt          BOOLEAN,              -- ZUSATZFAHRT_TF
    faellt_aus           BOOLEAN,              -- FAELLT_AUS_TF
    durchfahrt           BOOLEAN,              -- DURCHFAHRT_TF
    an_soll              TIMESTAMPTZ,          -- ANKUNFTSZEIT (Fahrplan)
    an_ist               TIMESTAMPTZ,          -- AN_PROGNOSE (Ist bzw. Prognose)
    an_status            VARCHAR,              -- AN_PROGNOSE_STATUS (REAL, GESCHAETZT, PROGNOSE, UNBEKANNT)
    ab_soll              TIMESTAMPTZ,          -- ABFAHRTSZEIT (Fahrplan)
    ab_ist               TIMESTAMPTZ,          -- AB_PROGNOSE
    ab_status            VARCHAR,              -- AB_PROGNOSE_STATUS
    -- Abgeleitete Verspaetungen in Minuten (Ist minus Soll), beim Laden berechnet.
    -- Welche davon (Ankunft oder Abfahrt) in die Analyse kommt, legt Paket A fest.
    an_verspaetung_min   DOUBLE,
    ab_verspaetung_min   DOUBLE,
    quelle_datei         VARCHAR,              -- Name der Tagesdatei (Herkunft)
    PRIMARY KEY (betriebstag, fahrt_bezeichner, bpuic, halt_nr)
);

-- -----------------------------------------------------------------------------
-- Wetterstationen und -messungen (Spalten legt Paket C fest, hier Vorschlag)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS wetterstation (
    station_abk      VARCHAR PRIMARY KEY,     -- MeteoSchweiz-Kuerzel, z. B. 'STG'
    name             VARCHAR NOT NULL,
    kanton           VARCHAR(2),
    lat              DOUBLE,
    lon              DOUBLE,
    hoehe_m          DOUBLE
);

CREATE TABLE IF NOT EXISTS wettermessung (
    station_abk          VARCHAR NOT NULL,     -- Fremdschluessel auf wetterstation
    zeitpunkt            TIMESTAMPTZ NOT NULL, -- Ende des Messintervalls (Stundenwert)
    niederschlag_mm      DOUBLE,               -- Niederschlag Stundensumme
    temperatur_c         DOUBLE,               -- Lufttemperatur 2 m
    schneehoehe_cm       DOUBLE,               -- Schneehoehe (falls verfuegbar)
    wind_kmh             DOUBLE,               -- Windgeschwindigkeit
    PRIMARY KEY (station_abk, zeitpunkt)
);

-- Zuordnung Haltestelle -> naechste passende Wetterstation (raeumlicher Join, Paket C)
CREATE TABLE IF NOT EXISTS haltestelle_station (
    bpuic            VARCHAR PRIMARY KEY,     -- 7-stellige Haltestellennummer
    station_abk      VARCHAR NOT NULL,
    distanz_km       DOUBLE,
    hoehendiff_m     DOUBLE
);

-- -----------------------------------------------------------------------------
-- Ingestion-Log: eine Zeile pro verarbeitetem Tag. Grundlage fuer Idempotenz
-- (bereits geladene Tage werden uebersprungen) und fuer die Dokumentation.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ingest_log (
    quelle           VARCHAR NOT NULL,         -- 'istdaten' oder 'wetter'
    betriebstag      DATE NOT NULL,
    status           VARCHAR NOT NULL,         -- 'ok' oder 'fehler'
    zeilen_roh       BIGINT,                   -- Zeilen vor dem Filter
    zeilen_gefiltert BIGINT,                   -- Zeilen nach dem Filter
    dauer_s          DOUBLE,
    meldung          VARCHAR,
    geladen_am       TIMESTAMPTZ DEFAULT current_timestamp,
    filter           VARCHAR,                  -- Kennung des Haltestellenfilters ('keiner' oder Pruefsumme der Liste)
    PRIMARY KEY (quelle, betriebstag)
);
-- Fuer Datenbanken, die vor Einfuehrung der Spalte angelegt wurden
ALTER TABLE ingest_log ADD COLUMN IF NOT EXISTS filter VARCHAR;

-- Indizes fuer die typischen Abfragen (Zeit und Haltestelle)
CREATE INDEX IF NOT EXISTS idx_halt_ab_soll ON halt (ab_soll);
CREATE INDEX IF NOT EXISTS idx_halt_bpuic   ON halt (bpuic_haltestelle);
