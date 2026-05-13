-- CREATE DATABASE flight_analytics;

-- \c flight_analytics;

-- -- RAW LAYER
-- CREATE TABLE raw_flights (
--     id SERIAL PRIMARY KEY,
--     airline TEXT,
--     source TEXT,
--     destination TEXT,
--     departure_time TEXT,
--     arrival_time TEXT,
--     duration TEXT,
--     stops TEXT,
--     base_fare NUMERIC,
--     tax_and_surcharge NUMERIC,
--     total_fare NUMERIC,
--     travel_date DATE,
--     booking_class TEXT,
--     load_timestamp TIMESTAMP DEFAULT NOW(),
--     pipeline_run_id TEXT
-- );

-- -- CLEAN LAYER
-- CREATE TABLE cleaned_flights (
--     id SERIAL PRIMARY KEY,
--     raw_id INT,
--     airline TEXT,
--     source TEXT,
--     destination TEXT,
--     base_fare NUMERIC,
--     tax_and_surcharge NUMERIC,
--     total_fare NUMERIC,
--     travel_date DATE,
--     is_peak_season INT,
--     season_label TEXT,
--     validation_status TEXT,
--     pipeline_run_id TEXT
-- );

-- FIX: Removed 'CREATE DATABASE' and '\c' — the DB is already created
--       by the POSTGRES_DB environment variable in docker-compose.yml.
--       This script runs inside flight_analytics automatically.

-- RAW LAYER
CREATE TABLE IF NOT EXISTS raw_flights (
    id SERIAL PRIMARY KEY,
    airline TEXT,
    source TEXT,
    destination TEXT,
    departure_time TEXT,
    arrival_time TEXT,
    duration TEXT,
    stops TEXT,
    base_fare NUMERIC,
    tax_and_surcharge NUMERIC,
    total_fare NUMERIC,
    travel_date DATE,
    booking_class TEXT,
    load_timestamp TIMESTAMP DEFAULT NOW(),
    pipeline_run_id TEXT
);

-- CLEAN LAYER
CREATE TABLE IF NOT EXISTS cleaned_flights (
    id SERIAL PRIMARY KEY,
    raw_id INT,
    airline TEXT,
    source TEXT,
    destination TEXT,
    base_fare NUMERIC,
    tax_and_surcharge NUMERIC,
    total_fare NUMERIC,
    travel_date DATE,
    is_peak_season INT,
    season_label TEXT,
    validation_status TEXT,
    pipeline_run_id TEXT
);