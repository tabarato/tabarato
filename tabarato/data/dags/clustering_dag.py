from core.clustering import Clustering
from datetime import datetime, timedelta
import sys
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor


sys.path.append('/opt/airflow/dags/core')

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 3, 15),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG('clustering_dag', default_args = default_args, schedule_interval = "0 4 * * *") as dag:
    # wait_for_bistek_dag_task = ExternalTaskSensor(
    #     task_id = 'wait_for_bistek_dag_task',
    #     external_dag_id = 'bistek_dag',
    #     external_task_id = None,
    #     mode = 'poke',
    #     timeout = 600
    # )

    # wait_for_angeloni_dag_task = ExternalTaskSensor(
    #     task_id = 'wait_for_angeloni_dag_task',
    #     external_dag_id = 'angeloni_dag',
    #     external_task_id = None,
    #     mode = 'poke',
    #     timeout = 600
    # )

    process_task = PythonOperator(
        task_id = "process_task",
        python_callable = Clustering.process
    )

    load_task = PythonOperator(
        task_id = "load_task",
        python_callable = Clustering.load
    )

    # [wait_for_bistek_dag_task, wait_for_angeloni_dag_task] >> 
    process_task >> load_task
