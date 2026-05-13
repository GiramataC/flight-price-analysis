# from airflow import DAG
# from airflow.operators.python import PythonOperator
# from datetime import datetime

# from scripts.ingestion import ingest_csv_to_postgres
# from scripts.validation import validate_data

# POSTGRES_URI = "postgresql://airflow:airflow@postgres-analytics:5432/flight_analytics"

# def run_dbt():
#     import os
#     os.system("dbt run")

# with DAG(
#     "flight_pipeline",
#     start_date=datetime(2024, 1, 1),
#     schedule_interval="@daily",
#     catchup=False
# ) as dag:

#     ingest = PythonOperator(
#         task_id="ingest",
#         python_callable=ingest_csv_to_postgres,
#         op_kwargs={
#             "csv_path": "/opt/airflow/data/file.csv",
#             "postgres_uri": POSTGRES_URI,
#             "table_name": "raw_flights"
#         }
#     )

#     validate = PythonOperator(
#         task_id="validate",
#         python_callable=validate_data,
#         op_kwargs={
#             "postgres_uri": POSTGRES_URI,
#             "raw_table": "raw_flights",
#             "clean_table": "cleaned_flights",
#             "run_id": "{{ ti.xcom_pull(task_ids='ingest')['run_id'] }}"
#         }
#     )

#     dbt_run = PythonOperator(
#         task_id="dbt_run",
#         python_callable=run_dbt
#     )

#     ingest >> validate >> dbt_run

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.mysql.hooks.mysql import MySqlHook
from datetime import datetime
import subprocess

from scripts.ingestion import ingest_csv_to_mysql
from scripts.validation import validate_data
from scripts.load_to_postgres import load_to_postgres

def get_mysql_uri():
    return MySqlHook(mysql_conn_id="mysql_staging").get_uri()

def get_postgres_uri():
    return PostgresHook(postgres_conn_id="postgres_analytics").get_uri()

def run_ingest(**context):
    return ingest_csv_to_mysql(
        csv_path="/opt/airflow/data/Flight_Price_Dataset_of_Bangladesh.csv",
        mysql_uri=get_mysql_uri(),
        table_name="raw_flights"
    )

def run_validate(**context):
    mysql_uri = get_mysql_uri()
    run_id = context["ti"].xcom_pull(task_ids="ingest")["run_id"]
    return validate_data(
        mysql_uri=mysql_uri,
        raw_table="raw_flights",
        clean_table="validated_flights",
        run_id=run_id
    )

def run_load_to_postgres(**context):
    run_id = context["ti"].xcom_pull(task_ids="ingest")["run_id"]
    return load_to_postgres(
        mysql_uri=get_mysql_uri(),
        postgres_uri=get_postgres_uri(),
        source_table="validated_flights",
        target_table="raw_flights",
        run_id=run_id
    )

def run_dbt():
    subprocess.run(
        ["dbt", "run", "--project-dir", "/opt/airflow/dbt"],
        check=True
    )

with DAG(
    "flight_pipeline",
    start_date=datetime(2024, 1, 1),
    schedule="@daily",
    catchup=False
) as dag:

    ingest = PythonOperator(task_id="ingest", python_callable=run_ingest)
    validate = PythonOperator(task_id="validate", python_callable=run_validate)
    load_pg = PythonOperator(task_id="load_to_postgres", python_callable=run_load_to_postgres)
    dbt_run = PythonOperator(task_id="dbt_run", python_callable=run_dbt)

    ingest >> validate >> load_pg >> dbt_run