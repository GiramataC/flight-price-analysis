"""
scripts/kpi_computation.py
~~~~~~~~~~~~~~~~~~~~~~~~~~
Reads validated data from MySQL and computes all KPIs,
then writes them back to MySQL-side staging views / tables
before the load step moves everything to PostgreSQL.

KPIs
----
1.  Average Fare by Airline
2.  Seasonal Fare Variation  (peak vs off-peak, per airline)
3.  Booking Count by Airline
4.  Most Popular Routes      (top-N source-destination pairs)
5.  Route × Airline Performance
"""
from __future__ import annotations

import logging
from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine

logger = logging.getLogger(__name__)


# ─── helpers ─────────────────────────────────────────────────

def _load_validated(engine, validated_table: str, run_id: str) -> pd.DataFrame:
    df = pd.read_sql(
        f"SELECT * FROM {validated_table} WHERE pipeline_run_id = %s",
        con=engine,
        params=(run_id,),
    )
    logger.info("Loaded %d validated rows for KPI computation", len(df))
    return df


# ─── KPI 1: Average Fare by Airline ──────────────────────────

def kpi_avg_fare_by_airline(df: pd.DataFrame, run_id: str) -> pd.DataFrame:
    """
    Per airline: avg base fare, avg tax, avg total fare, min/max, count.
    """
    grp = df.groupby("airline", as_index=False).agg(
        avg_base_fare  = ("base_fare",         "mean"),
        avg_tax        = ("tax_and_surcharge",  "mean"),
        avg_total_fare = ("total_fare",         "mean"),
        min_fare       = ("total_fare",         "min"),
        max_fare       = ("total_fare",         "max"),
        booking_count  = ("total_fare",         "count"),
    )
    grp = grp.round(2)
    grp["pipeline_run_id"] = run_id
    grp["computed_at"]     = datetime.utcnow()
    logger.info("KPI 1 – avg fare by airline: %d airlines", len(grp))
    return grp


# ─── KPI 2: Seasonal Fare Variation ──────────────────────────

def kpi_seasonal_fare_variation(df: pd.DataFrame, run_id: str) -> pd.DataFrame:
    """
    Per (airline, season_label, is_peak):
      - avg total fare
      - booking count
      - fare_premium_pct vs overall airline off-peak avg
    """
    grp = df.groupby(["airline", "season_label", "is_peak_season"], as_index=False).agg(
        avg_total_fare = ("total_fare", "mean"),
        booking_count  = ("total_fare", "count"),
    )

    # Off-peak baseline per airline
    offpeak = grp[grp["is_peak_season"] == 0][["airline", "avg_total_fare"]].copy()
    offpeak.columns = ["airline", "offpeak_avg"]

    grp = grp.merge(offpeak, on="airline", how="left")
    grp["fare_premium_pct"] = (
        (grp["avg_total_fare"] - grp["offpeak_avg"]) / grp["offpeak_avg"].replace(0, pd.NA) * 100
    ).round(2)
    grp = grp.drop(columns=["offpeak_avg"])

    grp = grp.rename(columns={"is_peak_season": "is_peak"})
    grp = grp.round({"avg_total_fare": 2})
    grp["pipeline_run_id"] = run_id
    grp["computed_at"]     = datetime.utcnow()
    logger.info("KPI 2 – seasonal variation: %d rows", len(grp))
    return grp


# ─── KPI 3: Booking Count by Airline ─────────────────────────

def kpi_booking_count_by_airline(df: pd.DataFrame, run_id: str) -> pd.DataFrame:
    """
    Per airline: total, peak, off-peak bookings + market share %.
    """
    total_bookings = len(df)

    all_bk = df.groupby("airline", as_index=False)["total_fare"].count().rename(
        columns={"total_fare": "total_bookings"}
    )
    peak_bk = (
        df[df["is_peak_season"] == 1]
        .groupby("airline", as_index=False)["total_fare"]
        .count()
        .rename(columns={"total_fare": "peak_bookings"})
    )
    grp = all_bk.merge(peak_bk, on="airline", how="left")
    grp["peak_bookings"]    = grp["peak_bookings"].fillna(0).astype(int)
    grp["offpeak_bookings"] = grp["total_bookings"] - grp["peak_bookings"]
    grp["market_share_pct"] = (grp["total_bookings"] / total_bookings * 100).round(4)

    grp["pipeline_run_id"] = run_id
    grp["computed_at"]     = datetime.utcnow()
    logger.info("KPI 3 – booking count by airline: %d airlines", len(grp))
    return grp


# ─── KPI 4: Most Popular Routes ──────────────────────────────

def kpi_popular_routes(df: pd.DataFrame, run_id: str, top_n: int = 20) -> pd.DataFrame:
    """
    Top N source-destination pairs by booking count.
    Includes avg/min/max fare and the dominant airline per route.
    """
    grp = df.groupby(["source", "destination"], as_index=False).agg(
        booking_count  = ("total_fare", "count"),
        avg_total_fare = ("total_fare", "mean"),
        min_fare       = ("total_fare", "min"),
        max_fare       = ("total_fare", "max"),
    )

    # Dominant airline per route
    top_airline = (
        df.groupby(["source", "destination", "airline"], as_index=False)
        .size()
        .sort_values("size", ascending=False)
        .drop_duplicates(subset=["source", "destination"])
        [["source", "destination", "airline"]]
        .rename(columns={"airline": "top_airline"})
    )
    grp = grp.merge(top_airline, on=["source", "destination"], how="left")

    grp = grp.sort_values("booking_count", ascending=False).head(top_n)
    grp["rank"]  = range(1, len(grp) + 1)
    grp["route"] = grp["source"] + " → " + grp["destination"]
    grp = grp.round({"avg_total_fare": 2, "min_fare": 2, "max_fare": 2})

    grp["pipeline_run_id"] = run_id
    grp["computed_at"]     = datetime.utcnow()
    logger.info("KPI 4 – popular routes: top %d of %d routes", len(grp), len(df[["source","destination"]].drop_duplicates()))
    return grp


# ─── KPI 5: Route × Airline Performance ──────────────────────

def kpi_route_airline_performance(df: pd.DataFrame, run_id: str) -> pd.DataFrame:
    """
    For each (source, destination, airline): booking count, avg fare,
    and that airline's share of bookings on that route.
    """
    grp = df.groupby(["source", "destination", "airline"], as_index=False).agg(
        booking_count  = ("total_fare", "count"),
        avg_total_fare = ("total_fare", "mean"),
    )

    route_totals = (
        grp.groupby(["source", "destination"])["booking_count"]
        .transform("sum")
    )
    grp["route_share_pct"] = (grp["booking_count"] / route_totals * 100).round(4)
    grp = grp.round({"avg_total_fare": 2})

    grp["pipeline_run_id"] = run_id
    grp["computed_at"]     = datetime.utcnow()
    logger.info("KPI 5 – route×airline: %d rows", len(grp))
    return grp


# ─── Entry-point called by Airflow ───────────────────────────

def compute_all_kpis(
    mysql_uri: str,
    validated_table: str,
    pipeline_run_id: str,
    top_n_routes: int = 20,
) -> dict:
    """
    Compute all KPIs and return as a dict of DataFrames (to be
    loaded by the next task into PostgreSQL).
    """
    engine = create_engine(mysql_uri, pool_pre_ping=True)
    df = _load_validated(engine, validated_table, pipeline_run_id)

    if df.empty:
        raise ValueError(f"No validated rows found for run_id={pipeline_run_id}")

    kpis = {
        "kpi_avg_fare_by_airline":        kpi_avg_fare_by_airline(df, pipeline_run_id),
        "kpi_seasonal_fare_variation":    kpi_seasonal_fare_variation(df, pipeline_run_id),
        "kpi_booking_count_by_airline":   kpi_booking_count_by_airline(df, pipeline_run_id),
        "kpi_popular_routes":             kpi_popular_routes(df, pipeline_run_id, top_n_routes),
        "kpi_route_airline_performance":  kpi_route_airline_performance(df, pipeline_run_id),
        "_fact_data":                     df,  # passed through for PG load
    }

    # Summary statistics for XCom
    summary = {
        "run_id":                     pipeline_run_id,
        "total_rows":                 len(df),
        "airlines":                   int(df["airline"].nunique()),
        "routes":                     int(df.groupby(["source","destination"]).ngroups),
        "peak_rows":                  int((df["is_peak_season"] == 1).sum()),
        "kpi_avg_fare_rows":          len(kpis["kpi_avg_fare_by_airline"]),
        "kpi_seasonal_rows":          len(kpis["kpi_seasonal_fare_variation"]),
        "kpi_booking_count_rows":     len(kpis["kpi_booking_count_by_airline"]),
        "kpi_popular_routes_rows":    len(kpis["kpi_popular_routes"]),
        "kpi_route_airline_rows":     len(kpis["kpi_route_airline_performance"]),
    }
    logger.info("KPI computation complete: %s", summary)
    # Store DataFrames in a module-level cache keyed by run_id
    # (Airflow tasks share memory within a worker process)
    _KPI_CACHE[pipeline_run_id] = kpis
    return {
    "summary": summary,
    "kpis": kpis
       }


# Module-level cache so the next task can access DataFrames
_KPI_CACHE: dict[str, dict] = {}
