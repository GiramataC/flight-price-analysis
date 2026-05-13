-- SELECT
--     id,
--     airline,
--     source,
--     destination,
--     base_fare,
--     tax_and_surcharge,
--     total_fare,
--     travel_date
-- FROM raw_flights

SELECT
    airline,
    source,
    destination,
    departure_time,
    arrival_time,
    duration,
    stops,
    base_fare,
    tax_and_surcharge,
    total_fare,
    booking_class,
    pipeline_run_id,
    load_timestamp
FROM raw_flights