"""
evaluation/metrics.py
─────────────────────
Single shared function for computing and packaging model metrics.
Imported by both models.trainer and models.tuner — no duplication.
"""

from typing import Optional

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def compute_metrics(
    name: str,
    model,
    X_test,
    y_test,
    cv_scores: Optional[np.ndarray] = None,
) -> dict:
    """
    Compute R², MAE, RMSE, and mean CV R² for a fitted estimator.

    Parameters
    ----------
    name       : display name for the model
    model      : fitted sklearn-compatible estimator
    X_test     : test features (scaled or raw, matching how model was trained)
    y_test     : ground-truth target
    cv_scores  : array of per-fold R² from cross_val_score (optional)

    Returns
    -------
    dict with keys: Model, R², MAE, RMSE, CV R² (mean)
    """
    y_pred = model.predict(X_test)

    # return {
    #     "Model":         name,
    #     "R²":            round(float(r2_score(y_test, y_pred)), 4),
    #     "MAE":           round(float(mean_absolute_error(y_test, y_pred)), 2),
    #     "RMSE":          round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 2),
    #     "CV R² (mean)":  round(float(cv_scores.mean()), 4) if cv_scores is not None else float("nan"),
    # }
    return {
    "Model": name,
    "R²": round(float(r2_score(y_test, y_pred)), 4),
    "MAE": round(float(mean_absolute_error(y_test, y_pred)), 2),
    "RMSE": round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 2),
    "CV R²": round(float(cv_scores.mean()), 4)
        if cv_scores is not None else np.nan,
    }
