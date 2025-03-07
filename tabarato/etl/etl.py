from abc import ABC, abstractmethod
from dotenv import load_dotenv
from pandas import DataFrame

load_dotenv()

class ETL(ABC):
    @abstractmethod
    def extract(self) -> list:
        pass

    @abstractmethod
    def transform(self, data) -> DataFrame:
        pass
    
    @abstractmethod
    def load(self, data) -> None:
        # insert into MongoDB
        pass
        