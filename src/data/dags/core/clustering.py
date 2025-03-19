from core.utils.string_utils import strip_all, get_words
from core.loader import Loader
from collections import Counter
import json
import numpy as np
import os
import re
import requests
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import pdist
from scipy.cluster.hierarchy import fcluster, linkage

class Clustering:
    ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL")
    
    @classmethod
    def process(cls, ti) -> pd.DataFrame:
        df = Loader.read("silver")

        df.dropna(subset=["name"], inplace=True)
        df["name"] = cls._normalize_names(df["name"])
        df = cls._correct_brands(df)
        df["tokens"] = df.apply(cls._tokenize, axis=1)

        # brand_mapping = {brand: idx for idx, brand in enumerate(df["brand"].unique())}
        # df["brand_encoded"] = df["brand"].map(brand_mapping)

        # vectorizer = CountVectorizer(tokenizer=lambda x: x.split(), lowercase=True, binary=True)
        # product_name_features = vectorizer.fit_transform(df["name"]).toarray()

        # scaler = StandardScaler()
        # numeric_features = scaler.fit_transform(df[["weight", "brand_encoded"]])

        # features = np.hstack((product_name_features, numeric_features))

        # distance_matrix = pdist(features, metric="euclidean")
        # linkage_matrix = linkage(distance_matrix, method="ward")

        # distance_threshold = 1.0  
        # cluster_labels = fcluster(linkage_matrix, distance_threshold, criterion="distance")

        # df["cluster"] = cluster_labels

        df_grouped = df.groupby(["brand", "tokens"]).agg({
            "name": "first",
            # "cluster": "first",
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
    def _normalize_names(cls, names: pd.Series) -> list:
        word_frequencies, bigram_frequencies = cls._compute_word_frequencies(names)
        abbreviations = cls._extract_abbreviations(names)

        normalized = [cls._normalize_abbreviations(name, word_frequencies, bigram_frequencies, abbreviations) for name in names]
        
        return normalized

    @classmethod
    def _compute_word_frequencies(cls, names: pd.Series) -> Counter | Counter:
        word_frequencies = Counter()
        bigram_frequencies = Counter()
        
        for name in names:
            words = get_words(name.lower())
            for i, word in enumerate(words):
                if not word.endswith('.'):
                    word_frequencies[word] += 1
                
                if i < len(words) - 1:
                    bigram = (word, words[i + 1])
                    bigram_frequencies[bigram] += 1
                    
        return word_frequencies, bigram_frequencies

    @classmethod
    def _extract_abbreviations(cls, names: pd.Series) -> set:
        abbreviations = set()
        for name in names:
            words = get_words(name.lower())
            for word in words:
                if word.endswith('.'):
                    abbreviations.add(word[:-1])
        return abbreviations

    @classmethod
    def _normalize_abbreviations(cls, name: str, word_frequencies: Counter, bigram_frequencies: Counter, abbreviations: set) -> str:
        words = get_words(name.lower())
        for i, word in enumerate(words):
            if word.endswith('.') or word in abbreviations:
                base = word.rstrip('.')
                next_word = words[i + 1] if i + 1 < len(words) else None
                words[i] = cls._normalize_abbreviation(word_frequencies, bigram_frequencies, word, base, next_word)

        return " ".join(words).title()

    @classmethod
    def _normalize_abbreviation(cls, word_frequencies: Counter, bigram_frequencies: Counter, word: str, abbreviation: str, next_word: str) -> str:
        matches = [w for w in word_frequencies if w.startswith(abbreviation)]

        if next_word:
            bigram_candidates = [(w, next_word) for w in matches if (w, next_word) in bigram_frequencies]
            if bigram_candidates:
                return max(bigram_candidates, key=lambda bg: bigram_frequencies[bg])[0]

        if matches:
            return max(matches, key=lambda w: word_frequencies[w])
        
        return word

    @classmethod
    def _tokenize(cls, row: pd.Series) -> str:
        brand = row["brand"]
        name = re.sub(f"\\b{re.escape(brand)}\\b", "", row["name"], flags=re.IGNORECASE)
        name = strip_all(name)
        words = re.findall(r"\b[a-zA-ZÀ-ÿ0-9]+\b", name.lower())
        return "-".join(sorted(words))

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