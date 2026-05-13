SELECT
    airline,
    CASE
        WHEN EXTRACT(MONTH FROM travel_date) IN (4,6,12) THEN 'Peak'
        ELSE 'Off-Peak'
    END AS season,
    AVG(total_fare) AS avg_fare
FROM {{ ref('stg_flights') }}
GROUP BY airline, season