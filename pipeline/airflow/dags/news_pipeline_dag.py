"""
DAG Airflow - Pipeline News
Utilise BashOperator pour éviter les problèmes d'imports
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

default_args = {
    "owner": "news-platform",
    "depends_on_past": False,
    "start_date": days_ago(1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "execution_timeout": timedelta(minutes=30),
}

dag = DAG(
    dag_id="news_pipeline_hourly",
    description="Pipeline articles de presse - Bronze/Silver/Gold",
    schedule_interval="0 * * * *",
    default_args=default_args,
    catchup=False,
    max_active_runs=1,
    tags=["news", "medallion"],
)

PROJECT = "/opt/airflow/project"
PYTHON  = "python"

with dag:

    start = BashOperator(
        task_id="pipeline_start",
        bash_command=f'echo "=== Pipeline démarré $(date) ==="',
    )

    scrape_hespress = BashOperator(
        task_id="scrape_hespress",
        bash_command=f"cd {PROJECT} && {PYTHON} run_scraper.py hespress",
    )

    scrape_aljazeera = BashOperator(
        task_id="scrape_aljazeera",
        bash_command=f"cd {PROJECT} && {PYTHON} run_scraper.py aljazeera",
    )

    scrape_bbc = BashOperator(
        task_id="scrape_bbc",
        bash_command=f"cd {PROJECT} && {PYTHON} run_scraper.py bbc",
    )

    bronze_to_silver = BashOperator(
        task_id="bronze_to_silver",
        bash_command=f"cd {PROJECT} && {PYTHON} run_bronze_silver.py",
    )

    quality_check = BashOperator(
        task_id="data_quality_check",
        bash_command=f"cd {PROJECT} && {PYTHON} run_quality.py",
    )

    silver_to_gold = BashOperator(
        task_id="silver_to_gold",
        bash_command=f"cd {PROJECT} && {PYTHON} run_gold.py",
    )

    end = BashOperator(
        task_id="pipeline_end",
        bash_command=f'echo "=== Pipeline terminé $(date) ==="',
    )

    start >> [scrape_hespress, scrape_aljazeera, scrape_bbc]
    [scrape_hespress, scrape_aljazeera, scrape_bbc] >> bronze_to_silver
    bronze_to_silver >> quality_check >> silver_to_gold >> end
