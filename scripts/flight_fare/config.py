# # from pathlib import Path

# # ROOT_DIR = Path(__file__).resolve().parent.parent

# # DATASET_PATH = ROOT_DIR / "flight_fare"/"data" / "Flight_Price_Dataset_of_Bangladesh.csv"

# # OUT_DIR = ROOT_DIR / "outputs"
# # PLOT_DIR = OUT_DIR / "plots"

# # SEED = 42

# # TEST_SIZE = 0.2
# # CV_FOLDS = 5

# # # After standardization (VERY IMPORTANT)
# # CAT_COLS = [
# #     "airline",
# #     "source",
# #     "destination",
# #     "class",
# #     "booking_source",
# #     "seasonality",
# #     "stopovers",
# # ]

# # NUM_COLS = [
# #     "base_fare_bdt",
# #     "tax_surcharge_bdt",
# #     "duration_hrs",
# #     "days_before_departure",
# # ]

# # TARGET = "total_fare_bdt"

# # TUNING_N_ITER = 5

# # # =========================================================
# # # XGBoost Hyperparameter Search Space
# # # =========================================================

# # XGB_PARAM_DIST = {
# #     "n_estimators": [100, 200],
# #     "max_depth": [4, 6, 8],
# #     "learning_rate": [0.01, 0.05, 0.1],
# #     "subsample": [0.8, 1.0],
# #     "colsample_bytree": [0.8, 1.0]
# # }


# from pathlib import Path

# # ── Paths ──────────────────────────────────────────────────────────────────
# ROOT_DIR     = Path(__file__).resolve().parent          # project root
# DATASET_PATH = ROOT_DIR / "data" / "Flight_Price_Dataset_of_Bangladesh.csv"
# OUT_DIR      = ROOT_DIR / "outputs"
# PLOT_DIR     = OUT_DIR / "plots"

# # ── Reproducibility ────────────────────────────────────────────────────────
# SEED = 42

# # ── Raw CSV column names (snake_case after cleaning) ──────────────────────
# COL_AIRLINE     = "airline"
# COL_SOURCE      = "source"
# COL_DEST        = "destination"
# COL_DEP_DT      = "departure_datetime"
# COL_ARR_DT      = "arrival_datetime"
# COL_DURATION    = "duration_hrs"
# COL_STOPOVERS   = "stopovers"
# COL_AIRCRAFT    = "aircraft_type"
# COL_CLASS       = "class"
# COL_BOOKING_SRC = "booking_source"
# COL_BASE_FARE   = "base_fare_bdt"
# COL_TAX         = "tax_surcharge_bdt"
# COL_TOTAL_FARE  = "total_fare_bdt"
# COL_SEASONALITY = "seasonality"
# COL_DAYS_BEFORE = "days_before_departure"

# TARGET = COL_TOTAL_FARE

# # ── Cleaning ───────────────────────────────────────────────────────────────
# IQR_FENCE_MULTIPLIER = 3.0

# # ── Feature groups ─────────────────────────────────────────────────────────
# # Categorical: string columns that will be one-hot encoded
# CAT_COLS = [
#     "airline",
#     "source",
#     "destination",
#     "aircraft_type",
#     "class",
#     "booking_source",
#     "seasonality",
# ]

# # Numerical: raw + engineered numeric columns fed to the model
# NUM_COLS = [
#     "base_fare_bdt",
#     "tax_surcharge_bdt",
#     "duration_hrs",
#     "days_before_departure",
#     "stopovers",           # ordinal int (0/1/2) after encoding in engineer.py
#     "departure_hour",
#     "departure_weekday",
#     "arrival_hour",
#     "tax_ratio",
# ]

# # ── Preprocessing ──────────────────────────────────────────────────────────
# TEST_SIZE = 0.20
# CV_FOLDS  = 5

# # ── Hyperparameter search (XGBoost) ────────────────────────────────────────
# XGB_PARAM_DIST = {
#     "n_estimators":     [100, 200, 300],
#     "max_depth":        [4, 6, 8],
#     "learning_rate":    [0.01, 0.05, 0.1],
#     "subsample":        [0.8, 1.0],
#     "colsample_bytree": [0.8, 1.0],
#     "reg_alpha":        [0.0, 0.1, 0.5],
#     "reg_lambda":       [0.5, 1.0, 2.0],
# }
# TUNING_N_ITER = 5

# # ── Plot theme (used by eda/analysis.py and visualisation/results.py) ──────
# PLT_STYLE = {
#     "bg":      "#0F1117",
#     "panel":   "#1A1D27",
#     "accent1": "#4F9CF9",
#     "accent2": "#F97B4F",
#     "accent3": "#4FD18B",
#     "accent4": "#C84FD1",
#     "text":    "#E8EAF0",
#     "grid":    "#2A2D3A",
# }

from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT_DIR     = Path(__file__).resolve().parent
DATASET_PATH = ROOT_DIR / "data" / "Flight_Price_Dataset_of_Bangladesh.csv"
OUT_DIR      = ROOT_DIR / "outputs"
PLOT_DIR     = OUT_DIR / "plots"

# ── Reproducibility ────────────────────────────────────────────────────────
SEED = 42

# ── Column name constants ──────────────────────────────────────────────────
COL_AIRLINE     = "airline"
COL_SOURCE      = "source"
COL_DEST        = "destination"
COL_DEP_DT      = "departure_datetime"
COL_ARR_DT      = "arrival_datetime"
COL_DURATION    = "duration_hrs"
COL_STOPOVERS   = "stopovers"
COL_AIRCRAFT    = "aircraft_type"
COL_CLASS       = "class"
COL_BOOKING_SRC = "booking_source"
COL_BASE_FARE   = "base_fare_bdt"
COL_TAX         = "tax_surcharge_bdt"
COL_TOTAL_FARE  = "total_fare_bdt"
COL_SEASONALITY = "seasonality"
COL_DAYS_BEFORE = "days_before_departure"

TARGET = COL_TOTAL_FARE

# ── Cleaning ───────────────────────────────────────────────────────────────
IQR_FENCE_MULTIPLIER = 3.0

# ── Feature groups ─────────────────────────────────────────────────────────
CAT_COLS = [
    # "route",


    "airline",
    "source",
    "destination",
    # "aircraft_type",
    "class",
    "booking_source",
    "seasonality",
]

NUM_COLS = [
    # "base_fare_bdt",
    # "tax_surcharge_bdt",



    # "departure_weekday",
    # "days_before_departure",
    # "days_before_departure",
    # "stopovers",


    "duration_hrs",
    "days_before_departure",
    "stopovers",
    "departure_hour",
    "departure_day",
    "departure_month",
    "departure_weekday",
    "arrival_hour",
    "is_international",
]



# ── Preprocessing ──────────────────────────────────────────────────────────
TEST_SIZE = 0.20
CV_FOLDS  = 5

# ── Hyperparameter search (XGBoost) ────────────────────────────────────────
XGB_PARAM_DIST = {
    "n_estimators":     [100, 200, 300],
    "max_depth":        [4, 6, 8],
    "learning_rate":    [0.01, 0.05, 0.1],
    "subsample":        [0.8, 1.0],
    "colsample_bytree": [0.8, 1.0],
    "reg_alpha":        [0.0, 0.1, 0.5],
    "reg_lambda":       [0.5, 1.0, 2.0],
}
TUNING_N_ITER = 20

# ── Plot theme ─────────────────────────────────────────────────────────────
PLT_STYLE = {
    "bg":      "#0F1117",
    "panel":   "#1A1D27",
    "accent1": "#4F9CF9",
    "accent2": "#F97B4F",
    "accent3": "#4FD18B",
    "accent4": "#C84FD1",
    "text":    "#E8EAF0",
    "grid":    "#2A2D3A",
}