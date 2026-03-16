import os
import sys
from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

sys.path.insert(0, "/opt/airflow")


def run_ingest_bronze():
    from ingestion.fetch_raw import build_job_config, load_bronze, load_client

    os.chdir("/opt/airflow")
    client = load_client()
    job_config = build_job_config()
    row_count = load_bronze(client, job_config)
    print(f"Loaded {row_count} rows into BigQuery bronze table")


with DAG(
    dag_id="manga_pipeline",
    description="Ingest manga CSV to BigQuery, run dbt staging and marts",
    schedule=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["manga", "pipeline"],
) as dag:
    ingest_bronze = PythonOperator(
        task_id="ingest_bronze",
        python_callable=run_ingest_bronze,
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="cd /opt/airflow/dbt && dbt run --profiles-dir . --target docker",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command="cd /opt/airflow/dbt && dbt test --profiles-dir . --target docker",
    )

    ingest_bronze >> dbt_run >> dbt_test
