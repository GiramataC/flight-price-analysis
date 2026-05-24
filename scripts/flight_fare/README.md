# Flight Fare Prediction — Bangladesh

A supervised regression pipeline that predicts flight ticket prices using the
[Flight Price Dataset of Bangladesh](https://www.kaggle.com/) (57,000 records,
17 features). The best model — Gradient Boosting — explains **89% of fare
variation** (R² = 0.8927, RMSE ≈ ৳48,241).

---

## Table of Contents

- [Project Structure](#project-structure)
- [Quickstart](#quickstart)
- [Pipeline Overview](#pipeline-overview)
- [Key Findings](#key-findings)
- [Model Results](#model-results)
- [Notebooks](#notebooks)
- [Configuration](#configuration)
- [Requirements](#requirements)

---

## Project Structure

```
flight_fare/
│
├── main.py                         # Pipeline orchestrator — run this
├── config.py                       # All paths, constants, hyperparameters
│
├── data/
│   ├── loader.py                   # Loads CSV, normalises column names
│   ├── cleaner.py                  # Deduplication, null handling, type casting
│   └── Flight_Price_Dataset_of_Bangladesh.csv
│
├── features/
│   └── engineer.py                 # Time features, is_international flag, route complexity
│
├── eda/
│   ├── analysis.py                 # KPIs, distributions, correlations (logged)
│   └── structure_inspection.ipynb  # Visual raw data inspection before cleaning
│
├── preprocessing/
│   └── splitter.py                 # Label encoding, log-transform target, train/test split, scaling
│
├── models/
│   ├── registry.py                 # Central catalogue of all 8 models
│   ├── trainer.py                  # Training loop — reads registry, runs CV
│   └── tuner.py                    # RandomizedSearchCV for XGBoost
│
├── evaluation/
│   └── metrics.py                  # R², MAE, RMSE computation
│
├── visualisation/
│   ├── results.py                  # Feature importance, prediction summary
│   └── model_analysis.ipynb        # Bias-variance, regularization, insights
│
├── artefacts/
│   └── persistence.py              # Saves model, scaler, results to outputs/
│
├── utils/
│   └── logger.py                   # Unified logger (terminal + file, Jupyter-safe)
│
└── outputs/
    ├── best_model_xgboost.pkl      # Saved best model
    ├── feature_scaler.pkl          # Fitted StandardScaler
    ├── model_comparison.csv        # R², MAE, RMSE for all models
    └── pipeline.log                # Full run log
```

---

## Quickstart

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the full pipeline
python main.py

# 3. Inspect results
cat outputs/model_comparison.csv
```

To stop the pipeline after a specific stage, set `RUN_UNTIL` in `main.py`:

```python
RUN_UNTIL = "eda"          # stops after EDA
RUN_UNTIL = "preprocessing" # stops after splitting
RUN_UNTIL = "full"          # runs everything (default)
```

---

## Pipeline Overview

```
load() → inspect_structure() → clean() → engineer() → run_full_eda()
      → prepare() → train_all() → tune_xgboost() → plot_all_results() → save_all()
```

| Stage | File | What it does |
|---|---|---|
| 1. Load | `data/loader.py` | Reads CSV, snake_cases column names |
| 1.5. Inspect | `eda/analysis.py` | Raw structure check before cleaning |
| 2. Clean | `data/cleaner.py` | Deduplication, datetime parsing, stopovers encoding, null imputation |
| 3. Engineer | `features/engineer.py` | Time features, `is_international` flag, trip complexity |
| 4. EDA | `eda/analysis.py` | KPIs, fare distribution, season analysis, correlations |
| 5. Preprocess | `preprocessing/splitter.py` | Label encode categoricals, log-transform target, 80/20 split, scale |
| 6. Train | `models/trainer.py` | Trains all 8 models from registry with 5-fold CV |
| 7. Tune | `models/tuner.py` | RandomizedSearchCV on XGBoost (20 iterations) |
| 8. Visualise | `visualisation/results.py` | Feature importance, prediction summary |
| 9. Save | `artefacts/persistence.py` | Persists model, scaler, comparison table |

---

## Key Findings

**Fare is driven by three factors that account for 97.6% of model decisions:**

| Factor | Importance | Insight |
|---|---|---|
| Flight duration | 55.8% | Longer routes cost significantly more |
| Destination | 23.8% | International hubs (JED, YYZ, LHR) carry premium pricing |
| Travel class | 18.1% | Business/First class 2–3× Economy fares |

**Seasonal premiums over Regular baseline:**

| Season | Avg Fare | Premium |
|---|---|---|
| Hajj | ৳97,144 | +43% |
| Eid | ৳91,560 | +34% |
| Winter Holidays | ৳79,677 | +17% |
| Regular | ৳68,077 | baseline |

**Airline brand has minimal pricing impact** — only ৳7,000 spread across 24
airlines. Route and class dominate.

**Linear models score R²=0.35** vs tree models at **R²=0.89** — confirming fare
pricing is non-linear. Rule-based pricing systems will underperform.

---

## Model Results

| Model | R² | MAE (৳) | RMSE (৳) | CV R² |
|---|---|---|---|---|
| **Gradient Boosting** | **0.8927** | **28,584** | **48,241** | 0.8921 |
| XGBoost (Tuned) | 0.8916 | 28,726 | 48,673 | 0.8916 |
| XGBoost | 0.8910 | 28,706 | 48,519 | 0.8905 |
| LightGBM | 0.8900 | 28,741 | 48,619 | 0.8898 |
| Random Forest | 0.8897 | 28,841 | 49,079 | 0.8891 |
| Decision Tree | 0.8879 | 28,921 | 49,415 | 0.8857 |
| Linear Regression | 0.3528 | 49,436 | 79,588 | 0.3530 |
| Ridge Regression | 0.3528 | 49,436 | 79,588 | 0.3530 |
| Lasso Regression | 0.3528 | 49,427 | 79,587 | 0.3530 |

**Gradient Boosting** is selected as the production model — highest R² with low
CV standard deviation (0.002), indicating stable generalisation.

---

## Notebooks

| Notebook | Location | Purpose |
|---|---|---|
| `structure_inspection.ipynb` | `eda/` | Raw data inspection — `.info()`, `.describe()`, outlier plots, missing values |
| `model_analysis.ipynb` | `visualisation/` | Bias-variance curves, regularization coefficients, feature importance, stakeholder summary |

Both notebooks are self-contained — they import from the project modules and
can be run independently after `main.py` has completed at least one full run.

---

## Configuration

All tuneable settings live in `config.py`:

```python
SEED          = 42
TEST_SIZE     = 0.20
CV_FOLDS      = 5
TUNING_N_ITER = 20       # RandomizedSearchCV iterations for XGBoost

XGB_PARAM_DIST = { ... } # XGBoost hyperparameter search space

CAT_COLS = [...]          # Categorical features fed to the model
NUM_COLS = [...]          # Numerical features fed to the model
TARGET   = "total_fare_bdt"
```

Adding a new model requires only one entry in `models/registry.py` — no other
file needs to change.

---

## Requirements

```
pandas
numpy
scikit-learn
xgboost
lightgbm
matplotlib
seaborn
jupyter
```

Install with:

```bash
pip install pandas numpy scikit-learn xgboost lightgbm matplotlib seaborn jupyter
```

---

## Limitations

- 11% of fare variation is unexplained — likely driven by real-time demand,
  seat inventory, and promotional pricing not present in this dataset.
- Label encoding of categoricals assumes no ordinal relationship — a future
  improvement would use target encoding for high-cardinality columns like
  `destination` (20 unique values).
- Model trained on 2025 fare data — seasonal patterns and route pricing may
  shift with airline policy changes.
