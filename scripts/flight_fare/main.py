"""
main.py
───────
Pipeline orchestrator for the Flight Fare Prediction project.

This file contains ZERO business logic.  It only:
  1. Calls each module in the correct order
  2. Passes outputs between modules
  3. Handles top-level timing and reporting

To swap any stage, change that module — not this file.
To run the pipeline:
    python main.py
"""

import warnings
from datetime import datetime

import numpy as np
import pandas as pd

import sys
# sys.stdout.reconfigure(encoding='utf-8')

warnings.filterwarnings("ignore")
np.random.seed(42)

# ── Pipeline modules ─────────────────────────────────────────────────────────
# from flight_fare import config
# from flight_fare.utils import get_logger
# from flight_fare.data import load, clean
# from flight_fare.features import engineer
# from flight_fare.eda import run_full_eda
# from flight_fare.preprocessing import prepare
# from flight_fare.models import train_all, tune_xgboost
# from flight_fare.visualisation import plot_all_results
# from flight_fare.artefacts import save_all

import config
from utils.logger import get_logger
from data.loader import load
from data.cleaner import clean
# from features import engineer
from features.engineer import engineer
from eda.analysis import run_full_eda #, inspect_structure
from preprocessing.splitter import prepare
from models.trainer import train_all
from models.tuner import tune_xgboost
from visualisation.results import plot_all_results
from artefacts.persistence import save_all

log = get_logger(__name__, log_file=config.OUT_DIR / "pipeline.log")


def main() -> None:
    t0 = datetime.now()
    log.info("═" * 55)
    log.info("  Flight Fare Prediction Pipeline — START")
    log.info("═" * 55)

    # ── Stage 1: Data acquisition ────────────────────────────────────────────
    df_raw = load()     

    # # ── Stage 1.5: Raw structure inspection────────────────────────────────────────────
    # inspect_structure(df_raw)                    

    # ── Stage 2: Cleaning ────────────────────────────────────────────────────
    df_clean = clean(df_raw)

    # ── Stage 3: Feature engineering ─────────────────────────────────────────
    df = engineer(df_clean)

    # ── Stage 4: EDA ─────────────────────────────────────────────────────────
    run_full_eda(df)

    # ── Stage 5: Preprocessing / split ───────────────────────────────────────
    data = prepare(df)

    # ── Stage 6–7: Train & cross-validate all models ─────────────────────────
    results_df, trained_models = train_all(data)

    # ── Stage 8: Hyperparameter tuning (XGBoost) ─────────────────────────────
    best_model, tuned_metrics = tune_xgboost(data)

    # Append tuned result to comparison table
    full_results = pd.concat(
        [results_df, pd.DataFrame([tuned_metrics])],
        ignore_index=True,
    )

    # ── Stage 9: Visualise results ────────────────────────────────────────────
    plot_all_results(
        results_df=full_results,
        best_model=best_model,
        X_test=data.X_test,
        y_test=data.y_test,
        feature_names=data.feature_names,
        X_train_sc=data.X_train_sc,
        y_train=data.y_train,
        X_test_sc=data.X_test_sc,
    )

    # ── Stage 10: Save artefacts ──────────────────────────────────────────────
    save_all(best_model, data.scaler, full_results)

    # ── Final report ─────────────────────────────────────────────────────────
    elapsed = (datetime.now() - t0).total_seconds()
    log.info("═" * 55)
    log.info("  Pipeline complete in %.1f s", elapsed)
    log.info("  Outputs → %s", config.OUT_DIR)
    log.info("═" * 55)

    print("\n" + "═" * 60)
    print("  MODEL COMPARISON  (sorted by R²)")
    print("═" * 60)
    print(
        full_results
        .sort_values("R²", ascending=False)
        .to_string(index=False)
    )
    print("═" * 60)


if __name__ == "__main__":
    main()
