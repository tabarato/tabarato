from core.angeloni import AngeloniETL
from datetime import datetime
import sys
from airflow import DAG
from airflow.operators.python import PythonOperator


sys.path.append('/opt/airflow/dags/core')

with DAG("angeloni_dag", start_date = datetime(2025, 3, 15), schedule_interval = "0 3 * * *", catchup = False) as dag:
    extract_task = PythonOperator(
        task_id = "extract_task",
        python_callable = AngeloniETL.extract
    )

    transform_task = PythonOperator(
        task_id = "transform_task",
        python_callable = AngeloniETL.transform
    )

    load_task = PythonOperator(
        task_id = "load_task",
        python_callable = AngeloniETL.load
    )

    extract_task >> transform_task >> load_task