SELECT
    source,
    destination,
    COUNT(*) AS bookings,
    AVG(total_fare) AS avg_fare
FROM {{ ref('stg_flights') }}
GROUP BY source, destination
ORDER BY bookings DESC