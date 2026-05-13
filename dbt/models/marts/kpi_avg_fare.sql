SELECT
    airline,
    AVG(total_fare) AS avg_fare,
    COUNT(*) AS bookings
FROM {{ ref('stg_flights') }}
GROUP BY airline