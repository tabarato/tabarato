from core.transform.bistek import BistekTransformer
from datetime import datetime
import sys
from airflow import DAG
from airflow.operators.python import PythonOperator


sys.path.append('/opt/airflow/dags/core')

with DAG("bistek_transform_dag", start_date = datetime(2025, 3, 15), schedule_interval = None, catchup = False) as dag:
    transform_task = PythonOperator(
        task_id = "transform_task",
        python_callable = BistekTransformer.transform
    )

    load_task = PythonOperator(
        task_id = "load_task",
        python_callable = BistekTransformer.load
    )

    transform_task >> load_task