import datetime as dt
import os
import pathlib
from abc import ABC, abstractmethod
from dotenv import load_dotenv
from pandas import DataFrame
from pymongo import MongoClient

load_dotenv()

class StoreETL(ABC):
    MONGODB_CONNECTION = os.getenv("MONGODB_CONNECTION")
    MONGODB_DATABASE = os.getenv("MONGODB_DATABASE")

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
    def transform(cls, ti) -> DataFrame:
        pass

    @classmethod
    @abstractmethod
    def load(cls, ti) -> None:
        df = ti.xcom_pull(task_ids = "transform_task")

        if df.empty:
            return

        df["storeSlug"] = cls.slug()
        df["insertedAt"] = dt.datetime.now(dt.timezone.utc)
        
        client = MongoClient(cls.MONGODB_CONNECTION)
        db = client[cls.MONGODB_DATABASE]
        products = db["products"]

        products.insert_many(df.to_dict(orient="records"))

        client.close()

        path = "/opt/airflow/data/silver"

        pathlib.Path(path).mkdir(parents=True, exist_ok=True)
        
        df.to_parquet(f"{path}/{cls.slug()}_data.parquet")
