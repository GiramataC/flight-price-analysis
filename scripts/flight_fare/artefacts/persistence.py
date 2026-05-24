"""
artefacts/persistence.py
────────────────────────
Save and reload trained models, scalers, and result tables.

Having a dedicated persistence module means:
  • Path management stays in one place
  • Callers never import joblib directly
  • Loading (for inference) mirrors saving — consistent API
"""

import joblib
import pandas as pd

import config
from utils.logger import get_logger

log = get_logger(__name__)


def save_model(model, filename: str = "best_model_xgboost.pkl") -> None:
    path = config.OUT_DIR / filename
    config.OUT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    log.info("Model saved → %s", path)


def load_model(filename: str = "best_model_xgboost.pkl"):
    path = config.OUT_DIR / filename
    model = joblib.load(path)
    log.info("Model loaded ← %s", path)
    return model


def save_scaler(scaler, filename: str = "feature_scaler.pkl") -> None:
    path = config.OUT_DIR / filename
    config.OUT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(scaler, path)
    log.info("Scaler saved → %s", path)


def load_scaler(filename: str = "feature_scaler.pkl"):
    path = config.OUT_DIR / filename
    scaler = joblib.load(path)
    log.info("Scaler loaded ← %s", path)
    return scaler


def save_results(results_df: pd.DataFrame, filename: str = "model_comparison.csv") -> None:
    path = config.OUT_DIR / filename
    config.OUT_DIR.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(path, index=False)
    log.info("Results saved → %s", path)


def save_all(model, scaler, results_df: pd.DataFrame) -> None:
    """Convenience wrapper: save model, scaler, and CSV in one call."""
    log.info("── Saving Artefacts ──────────────────────────")
    save_model(model)
    save_scaler(scaler)
    save_results(results_df)
