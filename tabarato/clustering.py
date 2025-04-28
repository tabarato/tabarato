from .utils.string_utils import strip_all, get_words
from .loader import Loader
from collections import Counter
import numpy as np
import os
import pandas as pd
import matplotlib.pyplot as plt
import nltk
from nltk.corpus import stopwords
from scipy.spatial.distance import pdist
from scipy.cluster.hierarchy import fcluster, linkage
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
from sklearn.manifold import TSNE
from gensim.models import Word2Vec
import dotenv
import seaborn as sns

dotenv.load_dotenv()

nltk.download("stopwords")

class Clustering:
    PORTUGUESE_STOPWORDS = set(stopwords.words("portuguese"))

    @classmethod
    def process(cls) -> pd.DataFrame:
        df = Loader.read("silver")
        df = df[~((df["price"] == 0) & (df["old_price"] == 0))]

        # cls._correct_brands(df)

        print("Tokenizing...")
        model = Word2Vec.load("data/model/w2v.model")
        features = cls._get_features(df, model)

        print("Clustering...")
        distance_matrix = pdist(features, metric="cosine")
        linkage_matrix = linkage(distance_matrix, method="average")
        df["cluster"] = fcluster(linkage_matrix, t=0.05, criterion="distance")

        cls._evaluate_clusters(features, df["cluster"].astype(int).values)

        df["clustered_name"] = df["name"]

        df_grouped = df.groupby(["brand", "cluster"]).agg({
            "clustered_name": "first",
            "name": list,
            "store_id": list,
            "weight": list,
            "measure": list,
            "price": list,
            "old_price": list,
            "link": list,
            "cart_link": list,
            "image_url": list
        }).reset_index()

        df_grouped["variations"] = df_grouped.apply(cls._group_variations, axis=1)
        df_grouped.drop(columns=["name", "weight", "measure", "store_id", "price", "old_price", "link", "cart_link", "image_url"], inplace=True)

        return df_grouped

    @classmethod
    def load(cls, df):
        # df = ti.xcom_pull(task_ids = "process_task")

        Loader.load(df, layer="gold", name="products")

    @classmethod
    def _get_features(cls, df, model, min_ngram_freq=5, alpha=0.8):
        docs = [get_words(name.lower()) for name in df["name_without_brand"].tolist()]
        docs_phrased = [model.phraser[doc] for doc in docs]

        all_tokens = Counter(token for doc in docs_phrased for token in doc)
        main_terms = {token for token, count in all_tokens.items() if count >= min_ngram_freq}

        embeddings, binaries = [], []
        for doc in docs_phrased:
            vecs = []
            for token in doc:
                if token in model.wv:
                    weight = 2.0 if "_" in token else 1.0
                    vecs.append(model.wv[token] * weight)

            if vecs:
                emb = np.mean(vecs, axis=0)
                norm = np.linalg.norm(emb)
                emb = emb / norm if norm != 0 else emb
            else:
                emb = np.zeros(model.vector_size)
            embeddings.append(emb)

            presence = np.array([1 if term in doc else 0 for term in main_terms])
            binaries.append(presence)

        embeddings = np.vstack(embeddings)
        binaries = np.vstack(binaries)

        name_features = StandardScaler().fit(embeddings).transform(embeddings) * 0.8
        # binary_features = StandardScaler().fit(binaries).transform(binaries) * 0.2
        brand_encoded = OneHotEncoder(sparse_output=False).fit_transform(df[["brand"]]) * 0.2

        return np.hstack([name_features, brand_encoded])

    @classmethod
    def _evaluate_clusters(cls, features, cluster_labels):
        valid_mask = cluster_labels != -1
        n_clusters = len(np.unique(cluster_labels[valid_mask]))
        
        print("\n=== Clustering Evaluation ===")
        print(f"Number of clusters: {n_clusters}")
        print(f"Noise points: {np.sum(cluster_labels == -1)}")
        
        if n_clusters > 1:
            print(f"\nMetrics on clean data ({np.sum(valid_mask)} points):")
            print(f"Silhouette Score: {silhouette_score(features[valid_mask], cluster_labels[valid_mask]):.3f}")
            print(f"Davies-Bouldin Index: {davies_bouldin_score(features[valid_mask], cluster_labels[valid_mask]):.3f}")
            print(f"Calinski-Harabasz Index: {calinski_harabasz_score(features[valid_mask], cluster_labels[valid_mask]):.3f}")

        # tsne = TSNE(n_components=2, random_state=42)
        # reduced = tsne.fit_transform(features)

        # plt.figure(figsize=(14,6))
        # plt.subplot(1,2,1)
        # sns.scatterplot(
        #     x=reduced[:,0], 
        #     y=reduced[:,1], 
        #     hue=cluster_labels,
        #     palette='tab20',
        #     legend=False
        # )

        # plt.subplot(1,2,2)
        # sns.kdeplot(
        #     x=reduced[:,0], 
        #     y=reduced[:,1], 
        #     cmap='viridis', 
        #     fill=True
        # )
        # plt.show()

    @classmethod
    def _correct_brands(cls, df: pd.DataFrame) -> pd.DataFrame:
        all_brands = set(df["brand"].unique())

        brand_product_names = {}
        for brand in all_brands:
            brand_product_names[brand] = set(df[df["brand"] == brand]["name"].str.lower())

        corrected_brands = []
        corrected_names = []
        
        for _, row in df.iterrows():
            current_brand = row["brand"].lower()
            current_name = row["name"]

            normalized_name = strip_all(current_name.lower().replace(current_brand, ""))
            
            for brand in all_brands:
                if brand == current_brand:
                    continue

                if brand in normalized_name:
                    if current_name in brand_product_names[brand]:
                        print(current_brand, "|", brand)
                        current_brand = brand
                        break

                    if normalized_name in brand_product_names[brand]:
                        print(current_name, "|", normalized_name)
                        current_name = normalized_name.title()
                        current_brand = brand
                        break

            corrected_brands.append(current_brand)
            corrected_names.append(current_name)

        df["brand"] = corrected_brands
        df["name"] = corrected_names

        return df

    @classmethod
    def _group_variations(cls, row: pd.Series) -> dict:
        variations = [
            {
                "name": n, "weight": w, "measure": m, "store_id": s, "price": p,
                "old_price": op, "link": l, "cart_link": cl, "image_url": img
            }
            for n, w, m, s, p, op, l, cl, img in zip(
                row["name"], row["weight"], row["measure"], row["store_id"],
                row["price"], row["old_price"], row["link"], row["cart_link"], row["image_url"]
            )
        ]

        df = pd.DataFrame(variations)

        df_grouped = df.groupby(["weight", "measure"], as_index=False).agg(
            name=("name", "first"), # Apenas um nome representativo por variação
            image_url=("image_url", "first"), # Apenas uma imagem representativa por variação
            sellers=("store_id", lambda x: [
                {
                    "store_id": store,
                    "price": price,
                    "old_price": old_price,
                    "link": link,
                    "cart_link": cart_link
                }
                for store, price, old_price, link, cart_link in zip(
                    x, df.loc[x.index, "price"], df.loc[x.index, "old_price"],
                    df.loc[x.index, "link"], df.loc[x.index, "cart_link"]
                )
            ])
        )

        return df_grouped.to_dict(orient="records")
