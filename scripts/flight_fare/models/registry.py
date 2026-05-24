"""
models/registry.py
──────────────────
Central registry of every model used in the pipeline.

Each entry specifies:
  • the estimator instance
  • whether it needs scaled input (uses_scaled=True for linear models)

Adding a new model = one new entry in MODEL_REGISTRY.
The training loop in models/trainer.py reads this registry — no
other file needs to change.
"""

from dataclasses import dataclass
from typing import Any

from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
import xgboost as xgb
import lightgbm as lgb

import config


@dataclass
class ModelEntry:
    name:        str
    estimator:   Any
    uses_scaled: bool = False    # if True, trainer passes X_train_sc / X_test_sc


MODEL_REGISTRY: list[ModelEntry] = [
    ModelEntry(
        name="Linear Regression",
        estimator=LinearRegression(),
        uses_scaled=True,
    ),
    ModelEntry(
        name="Ridge Regression",
        estimator=Ridge(alpha=1.0, random_state=config.SEED),
        uses_scaled=True,
    ),
    ModelEntry(
        name="Lasso Regression",
        estimator=Lasso(alpha=0.001, max_iter=5_000, random_state=config.SEED),
        uses_scaled=True,
    ),
    ModelEntry(
        name="Decision Tree",
        estimator=DecisionTreeRegressor(
            max_depth=10, min_samples_leaf=20, random_state=config.SEED
        ),
        uses_scaled=False,
    ),
    ModelEntry(
        name="Random Forest",
        estimator=RandomForestRegressor(
            n_estimators=300, min_samples_leaf=5,
            n_jobs=-1, random_state=config.SEED
        ),
        uses_scaled=False,
    ),
    ModelEntry(
        name="Gradient Boosting",
        estimator=GradientBoostingRegressor(
            n_estimators=300, learning_rate=0.05,
            max_depth=5, subsample=0.8, random_state=config.SEED
        ),
        uses_scaled=False,
    ),
    ModelEntry(
        name="XGBoost",
        estimator=xgb.XGBRegressor(
            n_estimators=400, learning_rate=0.05, max_depth=6,
            subsample=0.8, colsample_bytree=0.8,
            reg_alpha=0.1, reg_lambda=1.0,
            n_jobs=-1, random_state=config.SEED, verbosity=0,
        ),
        uses_scaled=False,
    ),
    ModelEntry(
        name="LightGBM",
        estimator=lgb.LGBMRegressor(
            n_estimators=400, learning_rate=0.05, num_leaves=63,
            subsample=0.8, colsample_bytree=0.8,
            reg_alpha=0.1, reg_lambda=1.0,
            n_jobs=-1, random_state=config.SEED, verbose=-1,
        ),
        uses_scaled=False,
    ),
]
