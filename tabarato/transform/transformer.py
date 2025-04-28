from tabarato.utils.string_utils import strip_all
from tabarato.loader import Loader
import datetime as dt
import math
import re
import pandas as pd
from abc import ABC, abstractmethod
from unidecode import unidecode
from rapidfuzz import process, fuzz


class Transformer(ABC):
    LIQUID_MEASUREMENT = [
        "mililitros",
        "mililitro",
        "ml",
        "litros",
        "litro",
        "lt",
        "l"
    ]
    SOLID_MEASUREMENT = [
        "quilogramas",
        "quilograma",
        "quilos",
        "quilo",
        "kg",
        "gramas",
        "grama",
        "g"
    ]
    MEASUREMENT = LIQUID_MEASUREMENT + SOLID_MEASUREMENT
    DETAILS = [
        "lata",
        "vd",
        "pct",
        "cx",
        "fd",
        "pet",
        "pacote",
        "garrafa",
        "ln",
        "long neck",
        "descartavel",
        "frasco",
        "saco",
        "tablete",
        "barra",
        "cartela",
        "fardo",
        "balde",
        "galao",
        "tubo",
        "ampola",
        "pote",
        "kg",
        "litro",
        "lt",
        "caixa",
        "pack",
        "embalagem economica",
        "kit",
        "gfa",
        "gf",
        "bj",
        "bandeja",
        "sache"
    ]
    UNIT = [
        "unidades",
        "unidade",
        "unidadaes",
        r"un\.",
        "un"
    ]

    @classmethod
    @abstractmethod
    def slug(cls) -> str:
        pass

    @classmethod
    @abstractmethod
    def id(cls) -> int:
        pass

    @classmethod
    @abstractmethod
    def transform(cls, df: pd.DataFrame) -> pd.DataFrame:
        df[["measure", "weight"]] = df.apply(cls._transform_measurement, axis=1)
        df["brand"] = df.apply(cls._transform_brand, axis=1)
        df["name"] = df.apply(cls._transform_name, axis=1)
        df[["name", "name_without_brand", "brand_name"]] = df.apply(lambda row: cls._normalize_name_and_brand(row["name"], row["brand"]), axis=1, result_type="expand")

        return df.filter(items=[
            "name", "name_without_brand", "brand_name", "brand", "refId",
            "measure", "weight", "link", "cart_link",
            "price", "old_price", "description", "details",
            "image_url"
        ])

    @classmethod
    @abstractmethod
    def load(cls, df) -> None:
        # df = ti.xcom_pull(task_ids = "transform_task")
        if df.empty:
            return

        df["store_id"] = cls.id()
        df["insertedAt"] = dt.datetime.now(dt.timezone.utc)

        Loader.load(df, layer="silver", name=cls.slug())
    
    @classmethod
    def _transform_name(cls, row: pd.Series) -> str:
        name = row["name"].lower()

        ignore_patterns = [
            r"(?:leve\s(?:\w+|\+|mais)\s(?:e\s)?)?pague\s(?:\w+|\-|menos)", # leve + pague -
            r"l\+p\-", # l+p-
            r"\b\d+(?:[.,]\d+)?\s*(?:" + "|".join(cls.MEASUREMENT) + r")\b\.?\b", # peso
            r"\b(tradicional|trad\.|trad)\b", # tradicional
            r"\d+%\w+\.?", # percentual
            r"(?:c/|com)\s*(\d+(?:/\d+)?)(?:\s*(?:" + "|".join(cls.UNIT) + r"))?", # com X unidades
            r"(\d+(?:/\d+)?)(?:\s*(?:" + "|".join(cls.UNIT) + r"))(?!\s*\w)", # X unidades
            r"(?:" + "|".join(cls.UNIT) + r")(?!\s*\w)", # Unidades
            r"(?<!^)\b(\d+(?:[.,]\d+)?)?\s*(?:" + "|".join(cls.DETAILS) + r")\b\.?\b"
        ]

        for pattern in ignore_patterns:
            name = re.sub(pattern, "", name, flags=re.IGNORECASE)

        replace_patterns = {
            r"\bp/(?!\s?\d)": "para ", # p/ -> para
            r"\bs/(?!\s?\d)": "sem ", # s/ -> sem
            r"\bc/(?!\s?\d)": "com ", # c/ -> com
            r"\b\s?/\s?(?!\s?\d)": " e " # X/Y -> X e Y
        }

        for pattern, replacement in replace_patterns.items():
            name = re.sub(pattern, replacement, name, flags=re.IGNORECASE)

        name = name.replace("-", " ")
        name = re.sub(r"(?<!\d)\.(?!\d)", ". ", name)
        name = strip_all(name)
        name = unidecode(name)

        return name.title()

    @classmethod
    def _transform_brand(cls, row: pd.Series) -> str:
        brand = row["brand"]

        brand = brand.replace("'", "")
        brand = unidecode(brand)
        brand = strip_all(brand)
        brand = brand.replace(" ", "-")

        return brand.lower()

    @classmethod
    def _transform_measurement(cls, row: pd.Series) -> pd.Series:
        raw_weight = row["weight"]
        raw_measure = row["measure"]
        
        def get_from_list_or_default(value):
            try:
                return list(value)[0]
            except:
                return value
        
        try:
            weight = float(get_from_list_or_default(raw_weight).replace(",", ".")) if raw_weight else None
            measure = str(get_from_list_or_default(raw_measure).lower() if raw_measure else None)
        except Exception:
            weight = None
            measure = None

        if not weight or not measure or math.isnan(weight) or (measure not in cls.SOLID_MEASUREMENT and measure not in cls.LIQUID_MEASUREMENT and measure not in cls.UNIT):
            name = row["name"]
            solid_match = re.search(f"(\d+)\s*({'|'.join(cls.SOLID_MEASUREMENT)})", name, re.IGNORECASE)
            liquid_match = re.search(fr"(\d+(?:[.,]\d+)?)\s*({'|'.join(cls.LIQUID_MEASUREMENT)})", name, re.IGNORECASE)
            unit_match = re.search(f"(\d+)\s*({'|'.join(cls.UNIT)})", name, re.IGNORECASE)

            if solid_match:
                weight = float(solid_match.group(1))
                measure = str(solid_match.group(2)).lower()
            elif liquid_match:
                weight = float(liquid_match.group(1).replace(",", "."))
                measure = str(liquid_match.group(2)).lower()
            else:
                unit_pattern = r"(?:c/|com)\s*(\d+(?:/\d+)?)(?:\s*(?:" + "|".join(cls.UNIT) + r"))?"  
                unit_match = re.search(unit_pattern, name, re.IGNORECASE)
                units = []
                if unit_match:
                    units = [int(u) for u in unit_match.group(1).split("/") if u.isdigit()]
                else:
                    unit_pattern = r"(\d+(?:/\d+)?)(?:\s*(?:" + "|".join(cls.UNIT) + r"))(?!\s*\w)"
                    unit_match = re.search(unit_pattern, name, re.IGNORECASE)
                    if unit_match:
                        units = [int(u) for u in unit_match.group(1).split("/") if u.isdigit()]
                    else:
                        unit_pattern = "|".join(cls.UNIT)
                        unit_match = re.search(unit_pattern, name, re.IGNORECASE)
                        if unit_match:
                            units = [1]

                if units:
                    weight = units[-1]
                    measure = "un"
                else:
                    weight = 0
                    measure = ""

        if measure == "kg" or measure == "quilo" or measure == "quilograma":
            weight *= 1000
            measure = "g"
        elif measure == "l" or measure == "lt" or measure == "litro":
            weight *= 1000
            measure = "ml"

        return pd.Series([measure, int(weight)])

    @classmethod
    def _normalize_name_and_brand(cls, name, brand):
        def remove_duplicate_words(text):
            words = text.split()
            seen = set()
            result = []
            for word in reversed(words):
                word_lower = word.lower()
                if word_lower not in seen:
                    seen.add(word_lower)
                    result.insert(0, word)
            return " ".join(result)

        def clean_word(word):
            return re.sub(r'\W+', '', word).lower()

        def match_brand_name_in_name(name, brand):
            name_words = name.split()
            brand_words = brand.split("-")

            i = 0
            n = len(name_words)
            matched_indices = []

            while i < n:
                name_word_clean = clean_word(name_words[i])
                brand_first_word_clean = clean_word(brand_words[0])

                if brand_first_word_clean.startswith(name_word_clean):
                    matched_indices.append(i)
                    break
                i += 1

            if matched_indices:
                i += 1
                brand_idx = 1

                while i < n and brand_idx < len(brand_words):
                    name_word_clean = clean_word(name_words[i])
                    brand_word_clean = clean_word(brand_words[brand_idx])

                    if brand_word_clean.startswith(name_word_clean):
                        brand_idx += 1

                    matched_indices.append(i)
                    i += 1

                if brand_idx == len(brand_words):
                    start = matched_indices[0]
                    end = matched_indices[-1]
                    return " ".join(name_words[start:end+1])

            return ""

        def fuzzy_substring_match(name: str, brand: str, threshold: int):
            name = name.lower()
            brand = brand.lower()
            length = len(brand)

            best_substr = None
            best_score = 0

            for window in range(max(1, length - 2), length + 3):
                for i in range(len(name) - window + 1):
                    substr = name[i : i + window]
                    score = fuzz.ratio(substr, brand)
                    if score > best_score:
                        best_score = score
                        best_substr = substr

            if best_score >= threshold:
                return best_substr.title()
            return ""

        brand_name = match_brand_name_in_name(name, brand)
        if not brand_name:
            brand_name = fuzzy_substring_match(name, brand, threshold=80)

        part_before = name.strip()
        part_after = ""
        if brand_name:
            pattern = re.escape(brand_name).replace(r'\ ', r'\s+')
            match = re.search(pattern, name, flags=re.IGNORECASE)
            if match:
                part_before = name[:match.start()].strip()
                part_after = name[match.end():].strip()

        part_before = re.sub(r'\s+', ' ', part_before)
        part_after = re.sub(r'\s+', ' ', part_after)

        full_name = f"{part_before} {brand_name} {part_after}".strip()
        name = remove_duplicate_words(full_name)

        name_words = name.split()
        brand_words_set = set(clean_word(word) for word in brand_name.split())
        name_without_brand = " ".join([
            word for word in name_words if clean_word(word) not in brand_words_set
        ])

        return name, name_without_brand, brand_name
