"""
dags/flight_fare_retrain_dag.py
────────────────────────────────
Airflow DAG — scheduled retraining of the Flight Fare Prediction model.

Pipeline stages as individual tasks:
    load → inspect → clean → engineer → eda → preprocess → train → tune → save

Schedule: weekly (every Sunday at 02:00)

Setup:
    1. Copy your flight_fare/ project into the scripts/ folder of your
       Airflow project (the folder mounted at /opt/airflow/scripts/)
    2. Drop this file into your dags/ folder
    3. Add required packages to _PIP_ADDITIONAL_REQUIREMENTS in docker-compose.yml:
         scikit-learn xgboost lightgbm

docker-compose.yml change:
    _PIP_ADDITIONAL_REQUIREMENTS: '... scikit-learn xgboost lightgbm'
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.dates import days_ago

log = logging.getLogger(__name__)

# ── DAG default args ──────────────────────────────────────────────────────────
DEFAULT_ARGS = {
    "owner":            "flight_fare_pipeline",
    "depends_on_past":  False,
    "email_on_failure": False,
    "email_on_retry":   False,
    "retries":          1,
    "retry_delay":      timedelta(minutes=5),
}

# ── Path to flight_fare project inside container ──────────────────────────────
# Copy your flight_fare/ folder into scripts/ → Docker mounts it at /opt/airflow/scripts/
PROJECT_PATH = "/opt/airflow/scripts/flight_fare"


# ── Task functions ────────────────────────────────────────────────────────────

def task_load(**context):
    import sys
    sys.path.insert(0, PROJECT_PATH)
    from data.loader import load

    df_raw = load()
    log.info("Loaded: %d rows × %d cols", *df_raw.shape)

    # Push to XCom so downstream tasks can access shape info
    context["ti"].xcom_push(key="raw_shape", value=df_raw.shape)
    return "load_ok"


def task_inspect(**context):
    import sys
    sys.path.insert(0, PROJECT_PATH)
    from data.loader import load
    from eda.analysis import run_full_eda

    df_raw = load()
    run_full_eda(df_raw)
    log.info("Structure inspection complete")
    return "inspect_ok"


def task_clean(**context):
    import sys
    sys.path.insert(0, PROJECT_PATH)
    from data.loader import load
    from data.cleaner import clean

    df_raw   = load()
    df_clean = clean(df_raw)
    log.info("Cleaned: %d rows", len(df_clean))
    context["ti"].xcom_push(key="clean_shape", value=df_clean.shape)
    return "clean_ok"


def task_engineer(**context):
    import sys
    sys.path.insert(0, PROJECT_PATH)
    from data.loader import load
    from data.cleaner import clean
    from features.engineer import engineer

    df_raw   = load()
    df_clean = clean(df_raw)
    df       = engineer(df_clean)
    log.info("Engineered: %d rows × %d cols", *df.shape)
    context["ti"].xcom_push(key="engineered_shape", value=df.shape)
    return "engineer_ok"


def task_eda(**context):
    import sys
    sys.path.insert(0, PROJECT_PATH)
    from data.loader import load
    from data.cleaner import clean
    from features.engineer import engineer
    from eda.analysis import run_full_eda

    df_raw   = load()
    df_clean = clean(df_raw)
    df       = engineer(df_clean)
    run_full_eda(df)
    log.info("EDA complete")
    return "eda_ok"


def task_preprocess(**context):
    import sys
    sys.path.insert(0, PROJECT_PATH)
    from data.loader import load
    from data.cleaner import clean
    from features.engineer import engineer
    from preprocessing.splitter import prepare

    df_raw   = load()
    df_clean = clean(df_raw)
    df       = engineer(df_clean)
    data     = prepare(df)
    log.info("Train: %s | Test: %s", data.X_train.shape, data.X_test.shape)
    context["ti"].xcom_push(key="train_shape", value=data.X_train.shape)
    return "preprocess_ok"


def task_train(**context):
    import sys
    import pandas as pd
    sys.path.insert(0, PROJECT_PATH)
    from data.loader import load
    from data.cleaner import clean
    from features.engineer import engineer
    from preprocessing.splitter import prepare
    from models.trainer import train_all

    df_raw   = load()
    df_clean = clean(df_raw)
    df       = engineer(df_clean)
    data     = prepare(df)

    results_df, trained_models = train_all(data)

    best_model_name = results_df.iloc[0]["Model"]
    best_r2         = results_df.iloc[0]["R²"]

    log.info("Best model: %s | R²=%.4f", best_model_name, best_r2)
    context["ti"].xcom_push(key="best_model_name", value=best_model_name)
    context["ti"].xcom_push(key="best_r2",         value=float(best_r2))
    return "train_ok"


def task_tune(**context):
    import sys
    sys.path.insert(0, PROJECT_PATH)
    from data.loader import load
    from data.cleaner import clean
    from features.engineer import engineer
    from preprocessing.splitter import prepare
    from models.tuner import tune_xgboost

    df_raw   = load()
    df_clean = clean(df_raw)
    df       = engineer(df_clean)
    data     = prepare(df)

    best_model, metrics = tune_xgboost(data)
    log.info("Tuned XGBoost → R²=%.4f | RMSE=%.2f", metrics["R²"], metrics["RMSE"])
    context["ti"].xcom_push(key="tuned_r2",   value=float(metrics["R²"]))
    context["ti"].xcom_push(key="tuned_rmse", value=float(metrics["RMSE"]))
    return "tune_ok"


def task_save(**context):
    import sys
    sys.path.insert(0, PROJECT_PATH)
    from data.loader import load
    from data.cleaner import clean
    from features.engineer import engineer
    from preprocessing.splitter import prepare
    from models.trainer import train_all
    from models.tuner import tune_xgboost
    from artefacts.persistence import save_all
    import pandas as pd

    df_raw   = load()
    df_clean = clean(df_raw)
    df       = engineer(df_clean)
    data     = prepare(df)

    results_df, trained_models = train_all(data)
    best_model, tuned_metrics  = tune_xgboost(data)

    full_results = pd.concat(
        [results_df, pd.DataFrame([tuned_metrics])],
        ignore_index=True
    )

    save_all(best_model, data.scaler, full_results)

    # Log final summary
    ti          = context["ti"]
    tuned_r2    = ti.xcom_pull(task_ids="tune_model", key="tuned_r2")
    tuned_rmse  = ti.xcom_pull(task_ids="tune_model", key="tuned_rmse")

    log.info("═" * 50)
    log.info("  Retraining complete")
    log.info("  Best model R²  : %.4f", tuned_r2 or 0)
    log.info("  Best model RMSE: %.2f", tuned_rmse or 0)
    log.info("  Artefacts saved to outputs/")
    log.info("═" * 50)
    return "save_ok"


# ── DAG definition ────────────────────────────────────────────────────────────
with DAG(
    dag_id="flight_fare_retrain",
    description="Weekly retraining of the Flight Fare Prediction model",
    default_args=DEFAULT_ARGS,
    schedule_interval="0 2 * * 0",   # Every Sunday at 02:00
    start_date=days_ago(1),
    catchup=False,
    max_active_runs=1,
    tags=["flight_fare", "ml", "retraining"],
) as dag:

    start = EmptyOperator(task_id="start")
    end   = EmptyOperator(task_id="end")

    load_data = PythonOperator(
        task_id="load_data",
        python_callable=task_load,
    )

    inspect = PythonOperator(
        task_id="inspect_structure",
        python_callable=task_inspect,
    )

    clean_data = PythonOperator(
        task_id="clean_data",
        python_callable=task_clean,
    )

    engineer_features = PythonOperator(
        task_id="engineer_features",
        python_callable=task_engineer,
    )

    run_eda = PythonOperator(
        task_id="run_eda",
        python_callable=task_eda,
    )

    preprocess = PythonOperator(
        task_id="preprocess",
        python_callable=task_preprocess,
    )

    train = PythonOperator(
        task_id="train_models",
        python_callable=task_train,
    )

    tune = PythonOperator(
        task_id="tune_model",
        python_callable=task_tune,
    )

    save = PythonOperator(
        task_id="save_artefacts",
        python_callable=task_save,
    )

    # ── Task dependencies (linear pipeline) ───────────────────────────────────
    start >> load_data >> inspect >> clean_data >> engineer_features
    engineer_features >> run_eda >> preprocess >> train >> tune >> save >> end
