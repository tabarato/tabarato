from .utils.string_utils import strip_all, get_words
from .loader import Loader
import json
import numpy as np
import os
import re
import requests
import pandas as pd
import psycopg2
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

        df[["part_before", "brand_name", "part_after"]] = df.apply(
            lambda row: cls._split_name_brand(row["name"], row["brand"]), 
            axis=1, 
            result_type="expand"
        )
        df["full_text"] = df["part_before"] + " " + df["part_after"]

        tokenizer = AutoTokenizer.from_pretrained("neuralmind/bert-base-portuguese-cased")
        model = AutoModel.from_pretrained("neuralmind/bert-base-portuguese-cased")
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device)
        model.eval()

        sentence_vectors = cls._get_bert_embeddings(df["full_text"].tolist(), model, device, tokenizer)
        
        name_scaler = StandardScaler()
        name_scaled = name_scaler.fit_transform(sentence_vectors)

        brand_scaler = OneHotEncoder(sparse_output=False)
        brand_features = brand_scaler.fit_transform(df[["brand"]])

        features = np.hstack((name_scaled, brand_features))
        
        distance_matrix = pdist(features, metric="cosine")
        linkage_matrix = linkage(distance_matrix, method="ward")
        cluster_labels = fcluster(linkage_matrix, t=0.7, criterion="distance")

        df["cluster"] = cluster_labels.astype(str)

        # df["final_cluster"] = df["cluster"].copy()

        # max_cluster_length = 10
        # for cluster_id in df["cluster"].unique():
        #     cluster_mask = df["cluster"] == cluster_id
        #     cluster_data = df[cluster_mask]
        #     if len(cluster_data) > max_cluster_length:
        #         sub_embeddings = cls._get_bert_embeddings(
        #             cluster_data["part_after"].fillna("") + " " + cluster_data["part_before"].fillna(""), 
        #             model, 
        #             device, 
        #             tokenizer
        #         )
        #         if sub_embeddings is not None:
        #             sub_distance = pdist(sub_embeddings, metric="cosine")
        #             sub_linkage = linkage(sub_distance, method="ward")
        #             sub_clusters = fcluster(sub_linkage, t=0.7, criterion="distance")
        #             df.loc[cluster_mask, "final_cluster"] = [f"{cluster_id}_{sub}" for sub in sub_clusters.astype(str)]

        # df["cluster"] = df["final_cluster"].astype(str)

        cls._evaluate_clusters(features, cluster_labels)

        # TODO: resolver casos como da 3 corações em que clusteredNames estão repetidos
        df["clusteredName"] = df.apply(
            lambda row: cls._build_clustered_name(row["part_before"], row["part_after"], row["brand_name"]), 
            axis=1
        )

        df_grouped = df.groupby(["brand", "cluster"]).agg({
            "clusteredName": "first",
            "name": list,
            "storeId": list,
            "weight": list,
            "measure": list,
            "price": list,
            "oldPrice": list,
            "link": list,
            "cartLink": list,
            "imageUrl": list
        }).reset_index()

        df_grouped["variations"] = df_grouped.apply(cls._group_variations, axis=1)
        df_grouped.drop(columns=["name", "weight", "measure", "storeId", "price", "oldPrice", "link", "cartLink", "imageUrl"], inplace=True)

        return df_grouped

    @classmethod
    def temp_process(cls) -> pd.DataFrame:
        df = Loader.read("silver")
        df.dropna(subset=["name"], inplace=True)

        df[["partBefore", "brandName", "partAfter"]] = df.apply(
            lambda row: cls._split_name_brand(row["name"], row["brand"]), 
            axis=1, 
            result_type="expand"
        )

        df['cleanedName'] = df['partBefore'] + ' ' + df['brandName'] + ' ' + df['weight'].astype(str) + df['measure'].astype(str)
        
        tokenizer = AutoTokenizer.from_pretrained("neuralmind/bert-base-portuguese-cased")
        model = AutoModel.from_pretrained("neuralmind/bert-base-portuguese-cased")
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device)
        model.eval()

        sentence_vectors = cls._get_bert_embeddings(df["cleanedName"].tolist(), model, device, tokenizer)
        
        name_scaler = StandardScaler()
        name_scaled = name_scaler.fit_transform(sentence_vectors)

        brand_scaler = OneHotEncoder(sparse_output=False)
        brand_features = brand_scaler.fit_transform(df[["brand"]])

        features = np.hstack((name_scaled, brand_features))
        
        distance_matrix = pdist(features, metric="cosine")
        linkage_matrix = linkage(distance_matrix, method="ward")
        cluster_labels = fcluster(linkage_matrix, t=0.7, criterion="distance")

        df["cluster"] = cluster_labels.astype(str)

        df["final_cluster"] = df["cluster"].copy()

        max_cluster_length = 10
        for cluster_id in df["cluster"].unique():
            cluster_mask = df["cluster"] == cluster_id
            cluster_data = df[cluster_mask]
            if len(cluster_data) > max_cluster_length:
                sub_embeddings = cls._get_bert_embeddings(cluster_data["cleanedName"].tolist(), model, device, tokenizer)
                if sub_embeddings is not None:
                    sub_distance = pdist(sub_embeddings, metric="cosine")
                    sub_linkage = linkage(sub_distance, method="ward")
                    sub_clusters = fcluster(sub_linkage, t=0.7, criterion="distance")
                    df.loc[cluster_mask, "final_cluster"] = [f"{cluster_id}_{sub}" for sub in sub_clusters.astype(str)]

        df["cluster"] = df["final_cluster"].astype(str)

        cls._evaluate_clusters(features, cluster_labels)

        # TODO: resolver casos como da 3 corações em que clusteredNames estão repetidos
        df["clusteredName"] = df["cleanedName"]

        return df

    @classmethod
    def load(cls, df):
        # df = ti.xcom_pull(task_ids = "process_task")
        Loader.load(df, layer="clustered", name="products")

        records = cls._postgres_load(df)
        products = cls._map_to_products(records)

        Loader.load(pd.DataFrame(products), layer="clustered", name="es-products")

        cls._elasticsearch_load(products)

    @classmethod
    def _build_clustered_name(cls, part_before, part_after, brand_name):
        main_name = f"{part_before} {brand_name}".strip()
        if part_after and part_after.lower() not in main_name.lower():
            return f"{main_name} {part_after}"
        return main_name

    @classmethod
    def _postgres_load(cls, df: pd.DataFrame) -> list:
        conn = psycopg2.connect(
            dbname=cls.POSTGRES_DB,
            user=cls.POSTGRES_USER,
            password=cls.POSTGRES_PASSWORD,
            host="localhost",
            port="5432"
        )
        cursor = conn.cursor()

        unique_brands = df["brand"].unique()
        cursor.executemany("""
            INSERT INTO brands (name)
            VALUES (%s)
            ON CONFLICT (name) DO NOTHING
        """, [(b,) for b in unique_brands])

        cursor.execute("SELECT id, name FROM brands WHERE name = ANY(%s)", (list(unique_brands),))
        brand_map = {name: bid for bid, name in cursor.fetchall()}

        product_entries = []
        for _, row in df.iterrows():
            for variation in row["variations"]:
                product_entries.append((
                    row["clusteredName"],
                    brand_map[row["brand"]],
                    variation["weight"],
                    variation["measure"]
                ))

        cursor.executemany("""
            INSERT INTO products (clustered_name, id_brand, weight, measure)
            VALUES (%s, %s, %s, %s)
        """, product_entries)

        cursor.execute("""
            SELECT id, clustered_name, weight, measure 
            FROM products
        """)
        product_map = {(name, weight, measure): pid for pid, name, weight, measure in cursor.fetchall()}

        store_product_rows = []
        for _, row in df.iterrows():
            for variation in row["variations"]:
                for store in variation["sellers"]:
                    store_product_rows.append((
                        store["storeId"],
                        product_map[(row["clusteredName"], variation["weight"], variation["measure"])],
                        variation["name"],
                        store["price"],
                        store["oldPrice"],
                        store["link"],
                        store["cartLink"],
                        variation["imageUrl"]
                    ))

        cursor.executemany("""
            INSERT INTO store_products (
                id_store, id_product, name,
                price, old_price, link, cart_link, image_url
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, store_product_rows)

        conn.commit()

        cursor.execute("""
            SELECT
                sp.id AS store_product_id,
                sp.id_store,
                sp.name,
                sp.price,
                sp.old_price,
                sp.link,
                sp.cart_link,
                sp.image_url,
                p.id AS product_id,
                p.clustered_name,
                p.weight,
                p.measure,
                b.name AS brand
            FROM store_products sp
            JOIN products p ON sp.id_product = p.id
            JOIN brands b ON p.id_brand = b.id
        """)
        rows = cursor.fetchall()
        colnames = [desc[0] for desc in cursor.description]
        cursor.close()
        conn.close()

        return [dict(zip(colnames, row)) for row in rows]

    @classmethod
    def _map_to_products(cls, records: list) -> list:
        grouped_products = {}

        for record in records:
            key = (record["clustered_name"], record["brand"])
            variation_key = record["product_id"]

            if key not in grouped_products:
                grouped_products[key] = {
                    "clusteredName": record["clustered_name"],
                    "brand": record["brand"],
                    "variations": {}
                }

            product = grouped_products[key]

            if variation_key not in product["variations"]:
                product["variations"][variation_key] = {
                    "productId": record["product_id"],
                    "name": record["name"],
                    "weight": int(record["weight"]) if record["weight"] else None,
                    "measure": record["measure"],
                    "imageUrl": record["image_url"],
                    "prices": []
                }

            price = float(record["price"]) if record["price"] else None
            if price:
                product["variations"][variation_key]["prices"].append(price)

        for product in grouped_products.values():
            variations_list = []
            for variation in product["variations"].values():
                prices = variation.pop("prices")
                variation["minPrice"] = min(prices) if prices else None
                variation["maxPrice"] = max(prices) if prices else None
                variations_list.append(variation)
            product["variations"] = variations_list

        return list(grouped_products.values())

    @classmethod
    def _elasticsearch_load(cls, products):
        bulk_request = ""
        for product in products:
            bulk_request += '{"index": {}}\n'
            bulk_request += json.dumps(product) + "\n"

        headers = {"Content-Type": "application/json"}
        response = requests.post(cls.ELASTICSEARCH_URL + "/products/_bulk", data=bulk_request, headers=headers)

        if response.status_code != 200:
            print(response.text)
            raise Exception(response.text)

    @classmethod
    def _get_bert_embeddings(cls, texts, model, device, tokenizer) -> np.ndarray:
        batch_size = 32
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]

            processed_batch = []
            for text in batch:
                processed_text = cls._remove_stopwords(text)
                processed_batch.append(processed_text)

            inputs = tokenizer(
                processed_batch,
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
    def _split_name_brand(cls, name, brand):
        brand_regex = cls._generate_remove_brand_regex(brand)
        match = re.search(brand_regex, name, flags=re.IGNORECASE)
        if match:
            part_before = name[:match.start()].strip()
            brand_name = name[match.start():match.end()].strip().replace("-", " ")
            part_after = name[match.end():].strip()
        else:
            part_before = name.strip()
            brand_name = ""
            part_after = ""

        part_before = re.sub(r'\s+', ' ', part_before)
        part_after = re.sub(r'\s+', ' ', part_after)
        return part_before, brand_name, part_after

    @classmethod
    def _evaluate_clusters(cls, features, cluster_labels):
        # Filter out noise points (-1 labels) for metrics that don't handle them
        valid_mask = cluster_labels != -1
        n_clusters = len(np.unique(cluster_labels[valid_mask]))
        
        print("\n=== HDBSCAN Clustering Evaluation ===")
        print(f"Number of clusters: {n_clusters}")
        print(f"Noise points: {np.sum(cluster_labels == -1)}")
        
        if n_clusters > 1:
            # Metrics on non-noise points
            print(f"\nMetrics on clean data ({np.sum(valid_mask)} points):")
            print(f"Silhouette Score: {silhouette_score(features[valid_mask], cluster_labels[valid_mask]):.3f}")
            print(f"Davies-Bouldin Index: {davies_bouldin_score(features[valid_mask], cluster_labels[valid_mask]):.3f}")
            print(f"Calinski-Harabasz Index: {calinski_harabasz_score(features[valid_mask], cluster_labels[valid_mask]):.3f}")
        
        # Visualization with noise points
        tsne = TSNE(n_components=2, random_state=42)
        reduced = tsne.fit_transform(features)
        
        plt.figure(figsize=(12,8))
        # Plot noise points first
        noise_mask = cluster_labels == -1
        plt.scatter(reduced[noise_mask, 0], reduced[noise_mask, 1], 
                    c='gray', alpha=0.3, label='Noise')
        
        # Plot clusters
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
                        current_brand = brand
                        break

                    if normalized_name in brand_product_names[brand]:
                        current_name = normalized_name.title()
                        current_brand = brand
                        break

            corrected_brands.append(current_brand)
            corrected_names.append(current_name)

        df["brand"] = corrected_brands
        df["name"] = corrected_names

        return df

    @classmethod
    def _tokenize(cls, row: pd.Series) -> str:
        brand = row["brand"].lower()
        name = row["name"]

        brand_regex = cls._generate_remove_brand_regex(brand)
        name_without_brand = re.sub(brand_regex, "", name, flags=re.IGNORECASE).strip()
        name_without_brand = re.sub(r"\s+", " ", name_without_brand)

        words = re.findall(r"\b[a-zA-ZÀ-ÿ0-9]+\b", name_without_brand)
        filtered_words = [
            word for word in words 
            if word.lower() not in cls.PORTUGUESE_STOPWORDS
        ]
        return filtered_words
    
    @classmethod
    def _generate_remove_brand_regex(cls, brand):
        words = brand.split("-")

        if words[-1].endswith("s"):
            last_word = words[-1][:-1]
            words[-1] = last_word
            s_sufix = r"(\W*s)?"
        else:
            s_sufix = ""

        return r"\b" + r"\W*".join([re.escape(p) for p in words]) + s_sufix + r"\b"

    @classmethod
    def _get_sentence_vector(cls, tokens, model):
        vectors = []
        for token in tokens:
            if token in model.wv:
                vectors.append(model.wv[token])
        if len(vectors) == 0:
            return np.zeros(model.vector_size)
        return np.mean(vectors, axis=0)


    @classmethod
    def _group_variations(cls, row: pd.Series) -> dict:
        variations = [
            {
                "name": n, "weight": w, "measure": m, "storeId": s, "price": p,
                "oldPrice": op, "link": l, "cartLink": cl, "imageUrl": img
            }
            for n, w, m, s, p, op, l, cl, img in zip(
                row["name"], row["weight"], row["measure"], row["storeId"],
                row["price"], row["oldPrice"], row["link"], row["cartLink"], row["imageUrl"]
            )
        ]

        df = pd.DataFrame(variations)

        df_grouped = df.groupby(["weight", "measure", "name"], as_index=False).agg(
            imageUrl=("imageUrl", "first"),  # Apenas uma imagem representativa por variação
            sellers=("storeId", lambda x: [
                {
                    "storeId": store,
                    "price": price,
                    "oldPrice": old_price,
                    "link": link,
                    "cartLink": cart_link
                }
                for store, price, old_price, link, cart_link in zip(
                    x, df.loc[x.index, "price"], df.loc[x.index, "oldPrice"],
                    df.loc[x.index, "link"], df.loc[x.index, "cartLink"]
                )
            ])
        )

        return df_grouped.to_dict(orient="records")