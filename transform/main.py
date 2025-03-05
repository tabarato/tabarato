import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import pdist
from scipy.cluster.hierarchy import fcluster, linkage, dendrogram
import json
import re
import math


DATA_PATH = "..\\scraping-bistek\\data.json"


def tokenize(text):
    text = text.lower()
    words = re.findall(r"\b[a-zA-ZÀ-ÿ0-9]+\b", text)
    return words


def normalize_product_name(row):
    product_name = row["productName"]
    brand = row["brand"]
    weight = int(row["weight"])
    measure = row["measure"]

    if weight < 1000:
        measurement_text = str(weight) + measure
    else:
        if measure == "g":
            measure = "KG"
        else:
            measure = "LT"

        measurement_text = str(weight / 1000) + measure

    product_name = re.sub(re.escape(brand), "", product_name, flags=re.IGNORECASE)

    product_name = re.sub(re.escape(measurement_text), "", product_name, flags=re.IGNORECASE)

    product_name = re.sub(r"\s+", " ", product_name).strip()

    return product_name


def normalize_measurement(row):
    raw_weight = row["Peso Produto"]
    raw_measure = row["Unidade de Medida"]
    
    weight = float(raw_weight[0]) if raw_weight and isinstance(raw_weight, list) else float(raw_weight)
    measure = str(raw_measure[0]) if raw_measure and isinstance(raw_measure, list) else str(raw_measure)

    if math.isnan(weight):
        product_name = row["productName"]
        match = re.search(r"(\d+)\s*(ml|g|kg|l|lt)", product_name, re.IGNORECASE)

        if match:
            weight = match.group(1)
            measure = match.group(2)
        else:
            weight = 0
            measure = ""

    if measure.upper() == "KG":
        weight *= 1000
        measure = "g"
    elif measure.upper() == "LT":
        weight *= 1000
        measure = "ml"
    
    return pd.Series([measure, weight])


if __name__ == "__main__":
    df = pd.read_json(DATA_PATH)

    brand_mapping = {brand: idx for idx, brand in enumerate(df["brand"].unique())}
    df["brand_encoded"] = df["brand"].map(brand_mapping)

    df[["measure", "weight"]] = df.apply(normalize_measurement, axis=1)

    df["normalized_product_name"] = df.apply(normalize_product_name, axis=1)
    df["tokens"] = df["normalized_product_name"].apply(tokenize)

    df.drop(["productId", "brandId", "brandImageUrl",
             "productReference", "productReferenceCode", "categoryId", 
             "metaTagDescription", "releaseDate", "clusterHighlights",
             "productClusters", "searchableClusters", "categories",
             "categoriesIds", "link", "Peso Produto",
             "Unidade de Medida", "Especificações", "allSpecifications",
             "allSpecificationsGroups", "description", "items",
             "productTitle", "linkText"], axis=1, inplace=True)

    print(df.info())
    print(df.describe())

    vectorizer = CountVectorizer(tokenizer=lambda x: x.split(), lowercase=True, binary=True)
    product_name_features = vectorizer.fit_transform(df["normalized_product_name"]).toarray()

    scaler = StandardScaler()
    numeric_features = scaler.fit_transform(df[["weight", "brand_encoded"]])

    features = np.hstack((product_name_features, numeric_features))

    distance_matrix = pdist(features, metric="euclidean")
    linkage_matrix = linkage(distance_matrix, method="ward")

    distance_threshold = 5.0  
    cluster_labels = fcluster(linkage_matrix, distance_threshold, criterion="distance")

    df["cluster"] = cluster_labels

    clustered_data = df.groupby("cluster").apply(lambda x: x.to_dict(orient="records")).to_dict()
    json_output = json.dumps(clustered_data, indent=4, ensure_ascii=False)

    with open("clustered_products.json", "w", encoding="utf-8") as f:
        f.write(json_output)

    plt.figure(figsize=(10, 5))
    dendrogram(linkage_matrix, labels=df["productName"].values, leaf_rotation=90)
    plt.title("Hierarchical Clustering Dendrogram")
    plt.xlabel("Products")
    plt.ylabel("Distance")
    plt.show()