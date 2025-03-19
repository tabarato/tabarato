import pathlib
from abc import ABC, abstractmethod
from pandas import DataFrame

class Extractor(ABC):
    @classmethod
    @abstractmethod
    def slug(cls) -> str:
        pass
    
    @classmethod
    @abstractmethod
    def extract(cls) -> DataFrame:
        pass

    @classmethod
    @abstractmethod
    def load(cls, ti) -> None:
        df = ti.xcom_pull(task_ids = "extract_task")
        if df.empty:
            return

        path = f"/opt/airflow/data/bronze"

        pathlib.Path(path).mkdir(parents=True, exist_ok=True)
        
        df.to_parquet(f"{path}/{cls.slug()}.parquet")
