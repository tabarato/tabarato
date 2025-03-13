from core.utils.string_utils import tokenize, object_id, timestamp
import json
import numpy as np
import os
import pathlib
import requests
import pandas as pd
from pandas import DataFrame
from pymongo import MongoClient
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import pdist
from scipy.cluster.hierarchy import fcluster, linkage


class Clustering:
    ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL")
    
    @classmethod
    def process(cls, ti) -> DataFrame:
        data_dir = pathlib.Path("/opt/airflow/data/silver")
        df = pd.concat(
            pd.read_parquet(parquet_file) for parquet_file in data_dir.glob("*.parquet")
        )

        df.dropna(subset=["name"], inplace=True)
        df["tokens"] = df["title"].apply(lambda x: tokenize(x, words_to_ignore=["lata"]))

        brand_mapping = {brand: idx for idx, brand in enumerate(df["brand"].unique())}
        df["brand_encoded"] = df["brand"].map(brand_mapping)

        vectorizer = CountVectorizer(tokenizer=lambda x: x.split(), lowercase=True, binary=True)
        product_name_features = vectorizer.fit_transform(df["title"]).toarray()

        scaler = StandardScaler()
        numeric_features = scaler.fit_transform(df[["weight", "brand_encoded"]])

        features = np.hstack((product_name_features, numeric_features))

        distance_matrix = pdist(features, metric="euclidean")
        linkage_matrix = linkage(distance_matrix, method="ward")

        distance_threshold = 1.0  
        cluster_labels = fcluster(linkage_matrix, distance_threshold, criterion="distance")

        df["cluster"] = cluster_labels

        df_grouped = df.groupby(["brand", "tokens"]).agg({
            "name": "first",
            "title": "first",
            "cluster": "first",
            "storeSlug": list,
            "weight": list,
            "measure": list
        }).reset_index()

        df_grouped["variations"] = df_grouped.apply(
            cls._group_variations,
            axis=1
        )

        df_grouped.drop(columns=["weight", "measure", "storeSlug"], inplace=True)

        return df_grouped

    @classmethod
    def load(cls, ti):
        df = ti.xcom_pull(task_ids = "process_task")

        path = "/opt/airflow/data/clustered"

        pathlib.Path(path).mkdir(parents=True, exist_ok=True)
        
        df.to_parquet(f"{path}/products.parquet")

        # request = ""
        # for product in df:
        #     request += '{"index": {}}\n'
        #     request += json.dumps(product) + '\n'

        # headers = {"Content-Type": "application/json"}
        # response = requests.post(cls.ELASTICSEARCH_URL + "/products/_bulk", data=request, headers=headers)

        # if response.status_code != 200:
        #     print(response.text)
        #     raise Exception(response.text)
    
    @classmethod
    def _group_variations(cls, row):
        variations = [{"weight": w, "measure": m, "storeSlug": s} for w, m, s in zip(row["weight"], row["measure"], row["storeSlug"])]

        df = pd.DataFrame(variations)

        df = df.groupby(["weight", "measure"], as_index=False).agg({
            "storeSlug": list
        })

        df.rename(columns={"storeSlug": "stores"}, inplace=True)

        return df.to_dict(orient="records")