from .utils.string_utils import strip_all, get_words
from .loader import Loader
import numpy as np
import os
import pandas as pd
from transformers import AutoTokenizer, AutoModel
import torch
import matplotlib.pyplot as plt
import nltk
from nltk.corpus import stopwords
from scipy.spatial.distance import pdist
from scipy.cluster.hierarchy import fcluster, linkage
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA
import dotenv

dotenv.load_dotenv()

nltk.download("stopwords")

class Clustering:
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_DB = os.getenv("POSTGRES_DB")
    ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL")
    PORTUGUESE_STOPWORDS = set(stopwords.words("portuguese"))

    @classmethod
    def process(cls) -> pd.DataFrame:
        df = Loader.read("silver")
        df.dropna(subset=["name"], inplace=True)

        categories = df["category"].dropna()
        categories = categories[categories.str.strip() != ""].unique().tolist()
        
        df = df[~((df["price"] == 0) & (df["old_price"] == 0))]

        # cls._correct_brands(df)

        df[["name", "name_without_brand", "category", "part_after"]] = df.apply(
            lambda row: cls._normalize_category(row, categories), 
            axis=1, 
            result_type="expand"
        )

        df = df[df["category"] != ""]

        tokenizer = AutoTokenizer.from_pretrained("neuralmind/bert-base-portuguese-cased")
        model = AutoModel.from_pretrained("neuralmind/bert-base-portuguese-cased")
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device)
        model.eval()

        print("Tokenizing...")
        sentence_vectors = cls._get_bert_embeddings(df["category"].tolist(), model, device, tokenizer)
        
        name_scaler = StandardScaler()
        name_scaled = name_scaler.fit_transform(sentence_vectors)

        brand_scaler = OneHotEncoder(sparse_output=False)
        brand_features = brand_scaler.fit_transform(df[["brand"]])

        features = np.hstack((name_scaled, brand_features))

        print("Clustering...")
        distance_matrix = pdist(features, metric="cosine")
        linkage_matrix = linkage(distance_matrix, method="average")
        df["cluster"] = fcluster(linkage_matrix, t=0.3, criterion="distance").astype(str)

        cls._evaluate_clusters(features, df["cluster"].astype(int).values)
        
        cls._subcluster_by_part_after(df, model, device, tokenizer)

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
    def _subcluster_by_part_after(cls, df: pd.DataFrame, model, device, tokenizer):
        for cid in df["cluster"].unique():
            mask = df["cluster"] == cid
            group = df[mask]
            
            if len(group) <= 1:
                continue

            sub_embeddings = cls._get_bert_embeddings(
                group["part_after"].fillna(""), 
                model, 
                device, 
                tokenizer
            )
            
            if sub_embeddings is not None:
                sub_distance = pdist(sub_embeddings, metric="cosine")
                sub_linkage = linkage(sub_distance, method="average")
                sub_clusters = fcluster(sub_linkage, t=0.2, criterion="distance")

                unique_sub_clusters = np.unique(sub_clusters)
                if len(unique_sub_clusters) > 1:
                    df.loc[mask, "cluster"] = [f"{cid}_{sub}" for sub in sub_clusters.astype(str)]

    @classmethod
    def _get_bert_embeddings(cls, texts, model, device, tokenizer) -> np.ndarray:
        batch_size = 128
        embeddings = []

        texts = [cls._remove_stopwords(text) for text in texts]

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]

            inputs = tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=64,
                return_tensors="pt"
            ).to(device)

            with torch.no_grad():
                outputs = model(**inputs)

            batch_embeddings = outputs.last_hidden_state.mean(dim=1).cpu().numpy()
            embeddings.append(batch_embeddings)

        return np.vstack(embeddings)

    @classmethod
    def _remove_stopwords(cls, text):
        words = get_words(text)
        filtered_words = [
            word for word in words 
            if word.lower() not in cls.PORTUGUESE_STOPWORDS
        ]
        return " ".join(filtered_words)

    @classmethod
    def _normalize_category(cls, row, known_categories):
        name = row["name"]
        name_without_brand = row["name_without_brand"]
        category = row["category"]
        brand_name = row["brand_name"]

        matching_categories = [cat for cat in known_categories if name_without_brand.lower().startswith(cat)]
        if matching_categories:
            sorted_categories = sorted(matching_categories, key=len, reverse=True)
            matching_category = sorted_categories[0]
        else:
            matching_category = None

        if matching_category:
            category = matching_category.strip()
            part_after = name_without_brand[len(category):].strip()
            category_name = name_without_brand[:len(category)]
            name_without_brand = category_name + " " + part_after
            name_without_brand = category_name + " " + brand_name + " " + part_after
        else:
            category = ""
            part_after = name_without_brand.strip()

        return name, name_without_brand, category, part_after

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

        plt.figure(figsize=(12,8))
        noise_mask = cluster_labels == -1
        plt.scatter(reduced[noise_mask, 0], reduced[noise_mask, 1], 
                    c='gray', alpha=0.3, label='Noise')

        unique_labels = np.unique(cluster_labels[valid_mask])
        colors = plt.cm.tab20(np.linspace(0, 1, len(unique_labels)))
    
        for label, color in zip(unique_labels, colors):
            mask = cluster_labels == label
            plt.scatter(reduced[mask, 0], reduced[mask, 1], 
                        c=[color], label=f'Cluster {label}', alpha=0.6)

        plt.title('HDBSCAN Cluster Visualization (t-SNE)')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.show()

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
            name=("name", "first"),  # Apenas um nome representativo por variação
            image_url=("image_url", "first"),  # Apenas uma imagem representativa por variação
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
