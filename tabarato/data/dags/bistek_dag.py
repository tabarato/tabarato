from core.bistek import BistekETL
from datetime import datetime
import sys
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator, BranchPythonOperator


sys.path.append('/opt/airflow/dags/core')

with DAG("bistek_dag", start_date = datetime(2025, 3, 1), schedule_interval = "0 3 * * *", catchup = False) as dag:
    extract_task = PythonOperator(
        task_id = "extract_task",
        python_callable = BistekETL.extract
    )

    transform_task = PythonOperator(
        task_id = "transform_task",
        python_callable = BistekETL.transform
    )

    load_task = PythonOperator(
        task_id = "load_task",
        python_callable = BistekETL.load
    )

    extract_task >> transform_task >> load_task