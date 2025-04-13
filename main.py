import pandas as pd
from tabarato.extract.bistek import BistekExtractor
from tabarato.transform.bistek import BistekTransformer
from tabarato.extract.angeloni import AngeloniExtractor
from tabarato.transform.angeloni import AngeloniTransformer



if __name__ == "__main__":
    df = pd.read_parquet("data/bistek_raw.parquet", engine="pyarrow")
    temp = df.head(1)
    df_transformed = BistekTransformer.transform(None, df)