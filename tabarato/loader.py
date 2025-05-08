import pathlib
import pandas as pd

class Loader():
    @classmethod
    def load(cls, df: pd.DataFrame, layer: str, name: str) -> None:
        path = f"data/{layer}"

        pathlib.Path(path).mkdir(parents=True, exist_ok=True)
        
        df.to_parquet(f"{path}/{name}.parquet", compression="gzip", engine="pyarrow")

    @classmethod
    def read(cls, layer: str, name: str = None) -> pd.DataFrame:
        if name:
            return pd.read_parquet(f"data/{layer}/{name}.parquet", engine="pyarrow")

        directory = pathlib.Path(f"data/{layer}")
        return pd.concat(
            pd.read_parquet(file) for file in directory.glob("*.parquet", engine="pyarrow")
        )