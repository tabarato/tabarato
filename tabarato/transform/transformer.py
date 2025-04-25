from tabarato.utils.string_utils import strip_all
from tabarato.loader import Loader
import datetime as dt
import math
import re
import pandas as pd
from abc import ABC, abstractmethod
from unidecode import unidecode


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
        "l",
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
        df[["name", "details"]] = df.apply(cls._transform_details, axis=1)
        df[["name_without_brand", "name"]] = df.apply(lambda row: cls._normalize_name_and_brand(row["name"], row["brand"]), axis=1, result_type="expand")

        return df.filter(items=[
            "name", "name_without_brand", "brand", "refId",
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
            r"(?:leve\s(?:\w+|\+)\s)?pague\s(?:\w+|\-)",
            r"l\+p\-",
            r"\b\d+(?:[.,]\d+)?\s*(?:" + "|".join(cls.MEASUREMENT) + r")\b\.?\b",
            r"\b(tradicional|trad\.|trad)\b",
            r"\d+%\w+\.?",
            r"(?:c/|com)\s*(\d+(?:/\d+)?)(?:\s*(?:" + "|".join(cls.UNIT) + r"))?",
            r"(\d+(?:/\d+)?)(?:\s*(?:" + "|".join(cls.UNIT) + r"))(?!\s*\w)",
            "|".join(cls.UNIT)
        ]

        for pattern in ignore_patterns:
            name = re.sub(pattern, "", name, flags=re.IGNORECASE)

        replace_patterns = {
            r"\bp/(?!\s?\d)": "para ",
            r"\bs/(?!\s?\d)": "sem ",
            r"\bc/(?!\s?\d)": "com ",
            r"\b\s?/\s?(?!\s?\d)": " e "
        }

        for pattern, replacement in replace_patterns.items():
            name = re.sub(pattern, replacement, name, flags=re.IGNORECASE)

        words = name.split()
        seen = set()
        deduped_words = [word for word in words if not (word in seen or seen.add(word))]
        name = " ".join(deduped_words)

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
    def _transform_details(cls, row: pd.Series) -> pd.Series:
        name = row["name"]

        details = []

        details_pattern = r"(?<!^)\b(\d+(?:[.,]\d+)?)?\s*(" + "|".join(cls.DETAILS) + r")\b\.?\b"
        matches = re.findall(details_pattern, name, re.IGNORECASE)

        if matches:
            for match in matches:
                detail = strip_all(" ".join(match))
                name = name.replace(detail, "")
                details.append(detail)

        name = strip_all(name)

        return pd.Series([name, details])

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

        name = (part_before + " " + part_after).strip()
        return name, (name + " " + brand_name).strip()

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
