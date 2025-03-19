from core.utils.string_utils import strip_all, get_words, replace_full_word
from core.loader import Loader
from collections import Counter
import json
import numpy as np
import os
import re
import requests
import pandas as pd
from gensim.models import Word2Vec
from gensim.utils import simple_preprocess
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
        df["name"] = cls._normalize_names(df)
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
    def _normalize_names(cls, df: pd.DataFrame) -> list:
        names = df["name"]
        brands = df["brand"]

        words_sentences = cls._get_words_sentences(names)
        abbreviations = cls._get_abbreviations(names)

        tokenized_sentences = [simple_preprocess(sent) for sent in names]
        model = Word2Vec(sentences=tokenized_sentences, vector_size=100, window=5, min_count=2, epochs=20)

        normalized = cls._normalize_abbreviations(names, brands, words_sentences, model)
        
        tokenized_sentences = [simple_preprocess(sent) for sent in normalized]
        model.build_vocab(tokenized_sentences, update=True)
        model.train(tokenized_sentences, total_examples=len(tokenized_sentences), epochs=10)

        normalized = cls._normalize_possible_abbreviations(normalized, brands, words_sentences, abbreviations, model)

        return normalized

    @classmethod
    def _get_words_sentences(cls, names: pd.Series):
        words_sentences = {}
        
        for name in names:
            words = get_words(name.lower())
            for i, word in enumerate(words):
                if not word.endswith('.') and len(word) > 1:
                    if words_sentences.get(word):
                        words_sentences[word].append(name.lower())
                    else:
                        words_sentences[word] = [name.lower()]

        return words_sentences

    @classmethod
    def _get_abbreviations(cls, names: pd.Series):
        return {word[:-1] for name in names for word in get_words(name.lower()) if word.endswith('.')}

    @classmethod
    def _normalize_abbreviations(cls, names, brands, words_sentences: dict, model):
        normalized_names = []

        for i, name in enumerate(names):
            brand = brands.iloc[i]
            normalized_brand = brand.replace("-", " ")
            words = get_words(name.lower().replace(normalized_brand, "{brand}"))

            for i, word in enumerate(words):
                if word == "{brand}":
                    continue

                if word.endswith('.'):
                    abbreviation = word.rstrip('.')
                    matches = [w for w in words_sentences.keys() if w.startswith(abbreviation) and w != abbreviation]
                    words[i] = cls._normalize_abbreviation(words_sentences, matches, name, word, model)

            normalized_names.append(" ".join(words).replace("{brand}", normalized_brand).title())

        return normalized_names
    
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
                    best_match = cls._normalize_abbreviation(words_sentences, matches, name, word, model, reduce_equal_boost=0.04)
                    if word != best_match:
                        print(name, "|", word, "|", best_match)
                    words[i] = best_match

            normalized_names.append(" ".join(words).replace("{brand}", normalized_brand).title())

        return normalized_names

    @classmethod
    def _normalize_abbreviation(cls, words_sentences, matches, name, word, model, reduce_equal_boost = None):
        if not matches:
            return word

        similarities = []
        for match in matches:
            if match in model.wv:
                sentences = words_sentences[match]
                for sentence in sentences:
                    similarity = model.wv.n_similarity(replace_full_word(name.lower(), word, match).split(), sentence.split())

                    if similarity > 0.8:
                        if match == word and reduce_equal_boost:
                            similarity -= reduce_equal_boost

                        similarities.append((match, similarity))

        if similarities:
            return max(similarities, key=lambda sc: sc[1])[0]

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