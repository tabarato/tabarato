from core.utils.string_utils import strip_all, get_words, replace_full_word
from core.loader import Loader
import json
import numpy as np
import os
import re
import requests
import pandas as pd
from transformers import AutoTokenizer, AutoModel, pipeline
import torch
from gensim.models import Word2Vec
import nltk
from nltk.corpus import stopwords
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from scipy.spatial.distance import pdist
from scipy.cluster.hierarchy import fcluster, linkage
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE

nltk.download('stopwords')

class Clustering:
    ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL")
    PORTUGUESE_STOPWORDS = set(stopwords.words('portuguese'))

    @classmethod
    def process(cls, ti) -> pd.DataFrame:
        df = Loader.read("silver")
        df.dropna(subset=["name"], inplace=True)

        df[['part_before', 'part_after']] = df.apply(
            lambda row: cls._split_name_brand(row['name'], row['brand']), 
            axis=1, 
            result_type='expand'
        )

        tokenizer = AutoTokenizer.from_pretrained("neuralmind/bert-base-portuguese-cased")
        model = AutoModel.from_pretrained("neuralmind/bert-base-portuguese-cased")
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device)
        model.eval()
        
        # pipe = pipeline('fill-mask', model=model, tokenizer=tokenizer, device=device.index if device.type == 'cuda' else -1)

        # df["name"] = cls._normalize_names(df, pipe)

        sentence_vectors = cls._get_bert_embeddings(df["part_before"].tolist(), model, device, tokenizer)
        
        name_scaler = StandardScaler()
        name_scaled = name_scaler.fit_transform(sentence_vectors)

        brand_scaler = OneHotEncoder(sparse_output=False)
        brand_features = brand_scaler.fit_transform(df[["brand"]])

        features = np.hstack((name_scaled, brand_features))
        
        distance_matrix = pdist(features, metric="cosine")
        linkage_matrix = linkage(distance_matrix, method="ward")
        threshold = 0.7
        cluster_labels = fcluster(linkage_matrix, t=threshold, criterion="distance")

        df["cluster"] = cluster_labels.astype(str)

        df["final_cluster"] = df["cluster"].copy()

        max_cluster_length = 10
        for cluster_id in df["cluster"].unique():
            cluster_mask = df["cluster"] == cluster_id
            cluster_data = df[cluster_mask]
            if len(cluster_data) > max_cluster_length:
                part_after_texts = cluster_data["part_after"].tolist()
                sub_embeddings = cls._get_bert_embeddings(part_after_texts, model, device, tokenizer)
                if sub_embeddings is not None:
                    sub_distance = pdist(sub_embeddings, metric='cosine')
                    sub_linkage = linkage(sub_distance, method='ward')
                    sub_clusters = fcluster(sub_linkage, t=0.7, criterion='distance')
                    df.loc[cluster_mask, "final_cluster"] = [f"{cluster_id}_{sub}" for sub in sub_clusters.astype(str)]

        # Atualiza os clusters finais
        df["cluster"] = df["final_cluster"].astype(str)

        df_grouped = df.groupby(["brand", "cluster"]).agg({
            "name": "first",
            "storeSlug": list,
            "weight": list,
            "measure": list,
            "price": list,
            "oldPrice": list,
            "link": list,
            "cartLink": list
        }).reset_index()

        df_grouped["variations"] = df_grouped.apply(cls._group_variations, axis=1)
        df_grouped.drop(columns=["weight", "measure", "storeSlug", "price", "oldPrice", "link", "cartLink"], inplace=True)

        cls.evaluate_clusters(features, cluster_labels)

        return df_grouped

    @classmethod
    def load(cls, ti):
        df = ti.xcom_pull(task_ids = "process_task")
        
        Loader.load(df, layer="clustered", name="products")

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
    def _get_bert_embeddings(cls, texts, model, device, tokenizer) -> np.ndarray:
        batch_size = 32
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            
            # Preprocess: remove stopwords from each text
            processed_batch = []
            for text in batch:
                # Split text into words while preserving original casing
                words = get_words(text)
                # Filter out stopwords (case-insensitive check)
                filtered_words = [
                    word for word in words 
                    if word.lower() not in cls.PORTUGUESE_STOPWORDS
                ]
                # Rejoin remaining words into a clean text
                processed_text = " ".join(filtered_words)
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
    def _split_name_brand(cls, name, brand):
        brand_regex = cls._generate_remove_brand_regex(brand)
        match = re.search(brand_regex, name, flags=re.IGNORECASE)
        if match:
            part_before = name[:match.start()].strip()
            part_after = name[match.end():].strip()
        else:
            part_before = name.strip()
            part_after = ""
        part_before = re.sub(r'\s+', ' ', part_before)
        part_after = re.sub(r'\s+', ' ', part_after)
        return part_before, part_after

    @classmethod
    def evaluate_clusters(cls, features, labels):
        # Métricas principais
        print(f"Silhouette Score: {silhouette_score(features, labels):.3f}")
        print(f"Davies-Bouldin Index: {davies_bouldin_score(features, labels):.3f}")
        print(f"Calinski-Harabasz Index: {calinski_harabasz_score(features, labels):.3f}")

        # Visualização com t-SNE
        tsne = TSNE(n_components=2, random_state=42)
        reduced = tsne.fit_transform(features)
        
        plt.figure(figsize=(12,8))
        scatter = plt.scatter(reduced[:,0], reduced[:,1], c=labels, cmap='tab20', alpha=0.6)
        plt.title('Visualização 2D dos Clusters (t-SNE)')
        plt.colorbar(scatter)
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
    def _normalize_names(cls, df: pd.DataFrame, pipe) -> list:
        names = df["name"].tolist()
        brands = df["brand"].tolist()
        texts = []

        # for name, brand in zip(names, brands):
        #     brand_regex = cls._generate_remove_brand_regex(brand)
        #     name_without_brand = re.sub(brand_regex, "", name, flags=re.IGNORECASE).strip()
        #     name_without_brand = re.sub(r"\s+", " ", name_without_brand)
        #     texts.append(name_without_brand)

        abbreviations = cls._get_abbreviations(pd.Series(names))

        normalized = cls._normalize_abbreviations(names, brands, pipe)
        return normalized

    @classmethod
    def _normalize_abbreviations(cls, names, brands, pipe):
        normalized_names = []
        
        for name, brand in zip(names, brands):
            # brand_regex = cls._generate_remove_brand_regex(brand)
            # name_without_brand = re.sub(brand_regex, "", name, flags=re.IGNORECASE).strip()
            words = get_words(name.lower())
            
            for i, word in enumerate(words):
                if word.endswith('.'):
                    abbreviation = word.rstrip('.')

                    masked_sentence = ' '.join([
                        w if idx != i else '[MASK]' for idx, w in enumerate(words)
                    ])
                    try:
                        print(masked_sentence)
                        predictions = pipe(masked_sentence, top_k=3)
                        print(predictions)
                        for pred in predictions:
                            token = pred['token_str'].lower()
                            if token != abbreviation:
                                words[i] = token
                                print(name, "|", abbreviation, "|", token)
                                break
                    except:
                        pass

            normalized_names.append(" ".join(words).title())
        
        return normalized_names

    @classmethod
    def _get_abbreviations(cls, names: pd.Series):
        return {word[:-1] for name in names for word in get_words(name.lower()) if word.endswith('.')}

    @classmethod
    def _normalize_possible_abbreviations(cls, names, brands, words_sentences: dict, abbreviations, model):
        normalized_names = []

        for i, name in enumerate(names):
            brand = brands.iloc[i]
            normalized_brand = brand.replace("-", " ")
            words = get_words(name.lower().replace(normalized_brand, "{brand}"))

            for i, word in enumerate(words):
                if word == "{brand}":
                    continue

                if word in abbreviations and len(word) > 1:
                    abbreviation = word.rstrip('.')
                    matches = [w for w in words_sentences.keys() if w.startswith(abbreviation)]
                    best_match = cls._normalize_abbreviation(matches, word, abbreviation, model, words, i)
                    if word != best_match:
                        print(name, "|", word, "|", best_match)
                    words[i] = best_match

            normalized_names.append(" ".join(words).replace("{brand}", normalized_brand).title())

        return normalized_names

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

        if words[-1].endswith('s'):
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
                "weight": w, "measure": m, 
                "storeSlug": s, "price": p, "oldPrice": op, "link": l, "cartLink": cl
            } 
            for w, m, s, p, op, l, cl in zip(
                row["weight"], row["measure"], row["storeSlug"], 
                row["price"], row["oldPrice"], row["link"], row["cartLink"]
            )
        ]

        df = pd.DataFrame(variations)

        df_grouped = df.groupby(["weight", "measure"], as_index=False).agg(
            sellers=("storeSlug", lambda x: [
                {"storeSlug": store, "price": price, "oldPrice": old_price, "link": link, "cartLink": cart_link} 
                for store, price, old_price, link, cart_link in zip(
                    x, df.loc[x.index, "price"], df.loc[x.index, "oldPrice"], 
                    df.loc[x.index, "link"], df.loc[x.index, "cartLink"]
                )
            ])
        )

        return df_grouped.to_dict(orient="records")
