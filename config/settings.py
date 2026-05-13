"""
config/settings.py
~~~~~~~~~~~~~~~~~~
Centralised configuration for the Bangladesh Flight Price pipeline.
"""
from __future__ import annotations

# ─── Database Connection IDs (must match Airflow Connections) ─
MYSQL_CONN_ID       = "mysql_staging"
POSTGRES_CONN_ID    = "postgres_analytics"

# ─── Table Names ─────────────────────────────────────────────
MYSQL_RAW_TABLE         = "raw_flight_prices"
MYSQL_VALIDATED_TABLE   = "validated_flight_prices"
MYSQL_AUDIT_TABLE       = "validation_audit"
MYSQL_RUNS_TABLE        = "pipeline_runs"

PG_FACT_TABLE               = "fact_flight_prices"
PG_KPI_AVG_FARE             = "kpi_avg_fare_by_airline"
PG_KPI_SEASONAL             = "kpi_seasonal_fare_variation"
PG_KPI_BOOKING_COUNT        = "kpi_booking_count_by_airline"
PG_KPI_POPULAR_ROUTES       = "kpi_popular_routes"
PG_KPI_ROUTE_AIRLINE        = "kpi_route_airline_performance"

# ─── Source Data ─────────────────────────────────────────────
CSV_FILE_PATH = "/opt/airflow/data/Flight_Price_Dataset_of_Bangladesh.csv"

# ─── CSV Column Mapping ───────────────────────────────────────
# Maps raw CSV headers → normalised internal names.
# Adjust if the Kaggle file ships with slightly different casing.
CSV_COLUMN_MAP: dict[str, str] = {
    "Airline":           "airline",
    "Source":            "source",
    "Destination":       "destination",
    "Departure Time":    "departure_time",
    "Arrival Time":      "arrival_time",
    "Duration":          "duration",
    "Stops":             "stops",
    "Base Fare":         "base_fare",
    "Tax & Surcharge":   "tax_and_surcharge",
    "Total Fare":        "total_fare",
    "Date":              "travel_date",
    "Class":             "booking_class",
}

REQUIRED_COLUMNS = [
    "airline", "source", "destination",
    "base_fare", "tax_and_surcharge", "total_fare",
]

# ─── Valid Bangladeshi City Names ─────────────────────────────
VALID_CITIES: set[str] = {
    "Dhaka", "Chittagong", "Sylhet", "Cox's Bazar",
    "Jessore", "Barisal", "Rajshahi", "Comilla",
    "Saidpur", "Jashore",
}

# ─── Season Definitions ───────────────────────────────────────
# Each entry: (label, list_of_(month, day_start, day_end) tuples)
# For simplicity the date ranges are (month_start, day_start) →
# (month_end, day_end).  Multi-month windows span across entries.
PEAK_SEASONS: list[dict] = [
    {
        "label": "Eid al-Fitr",
        "windows": [
            # Approximate Gregorian windows for 2023-2025
            {"month_start": 4, "day_start": 19, "month_end": 4, "day_end": 26},
            {"month_start": 4, "day_start":  8, "month_end": 4, "day_end": 15},
        ],
    },
    {
        "label": "Eid al-Adha",
        "windows": [
            {"month_start": 6, "day_start": 26, "month_end": 7, "day_end":  3},
            {"month_start": 6, "day_start": 15, "month_end": 6, "day_end": 22},
        ],
    },
    {
        "label": "Winter Holidays",
        "windows": [
            {"month_start": 12, "day_start": 20, "month_end": 12, "day_end": 31},
            {"month_start":  1, "day_start":  1, "month_end":  1, "day_end":  5},
        ],
    },
    {
        "label": "Pohela Boishakh",
        "windows": [
            {"month_start": 4, "day_start": 12, "month_end": 4, "day_end": 16},
        ],
    },
]

# ─── KPI: Top-N routes ───────────────────────────────────────
TOP_N_ROUTES = 20

# ─── Batch sizes for bulk inserts ────────────────────────────
MYSQL_BATCH_SIZE    = 5_000
POSTGRES_BATCH_SIZE = 5_000

# ─── DAG default args ────────────────────────────────────────
from datetime import datetime, timedelta

DAG_DEFAULT_ARGS: dict = {
    "owner":            "data_engineering",
    "depends_on_past":  False,
    "email_on_failure": False,
    "email_on_retry":   False,
    "retries":          2,
    "retry_delay":      timedelta(minutes=5),
    "start_date":       datetime(2024, 1, 1),
}