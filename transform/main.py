import numpy as np
import pandas as pd
import scipy.cluster.hierarchy as sch
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import pdist
import json
from scipy.cluster.hierarchy import fcluster


DATA_PATH = "..\\scraping-bistek\\data.json"


if __name__ == "__main__":
    df = pd.read_json(DATA_PATH)

    print(df.info())
    print(df.describe())

    vectorizer = TfidfVectorizer()
    product_name_features = vectorizer.fit_transform(df["productName"]).toarray()

    brand_mapping = {brand: idx for idx, brand in enumerate(df["brand"].unique())}
    df["brand_encoded"] = df["brand"].map(brand_mapping)

    df["weight"] = df["Peso Produto"].apply(lambda x: float(x) if isinstance(x, (int, float)) else float(x[0])).fillna(0)

    scaler = StandardScaler()
    numeric_features = scaler.fit_transform(df[["weight", "brand_encoded"]])

    features = np.hstack((product_name_features, numeric_features))

    distance_matrix = pdist(features, metric="euclidean")

    linkage_matrix = sch.linkage(distance_matrix, method="ward")

    distance_threshold = 5.0  

    cluster_labels = fcluster(linkage_matrix, distance_threshold, criterion="distance")
    df["cluster"] = cluster_labels

    clustered_data = df.groupby("cluster").apply(lambda x: x.to_dict(orient="records")).to_dict()
    json_output = json.dumps(clustered_data, indent=4, ensure_ascii=False)

    with open("clustered_products.json", "w", encoding="utf-8") as f:
        f.write(json_output)

    plt.figure(figsize=(10, 5))
    sch.dendrogram(linkage_matrix, labels=df["productName"].values, leaf_rotation=90)
    plt.title("Hierarchical Clustering Dendrogram")
    plt.xlabel("Products")
    plt.ylabel("Distance")
    plt.show()