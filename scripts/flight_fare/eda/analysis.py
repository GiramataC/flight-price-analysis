"""
eda/analysis.py
────────────────
# [CAPTURE]  buffer .info() → keeps all output routed through the logger
# [WARN]     null counts reflect true NaN only — encode-time nulls not caught here
# [NOTE]     describe(include="object") runs separately — pandas excludes these by default
# [CHECK]    head() = post-cleaner sanity check on values and column names
# [HEURISTIC] IQR × 1.5 flags candidates only — confirm outliers with domain context
"""

import pandas as pd
import numpy as np

from utils.logger import get_logger

log = get_logger(__name__)


# ─────────────────────────────────────────────
# STRUCTURE INSPECTION
# ─────────────────────────────────────────────

# def inspect_structure(df: pd.DataFrame) -> None:
#     """
#     Inspect the raw structure of the dataset using .info(), .describe(), and .head().

#     Initial Observations documented inline:
#     ─────────────────────────────────────────
#     * Missing data    : Flagged per column via .info() null counts.
#     * Outliers        : Visible in .describe() via min/max vs mean/std spread.
#     * Categorical cols: Identified as dtype=object; noted for encoding downstream.
#     * Numerical ranges: Captured in .describe() (min, max, mean, std, quartiles).

#     Assumptions & Limitations:
#     ─────────────────────────────────────────
#     * Assumes df has already passed through the cleaner (snake_case columns expected).
#     * .describe() covers numeric columns only; string columns need separate profiling.
#     * Outlier detection here is visual/heuristic — no automated IQR clipping is applied.
#     * Missing value counts from .info() may differ if dtypes are mixed (e.g. object
#       columns storing numeric strings won't appear as NaN).
#     """

#     log.info("── Structure Inspection ─────────────────────")

#     # ── Shape ────────────────────────────────────
#     log.info("Shape: %d rows × %d columns", *df.shape)

#     # ── .info() ──────────────────────────────────
#     # Shows dtypes, non-null counts → reveals missing data and type mismatches
#     log.info("── df.info() ────────────────────────────────")
#     import io
#     buffer = io.StringIO()
#     df.info(buf=buffer)
#     log.info("\n%s", buffer.getvalue())

#     # ── Missing data summary ──────────────────────
#     missing = df.isnull().sum()
#     missing_pct = (missing / len(df) * 100).round(2)
#     missing_report = pd.DataFrame({
#         "missing_count": missing,
#         "missing_pct": missing_pct
#     }).query("missing_count > 0").sort_values("missing_pct", ascending=False)

#     if missing_report.empty:
#         log.info("No missing values detected.")
#     else:
#         log.warning("Missing values found:\n%s", missing_report.to_string())

#     # ── .describe() ──────────────────────────────
#     # Numerical ranges, central tendency, spread → helps spot outliers
#     log.info("── df.describe() [numeric] ──────────────────")
#     log.info("\n%s", df.describe().to_string())

#     # Categorical columns described separately
#     cat_cols = df.select_dtypes(include="object").columns.tolist()
#     if cat_cols:
#         log.info("── df.describe() [categorical] ──────────────")
#         log.info("\n%s", df[cat_cols].describe().to_string())

#     # ── .head() ──────────────────────────────────
#     # First 5 rows — confirms column values look sensible after cleaning
#     log.info("── df.head() ────────────────────────────────")
#     log.info("\n%s", df.head().to_string())

#     # ── Dtype summary ────────────────────────────
#     log.info("── Column dtypes ────────────────────────────")
#     dtype_summary = df.dtypes.to_frame(name="dtype")
#     dtype_summary["kind"] = np.where(
#         df.dtypes == "object", "categorical", "numerical"
#     )
#     log.info("\n%s", dtype_summary.to_string())

#     # ── Outlier heuristic (IQR flag, numerical cols only) ────────────────
#     log.info("── Outlier Heuristic (IQR method) ───────────")
#     numeric_cols = df.select_dtypes(include=[np.number]).columns
#     for col in numeric_cols:
#         q1 = df[col].quantile(0.25)
#         q3 = df[col].quantile(0.75)
#         iqr = q3 - q1
#         n_outliers = ((df[col] < q1 - 1.5 * iqr) | (df[col] > q3 + 1.5 * iqr)).sum()
#         if n_outliers > 0:
#             log.warning("%-30s → %d potential outliers", col, n_outliers)
#         else:
#             log.info("%-30s → no outliers flagged", col)


# ─────────────────────────────────────────────
# KPI SUMMARY
# ─────────────────────────────────────────────

def print_kpis(df: pd.DataFrame) -> None:
    """Log key business KPIs safely."""

    log.info("── KPI Summary ─────────────────────────────")

    if "total_fare_bdt" not in df.columns:
        log.error("Missing target column: total_fare_bdt")
        return

    log.info("Rows: %d", len(df))
    log.info("Avg Fare: ৳%.2f", df["total_fare_bdt"].mean())
    log.info("Median Fare: ৳%.2f", df["total_fare_bdt"].median())
    log.info("Std Fare: ৳%.2f", df["total_fare_bdt"].std())

    # -------------------------
    # Top route (SAFE)
    # -------------------------
    if {"source", "destination"}.issubset(df.columns):
        df["route"] = df["source"].astype(str) + " → " + df["destination"].astype(str)
        top_route = df["route"].value_counts().idxmax()
        log.info("Most popular route: %s", top_route)
    else:
        log.warning("Route columns missing → skipping route KPI")

    # -------------------------
    # Airline stats
    # -------------------------
    if "airline" in df.columns:
        airline_avg = (
            df.groupby("airline")["total_fare_bdt"]
            .mean()
            .sort_values(ascending=False)
        )
        log.info("Avg fare by airline:\n%s", airline_avg.to_string())
    else:
        log.warning("Airline column missing → skipping airline KPI")
    # Top 5 most expensive routes
    if "route" in df.columns:
        top5 = (
            df.groupby("route")["total_fare_bdt"]
            .mean()
            .sort_values(ascending=False)
            .head(5)
        )
        log.info("Top 5 most expensive routes:\n%s", top5.to_string())


# ─────────────────────────────────────────────
# BASIC DISTRIBUTION ANALYSIS
# ─────────────────────────────────────────────

def fare_distribution(df: pd.DataFrame) -> None:
    """Simple numeric insights (no plotting)."""

    log.info("── Fare Distribution Analysis ───────────────")

    if "total_fare_bdt" not in df.columns:
        log.error("Missing total_fare_bdt")
        return

    q1 = df["total_fare_bdt"].quantile(0.25)
    q3 = df["total_fare_bdt"].quantile(0.75)

    log.info("Q1: %.2f | Q3: %.2f | IQR: %.2f", q1, q3, q3 - q1)


# ─────────────────────────────────────────────
# SEASON ANALYSIS
# ─────────────────────────────────────────────

def season_analysis(df: pd.DataFrame) -> None:
    """Check fare variation across seasons safely."""

    log.info("── Season Analysis ──────────────────────────")

    if "season" not in df.columns:
        log.warning("Season column missing → skipping")
        return

    if "total_fare_bdt" not in df.columns:
        return

    season_avg = df.groupby("season")["total_fare_bdt"].mean()

    log.info("Average fare by season:\n%s", season_avg.to_string())


# ─────────────────────────────────────────────
# CORRELATION ANALYSIS
# ─────────────────────────────────────────────

def correlation_analysis(df: pd.DataFrame) -> None:
    """Compute correlation safely on numeric columns only."""

    log.info("── Correlation Analysis ─────────────────────")

    numeric_df = df.select_dtypes(include=[np.number])

    if numeric_df.shape[1] < 2:
        log.warning("Not enough numeric columns for correlation")
        return

    corr = numeric_df.corr()

    # show strongest relationships with target if exists
    if "total_fare_bdt" in corr.columns:
        target_corr = corr["total_fare_bdt"].sort_values(ascending=False)
        log.info("Correlation with target:\n%s", target_corr.to_string())


# ─────────────────────────────────────────────
# MAIN ORCHESTRATOR
# ─────────────────────────────────────────────

def run_full_eda(df: pd.DataFrame) -> None:
    """
    Run full EDA pipeline safely.
    No crashes if columns are missing.

    Pipeline order:
        1. inspect_structure  ← NEW: raw structure, missing data, outlier flags
        2. print_kpis
        3. fare_distribution
        4. season_analysis
        5. correlation_analysis
    """

    log.info("── EDA START ────────────────────────────────")

    # inspect_structure(df)       # ← runs first: ground-truth view of the data
    print_kpis(df)
    fare_distribution(df)
    season_analysis(df)
    correlation_analysis(df)

    log.info("EDA COMPLETE")