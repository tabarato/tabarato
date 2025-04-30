from .utils.string_utils import get_words
from .loader import Loader
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import nltk
from nltk.corpus import stopwords
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
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

        print("Tokenizing...")
        model = Word2Vec.load("data/model/w2v.model")
        features = cls._get_features(model, df["name_without_brand"])

        print("Clustering...")
        db = DBSCAN(
            eps=0.01,
            min_samples=1,
            metric="euclidean"
        ).fit(features)

        df["cluster"] = db.labels_

        cls._evaluate_clusters(features, df["cluster"].values)

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
        
        def has_multiple_sellers(variations):
            return any(len(v["sellers"]) > 1 for v in variations)

        df_grouped = df_grouped[df_grouped["variations"].apply(has_multiple_sellers)]

        return df_grouped

    @classmethod
    def load(cls, df):
        # df = ti.xcom_pull(task_ids = "process_task")

        Loader.load(df, layer="gold", name="products")

    @classmethod
    def _get_features(cls, model, names):
        docs = [
            [word for word in get_words(n.lower()) if word not in cls.PORTUGUESE_STOPWORDS]
            for n in names
        ]
        docs_phrased = [model.phraser[doc] for doc in docs]

        embeddings = []
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

        embeddings = np.vstack(embeddings)

        name_features = StandardScaler().fit(embeddings).transform(embeddings)

        return name_features

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

        tsne = TSNE(n_components=2, random_state=42)
        reduced = tsne.fit_transform(features)
        plt.figure(figsize=(14,6))
        plt.subplot(1,2,1)
        sns.scatterplot(
            x=reduced[:,0], 
            y=reduced[:,1], 
            hue=cluster_labels,
            palette='tab20',
            legend=False
        )
        plt.subplot(1,2,2)
        sns.kdeplot(
            x=reduced[:,0], 
            y=reduced[:,1], 
            cmap='viridis', 
            fill=True
        )
        plt.show()

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
