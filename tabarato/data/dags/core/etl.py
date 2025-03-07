from abc import ABC, abstractmethod
from dotenv import load_dotenv
from pandas import DataFrame

load_dotenv()

class ETL(ABC):
    @classmethod
    @abstractmethod
    def extract(cls) -> DataFrame:
        pass

    @classmethod
    @abstractmethod
    def transform(cls, ti) -> DataFrame:
        pass

    @classmethod
    @abstractmethod
    def load(cls, ti) -> DataFrame:
        df = ti.xcom_pull(task_ids = "transform_task")

        with open("/opt/airflow/dags/output/data.json", "w", encoding='utf-8') as file:
            df.to_json(file, orient="records", indent=4, force_ascii=False)
            