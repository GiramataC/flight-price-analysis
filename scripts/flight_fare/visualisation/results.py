"""
visualisation/results.py
────────────────────────
Post-training evaluation visualisations.

Fixes:
- Uses safe column handling
- Compatible with current PreprocessedData structure
- Works with tree models (XGBoost, RF, etc.)
- Avoids missing feature crashes
"""

import numpy as np
import pandas as pd

from utils.logger import get_logger

log = get_logger(__name__)


# ─────────────────────────────────────────────
# MODEL COMPARISON (TEXT OUTPUT)
# ─────────────────────────────────────────────

def print_model_comparison(results_df: pd.DataFrame) -> None:
    """Print sorted model leaderboard."""

    log.info("── MODEL COMPARISON ─────────────────────────")

    if results_df is None or results_df.empty:
        log.warning("Empty results dataframe")
        return

    sorted_df = results_df.sort_values("R²", ascending=False)

    log.info("\n%s", sorted_df.to_string(index=False))


# ─────────────────────────────────────────────
# FEATURE IMPORTANCE
# ─────────────────────────────────────────────

def feature_importance(best_model, feature_names, top_n: int = 15) -> None:
    """
    Print top feature importance (works for tree-based models only).
    """

    log.info("── FEATURE IMPORTANCE ───────────────────────")

    if not hasattr(best_model, "feature_importances_"):
        log.warning("Model does not support feature_importances_")
        return

    importance = pd.Series(
        best_model.feature_importances_,
        index=feature_names
    ).sort_values(ascending=False)

    log.info("Top %d Features:\n%s", top_n, importance.head(top_n).to_string())


# ─────────────────────────────────────────────
# PREDICTION SUMMARY
# ─────────────────────────────────────────────

def prediction_summary(model, X_test, y_test) -> None:
    """
    Basic prediction diagnostics (no plotting required).
    """

    log.info("── PREDICTION SUMMARY ───────────────────────")

    preds = model.predict(X_test)

    residuals = y_test - preds

    log.info("Mean Prediction Error: %.2f", residuals.mean())
    log.info("Std Error: %.2f", residuals.std())
    log.info("Min Error: %.2f | Max Error: %.2f",
             residuals.min(), residuals.max())


# ─────────────────────────────────────────────
# ROUTE INSIGHTS (SAFE VERSION)
# ─────────────────────────────────────────────

def route_insights(df: pd.DataFrame) -> None:
    """
    Analyze route-level fare patterns safely.
    """

    log.info("── ROUTE INSIGHTS ───────────────────────────")

    required = {"source", "destination", "total_fare_bdt"}

    if not required.issubset(df.columns):
        log.warning("Missing route columns → skipping route insights")
        return

    df = df.copy()
    df["route"] = df["source"] + " → " + df["destination"]

    top_routes = (
        df.groupby("route")["total_fare_bdt"]
        .mean()
        .sort_values(ascending=False)
        .head(10)
    )

    log.info("Top 10 Expensive Routes:\n%s", top_routes.to_string())


# ─────────────────────────────────────────────
# MAIN ORCHESTRATOR
# ─────────────────────────────────────────────

def plot_all_results(
    results_df,
    best_model,
    X_test,
    y_test,
    feature_names,
    X_train_sc,
    y_train,
    X_test_sc,
    df=None
) -> None:
    """
    Full post-training analysis pipeline.
    """

    log.info("── RESULTS ANALYSIS START ───────────────────")

    print_model_comparison(results_df)

    prediction_summary(best_model, X_test, y_test)

    feature_importance(best_model, feature_names)

    if df is not None:
        route_insights(df)

    log.info("── RESULTS ANALYSIS COMPLETE ────────────────")