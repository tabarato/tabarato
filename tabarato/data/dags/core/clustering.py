from core.utils.string_utils import tokenize, object_id, timestamp
import json
import numpy as np
import os
import requests
import pandas as pd
from pandas import DataFrame
from pymongo import MongoClient
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import pdist
from scipy.cluster.hierarchy import fcluster, linkage


class Clustering:
    MONGODB_CONNECTION = os.getenv("MONGODB_CONNECTION")
    MONGODB_DATABASE = os.getenv("MONGODB_DATABASE")
    ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL")
    
    @classmethod
    def process(cls, ti) -> DataFrame:
        client = MongoClient(cls.MONGODB_CONNECTION)
        db = client[cls.MONGODB_DATABASE]
        products = db["products"]

        df = pd.DataFrame(list(products.find()))
        df.dropna(subset=["name"], inplace=True)
        df["_id"] = df["_id"].apply(object_id)
        df["tokens"] = df["title"].apply(tokenize)
        df["insertedAt"] = df["insertedAt"].apply(timestamp)

        brand_mapping = {brand: idx for idx, brand in enumerate(df["brand"].unique())}
        df["brand_encoded"] = df["brand"].map(brand_mapping)

        vectorizer = CountVectorizer(tokenizer=lambda x: x.split(), lowercase=True, binary=True)
        product_name_features = vectorizer.fit_transform(df["title"]).toarray()

        scaler = StandardScaler()
        numeric_features = scaler.fit_transform(df[["weight", "brand_encoded"]])

        features = np.hstack((product_name_features, numeric_features))

        distance_matrix = pdist(features, metric="euclidean")
        linkage_matrix = linkage(distance_matrix, method="ward")

        distance_threshold = 5.0  
        cluster_labels = fcluster(linkage_matrix, distance_threshold, criterion="distance")

        df["cluster"] = cluster_labels

        clustered_data = df.groupby("cluster").apply(lambda x: x.to_dict(orient="records")).to_dict()
        
        return clustered_data

    @classmethod
    def load(cls, ti):
        df = ti.xcom_pull(task_ids = "process_task")

        request = ""
        for product in df:
            request += '{"index": {}}\n'
            request += json.dumps(product) + '\n'

        headers = {"Content-Type": "application/json"}
        response = requests.post(cls.ELASTICSEARCH_URL + "/products/_bulk", data=request, headers=headers)

        if response.status_code != 200:
            print(response.text)
            raise Exception(response.text)