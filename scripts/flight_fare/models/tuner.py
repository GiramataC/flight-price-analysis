"""
models/tuner.py
────────────────
Hyperparameter tuning for XGBoost (robust version)

Fixes:
- No broken import of PreprocessedData
- Uses correct PreprocessedData structure from splitter
- Fully compatible with snake_case pipeline
- Safe CV + logging
"""

import numpy as np
import xgboost as xgb
from sklearn.model_selection import RandomizedSearchCV

import config
from utils.logger import get_logger
from evaluation.metrics import compute_metrics
from sklearn.model_selection import cross_val_score

log = get_logger(__name__)


def tune_xgboost(data):
    """
    Tune XGBoost using RandomizedSearchCV.

    Parameters
    ----------
    data : PreprocessedData
        Output from preprocessing.splitter.prepare()

    Returns
    -------
    best_model : fitted XGBRegressor
    metrics    : dict
    """

    log.info("── XGBoost Tuning START ──")

    base_model = xgb.XGBRegressor(
        n_jobs=-1,
        random_state=config.SEED,
        verbosity=0
    )

    search = RandomizedSearchCV(
        estimator=base_model,
        param_distributions=config.XGB_PARAM_DIST,
        n_iter=config.TUNING_N_ITER,
        scoring="r2",
        cv=config.CV_FOLDS,
        n_jobs=-1,
        random_state=config.SEED,
        verbose=0,
        refit=True,
    )

    # ---------------------------
    # IMPORTANT: use non-scaled data for tree models
    # ---------------------------
    search.fit(data.X_train, data.y_train)

    best_model = search.best_estimator_

    log.info("Best Params: %s", search.best_params_)
    log.info("Best CV R²: %.4f", search.best_score_)

    # ---------------------------
    # Evaluate final model
    # ---------------------------
    # metrics = compute_metrics(
    #     name="XGBoost (Tuned)",
    #     model=best_model,
    #     X_test=data.X_test,
    #     y_test=data.y_test,
    #     cv_scores=np.array([search.best_score_]),
    # )
    cv_scores = cross_val_score(
    best_model,
    data.X_train,
    data.y_train,
    cv=config.CV_FOLDS,
    scoring="r2",
    n_jobs=-1
    )

    # metrics = compute_metrics(
    #     name="XGBoost (Tuned)",
    #     model=best_model,
    #     X_test=data.X_test,
    #     y_test=data.y_test,
    #     cv_scores=cv_scores,
    # )

    # metrics["CV Std"] = round(cv_scores.std(), 4)
    metrics = compute_metrics(
        name="XGBoost (Tuned)",
        model=best_model,
        X_test=data.X_test,
        y_test=data.y_test,
        cv_scores=cv_scores,
    )

    metrics["CV Std"] = round(cv_scores.std(), 4)

    # ── Invert log transform → MAE/RMSE back to BDT scale ─────────────────
    log_preds       = best_model.predict(data.X_test)
    y_true_orig     = np.expm1(data.y_test)
    y_pred_orig     = np.expm1(log_preds)
    metrics["MAE"]  = round(float(np.mean(np.abs(y_true_orig - y_pred_orig))), 2)
    metrics["RMSE"] = round(float(np.sqrt(np.mean((y_true_orig - y_pred_orig) ** 2))), 2)

    log.info(
        "Tuned XGBoost → R²=%.4f | MAE=%.2f | RMSE=%.2f",
        metrics["R²"], metrics["MAE"], metrics["RMSE"]
    )

    log.info(
        "Tuned XGBoost → R²=%.4f | MAE=%.2f | RMSE=%.2f",
        metrics["R²"], metrics["MAE"], metrics["RMSE"]
    )

    return best_model, metrics