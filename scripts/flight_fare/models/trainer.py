# # models/trainer.py

# import logging
# import numpy as np
# import pandas as pd
# # from sklearn.metrics import mean_squared_error, r2_score
# from sklearn.model_selection import cross_val_score
# from evaluation.metrics import compute_metrics

# from models.registry import MODEL_REGISTRY

# logger = logging.getLogger(__name__)


# def train_all(data) -> tuple[pd.DataFrame, dict]:
#     logger.info("── Training START ──")

#     results = []
#     trained_models = {}

#     for entry in MODEL_REGISTRY:
#         logger.info("Training: %s", entry.name)

#         # ── Pick scaled or raw features based on registry flag ────────────
#         if entry.uses_scaled:
#             X_tr = data.X_train_sc
#             X_te = data.X_test_sc
#         else:
#             X_tr = data.X_train
#             X_te = data.X_test


#         # ── Train ─────────────────────────────────────────────────────────
#         entry.estimator.fit(X_tr, data.y_train)

       

#         cv_scores = cross_val_score(
#             entry.estimator,
#             X_tr,
#             data.y_train,
#             cv=5,
#             scoring="r2",
#             n_jobs=-1
#         )

#         cv_std = cv_scores.std()

#         metrics = compute_metrics(
#             name=entry.name,
#             model=entry.estimator,
#             X_test=X_te,
#             y_test=data.y_test,
#             cv_scores=cv_scores,
#         )

#         metrics["CV Std"] = round(cv_std, 4)

#         logger.info(
#             "%s → RMSE: %.2f | MAE: %.2f | R²: %.4f | CV R²: %.4f ± %.4f",
#             entry.name,
#             metrics["RMSE"],
#             metrics["MAE"],
#             metrics["R²"],
#             metrics["CV R²"],
#             cv_std,
#         )

#         results.append(metrics)

#         trained_models[entry.name] = entry.estimator

#     results_df = pd.DataFrame(results).sort_values("R²", ascending=False)

#     logger.info("── Training COMPLETE ──")
#     logger.info("\n%s", results_df.to_string(index=False))

#     return results_df, trained_models

# models/trainer.py

import logging
import numpy as np
import pandas as pd
from sklearn.model_selection import cross_val_score
from evaluation.metrics import compute_metrics

from models.registry import MODEL_REGISTRY

logger = logging.getLogger(__name__)


def train_all(data) -> tuple[pd.DataFrame, dict]:
    logger.info("── Training START ──")

    results = []
    trained_models = {}

    for entry in MODEL_REGISTRY:
        logger.info("Training: %s", entry.name)

        # ── Pick scaled or raw features based on registry flag ────────────
        if entry.uses_scaled:
            X_tr = data.X_train_sc
            X_te = data.X_test_sc
        else:
            X_tr = data.X_train
            X_te = data.X_test

        # ── Train ─────────────────────────────────────────────────────────
        entry.estimator.fit(X_tr, data.y_train)

        # ── Cross-validation (in log-space, consistent with training) ─────
        cv_scores = cross_val_score(
            entry.estimator,
            X_tr,
            data.y_train,
            cv=5,
            scoring="r2",
            n_jobs=-1,
        )
        cv_std = cv_scores.std()

        # ── Metrics (R² in log-space, MAE/RMSE in original BDT scale) ─────
        metrics = compute_metrics(
            name=entry.name,
            model=entry.estimator,
            X_test=X_te,
            y_test=data.y_test,   # log-scale → R² is meaningful
            cv_scores=cv_scores,
        )

        # Override MAE/RMSE: invert log transform so values are in BDT
        log_preds    = entry.estimator.predict(X_te)
        y_true_orig  = np.expm1(data.y_test)
        y_pred_orig  = np.expm1(log_preds)
        metrics["MAE"]    = round(float(np.mean(np.abs(y_true_orig - y_pred_orig))), 2)
        metrics["RMSE"]   = round(float(np.sqrt(np.mean((y_true_orig - y_pred_orig) ** 2))), 2)
        metrics["CV Std"] = round(cv_std, 4)

        logger.info(
            "%s → RMSE: %.2f | MAE: %.2f | R²: %.4f | CV R²: %.4f ± %.4f",
            entry.name,
            metrics["RMSE"],
            metrics["MAE"],
            metrics["R²"],
            metrics["CV R²"],
            cv_std,
        )

        results.append(metrics)
        trained_models[entry.name] = entry.estimator

    results_df = pd.DataFrame(results).sort_values("R²", ascending=False)

    logger.info("── Training COMPLETE ──")
    logger.info("\n%s", results_df.to_string(index=False))

    return results_df, trained_models

