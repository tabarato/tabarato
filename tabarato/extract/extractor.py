from tabarato.loader import Loader
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
    def load(cls, df) -> None:
        # df = ti.xcom_pull(task_ids = "extract_task")
        if df.empty:
            return

        Loader.load(df, layer="bronze", name=cls.slug())
