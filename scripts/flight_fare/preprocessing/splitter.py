# preprocessing/splitter.py

import logging
from dataclasses import dataclass
from typing import Any
import config


import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder

logger = logging.getLogger(__name__)


@dataclass
class SplitData:
    X_train:      Any
    X_test:       Any
    y_train:      Any
    y_test:       Any
    X_train_sc:   Any        # scaled version for distance-based models
    X_test_sc:    Any
    scaler:       Any
    features:     list
    feature_names: list      # alias — main.py uses both


def prepare(df, target="total_fare_bdt") -> SplitData:
    logger.info("── Preprocessing START ──")

    df = df.copy()

    # ── Feature selection ─────────────────────────────────────────────────────
    # base_fare_bdt and tax_surcharge_bdt deliberately excluded — leakage
    # feature_cols = [
    #     # Categorical
    #     "airline", "source", "destination", "class",
    #     "booking_source", "seasonality",
    #     # Engineered
    #     "is_international",
    #     # Numeric
    #     "duration_hrs", "stopovers", "days_before_departure",
    #     "departure_hour", "departure_day", "departure_month",
    #     "departure_weekday", "arrival_hour",
    # ]

    # # Only keep columns that actually exist
    # feature_cols = [c for c in feature_cols if c in df.columns]
    

    feature_cols = config.CAT_COLS + config.NUM_COLS
    feature_cols = [c for c in feature_cols if c in df.columns]
    missing = [c for c in feature_cols if c not in df.columns]
    if missing:
        logger.warning("Missing expected features: %s", missing)

    # ── Encode categoricals ───────────────────────────────────────────────────
    cat_cols = [c for c in feature_cols if df[c].dtype == "object"]
    for col in cat_cols:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        logger.info("Label encoded: %s (%d categories)", col, len(le.classes_))

    # ── Split ─────────────────────────────────────────────────────────────────
    X = df[feature_cols]
    y = df[target]

    # ── Log-transform target ──────────────────────────────────────────────────
    skew = y.skew()
    logger.info("Target skew before log transform: %.4f", skew)
    y = np.log1p(y)   # ← add this
    logger.info("Target log-transformed (use np.expm1 to invert predictions)")

    # X_train, X_test, y_train, y_test = train_test_split(
    #     X, y, test_size=0.2, random_state=42
    # )

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # ── Scale ─────────────────────────────────────────────────────────────────
    # Fit scaler on train only — never fit on test (data leakage)
    scaler = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc  = scaler.transform(X_test)

    logger.info("Train shape: %s | Test shape: %s", X_train.shape, X_test.shape)
    logger.info("Features used: %s", feature_cols)

    return SplitData(
        X_train=X_train,
        X_test=X_test,
        y_train=y_train,
        y_test=y_test,
        X_train_sc=X_train_sc,
        X_test_sc=X_test_sc,
        scaler=scaler,
        features=feature_cols,
        feature_names=feature_cols,
    )