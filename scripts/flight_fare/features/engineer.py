# # features/engineer.py

# import pandas as pd
# import logging

# logger = logging.getLogger(__name__)


# def engineer(df: pd.DataFrame) -> pd.DataFrame:
#     logger.info("── Feature Engineering START ──")

#     df = df.copy()

#     # -------------------------------------------------------
#     # 1. Standardize datetime column names
#     # -------------------------------------------------------
#     rename_map = {
#         "departure_date_and_time": "departure_datetime",
#         "arrival_date_and_time": "arrival_datetime",
#     }

#     df = df.rename(columns=rename_map)

#     # Ensure required columns exist
#     required_cols = ["departure_datetime", "arrival_datetime"]
#     for col in required_cols:
#         if col not in df.columns:
#             raise KeyError(f"Missing {col}. Available: {df.columns}")

#     # Convert to datetime safely
#     df["departure_datetime"] = pd.to_datetime(df["departure_datetime"], errors="coerce")
#     df["arrival_datetime"] = pd.to_datetime(df["arrival_datetime"], errors="coerce")

#     # -------------------------------------------------------
#     # 2. Time-based features
#     # -------------------------------------------------------
#     df["departure_hour"] = df["departure_datetime"].dt.hour
#     df["departure_day"] = df["departure_datetime"].dt.day
#     df["departure_month"] = df["departure_datetime"].dt.month
#     df["departure_weekday"] = df["departure_datetime"].dt.weekday

#     df["arrival_hour"] = df["arrival_datetime"].dt.hour

#     # -------------------------------------------------------
#     # 3. Duration validation / correction
#     # -------------------------------------------------------
#     if "duration_hrs" in df.columns:
#         df["duration_hrs"] = pd.to_numeric(df["duration_hrs"], errors="coerce")
#     else:
#         df["duration_hrs"] = (
#             df["arrival_datetime"] - df["departure_datetime"]
#         ).dt.total_seconds() / 3600

#     # -------------------------------------------------------
#     # 4. Fare-based features (safe)
#     # -------------------------------------------------------
#     if "base_fare_bdt" in df.columns and "tax_surcharge_bdt" in df.columns:
#         df["tax_surcharge_bdt"] = pd.to_numeric(df["tax_surcharge_bdt"], errors="coerce")
#         df["base_fare_bdt"] = pd.to_numeric(df["base_fare_bdt"], errors="coerce")

#         df["fare_total_check"] = df["base_fare_bdt"] + df["tax_surcharge_bdt"]

#     # -------------------------------------------------------
#     # 5. Stopovers encoding (safe)
#     # -------------------------------------------------------
#     if "stopovers" in df.columns:
#         df["stopovers"] = pd.to_numeric(df["stopovers"], errors="coerce").fillna(0)

#     logger.info("Feature Engineering complete")

#     return df

# features/engineer.py

import pandas as pd
import logging

logger = logging.getLogger(__name__)


def engineer(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("── Feature Engineering START ──")

    df = df.copy()

    # ── 1. Validate datetimes are parsed (cleaner should have done this) ──────
    for col in ["departure_datetime", "arrival_datetime"]:
        if col not in df.columns:
            raise KeyError(f"Missing {col} — check cleaner output. Available: {list(df.columns)}")
        if not pd.api.types.is_datetime64_any_dtype(df[col]):
            logger.warning("%s is not datetime64 — parsing now", col)
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # ── 2. Time-based features ────────────────────────────────────────────────
    df["departure_hour"]    = df["departure_datetime"].dt.hour
    df["departure_day"]     = df["departure_datetime"].dt.day
    df["departure_month"]   = df["departure_datetime"].dt.month
    df["departure_weekday"] = df["departure_datetime"].dt.weekday
    df["arrival_hour"]      = df["arrival_datetime"].dt.hour

    # ── 3. Duration validation ────────────────────────────────────────────────
    if "duration_hrs" not in df.columns:
        # Fallback: compute from datetimes if column missing
        df["duration_hrs"] = (
            df["arrival_datetime"] - df["departure_datetime"]
        ).dt.total_seconds() / 3600
        logger.info("duration_hrs computed from datetimes")
    else:
        df["duration_hrs"] = pd.to_numeric(df["duration_hrs"], errors="coerce")

    # ── 4. International flag (two-peak insight from EDA) ────────────────────
    # Bangladesh domestic flights are typically < 1.5hrs
    # Threshold at 3.5hrs cleanly separates the two fare clusters
    df["is_international"] = (df["duration_hrs"] > 3.5).astype(int)
    logger.info(
        "is_international: %d domestic | %d international",
        (df["is_international"] == 0).sum(),
        (df["is_international"] == 1).sum(),
    )

    # ── 5. Additional features ────────────────────

    df["route"] = df["source"] + "_" + df["destination"]
    df["is_weekend"] = df["departure_weekday"].isin([5, 6]).astype(int)
    df["last_minute_booking"] = (df["days_before_departure"] <= 7).astype(int)
    df["early_booking"] = (df["days_before_departure"] >= 30).astype(int)
    df["stopover_intensity"] = df["stopovers"] / (df["duration_hrs"] + 1e-6)
    df["trip_complexity"] = (
    df["stopovers"] +
    df["is_international"] +
    (df["duration_hrs"] > 8).astype(int)
        )

    logger.info("── Feature Engineering complete — shape: %s ──", df.shape)
    return df