from core.utils.string_utils import strip_all, get_words, replace_full_word
from core.loader import Loader
import json
import numpy as np
import os
import re
import requests
import pandas as pd
from gensim.models import Word2Vec
import nltk
from nltk.corpus import stopwords
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from scipy.spatial.distance import pdist
from scipy.cluster.hierarchy import fcluster, linkage

nltk.download('stopwords')

class Clustering:
    ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL")
    PORTUGUESE_STOPWORDS = set(stopwords.words('portuguese'))
    
    @classmethod
    def process(cls, ti) -> pd.DataFrame:
        df = Loader.read("silver")

        df.dropna(subset=["name"], inplace=True)

        tokenized_sentences = df.apply(cls._tokenize, axis=1).tolist()
        model = Word2Vec(sentences=tokenized_sentences, vector_size=128, window=8, min_count=2, workers=4, epochs=20)

        # TODO: melhorar matching, ainda não está 100%
        df["name"] = cls._normalize_names(df, model)
        df = cls._correct_brands(df)

        tokenized_sentences = df.apply(cls._tokenize, axis=1).tolist()
        sentence_vectors = np.array([cls._get_sentence_vector(tokens, model) for tokens in tokenized_sentences])

        name_scaler = StandardScaler()
        name_scaled = name_scaler.fit_transform(sentence_vectors)

        brand_scaler = OneHotEncoder(sparse_output=False)
        brand_features = brand_scaler.fit_transform(df[["brand"]])

        features = np.hstack((name_scaled, brand_features))
        distance_matrix = pdist(features, metric="euclidean")
        linkage_matrix = linkage(distance_matrix, method="ward")
        threshold = 1.0
        cluster_labels = fcluster(linkage_matrix, t=threshold, criterion="distance")

        df["cluster"] = cluster_labels

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
    def _normalize_names(cls, df: pd.DataFrame, model: Word2Vec) -> list:
        names = df["name"]
        brands = df["brand"]

        words_sentences = cls._get_words_sentences(names)
        abbreviations = cls._get_abbreviations(names)

        normalized = cls._normalize_abbreviations(names, brands, words_sentences, model)

        # normalized = cls._normalize_possible_abbreviations(normalized, brands, words_sentences, abbreviations, model)

        return normalized

    @classmethod
    def _get_words_sentences(cls, names: pd.Series):
        words_sentences = {}
        
        for name in names:
            words = get_words(name.lower())
            for i, word in enumerate(words):
                if word in cls.PORTUGUESE_STOPWORDS:
                    continue

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
                    best_match = cls._normalize_abbreviation(matches, word, abbreviation, model, words, i)
                    # if word != best_match:
                    #     print(name, "|", word, "|", best_match)
                    words[i] = best_match

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
                    best_match = cls._normalize_abbreviation(matches, word, abbreviation, model, words, i)
                    if word != best_match:
                        print(name, "|", word, "|", best_match)
                    words[i] = best_match

            normalized_names.append(" ".join(words).replace("{brand}", normalized_brand).title())

        return normalized_names

    @classmethod
    def _normalize_abbreviation(cls, matches, word, abbreviation, model, words_list, word_index):
        abbreviation = word.rstrip(".")

        if not matches or abbreviation not in model.wv:
            return word

        if words_list and word_index is not None:
            start = max(0, word_index - 3)
            end = min(len(words_list), word_index + 4)
            context_words = [
                w for w in words_list[start:word_index] + words_list[word_index+1:end]
                if w in model.wv and w not in cls.PORTUGUESE_STOPWORDS
            ]
        else:
            context_words = []

        target_vec = model.wv[abbreviation]
        context_vec = np.mean([model.wv[w] for w in context_words], axis=0) if context_words else np.zeros_like(target_vec)
        combined_vec = (target_vec + context_vec) / 2

        similarities = []
        for match in matches:
            if match in model.wv:
                similarity = model.wv.cosine_similarities(combined_vec, [model.wv[match]])[0]
                similarities.append((match, similarity))

        if not similarities:
            return word

        best_match = max(similarities, key=lambda x: x[1])
        if best_match[1] < 0.9:
            return word

        return best_match[0]

    @classmethod
    def _tokenize(cls, row: pd.Series) -> str:
        brand = row["brand"].lower()
        name = re.sub(f"\\b{re.escape(brand)}\\b", "", row["name"], flags=re.IGNORECASE)
        name = strip_all(name)

        words = re.findall(r"\b[a-zA-ZÀ-ÿ0-9]+\b", name.lower())
        filtered_words = [
            word for word in words 
            if word not in cls.PORTUGUESE_STOPWORDS
        ]
        
        return filtered_words

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
