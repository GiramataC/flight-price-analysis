import pandas as pd
from sqlalchemy import create_engine
import logging

logger = logging.getLogger(__name__)


def load_kpis_to_postgres(kpi_cache_key, postgres_conn_id):
    """
    Loads KPI outputs into PostgreSQL analytics tables.
    """

    engine = create_engine(
        "postgresql+psycopg2://airflow:airflow@postgres-analytics:5432/flight_analytics"
    )

    from scripts.kpi_computation import _KPI_CACHE

    kpis = _KPI_CACHE.get(kpi_cache_key)

    if not kpis:
        raise ValueError("No KPI data found for run")

    # ── Write each KPI table ──
    kpis["kpi_avg_fare_by_airline"].to_sql("kpi_avg_fare_by_airline", engine, if_exists="replace", index=False)

    kpis["kpi_seasonal_fare_variation"].to_sql("kpi_seasonal_fare_variation", engine, if_exists="replace", index=False)

    kpis["kpi_booking_count_by_airline"].to_sql("kpi_booking_count_by_airline", engine, if_exists="replace", index=False)

    kpis["kpi_popular_routes"].to_sql("kpi_popular_routes", engine, if_exists="replace", index=False)

    kpis["kpi_route_airline_performance"].to_sql("kpi_route_airline_performance", engine, if_exists="replace", index=False)

    logger.info("Loaded all KPIs into PostgreSQL successfully")