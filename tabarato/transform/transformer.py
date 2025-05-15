from tabarato.utils.string_utils import get_words, strip_all
from tabarato.utils.abbreviations import ABBREVIATIONS
from tabarato.loader import Loader
from datetime import datetime, timezone
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
        "cartela",
        "fardo",
        "balde",
        "galao",
        "tubo",
        "ampola",
        "pote",
        "pt",
        "kg",
        "litros",
        "litro",
        "lt",
        "caixa",
        "pack",
        "embalagem",
        "kit",
        "gfa",
        "gf",
        "bj",
        "bandeja",
        "sache",
        "refil",
        "rf",
        "economico",
        "economica",
        "ec",
        "squeeze",
        "sq",
        "tampa",
        "tp",
        "tamanho familia",
        "tradicional",
        r"trad\.",
        "trad",
        "uht",
        "homogeneizado"
    ]
    UNIT = [
        "unidades",
        "unidade",
        "unidadaes",
        "unid",
        r"un\.",
        "un"
    ]
    PROMOTION = [
        "gratis",
        r"\d*% de desconto",
        r"\d*% desconto",
        r"ed\. limitada",
        r"ed\. lim",
        r"ed\. l",
        "super economico",
        r"(?:\b(?:leve|l)(?:\s*(?:\+|mais|\d+))\s*(?:e\s)?)(?:pague|p)(?:\s*(?:\-|menos|\d+))?",
        r"leve pague"       
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
        df[["name", "brand", "measure", "weight"]] = df.apply(cls._transform_row, axis=1, result_type="expand")

        return df.filter(items=[
            "name", "brand", "ref_id",
            "measure", "weight", "link", "cart_link",
            "price", "old_price", "image_url"
        ])

    @classmethod
    @abstractmethod
    def load(cls, df) -> None:
        # df = ti.xcom_pull(task_ids = "transform_task")
        if df.empty:
            return

        df["store_id"] = cls.id()
        df["inserted_at"] = datetime.now(timezone.utc)

        Loader.load(df, layer="silver", name=cls.slug())

    @classmethod
    def _transform_row(cls, row: pd.Series):
        measure, weight = cls._transform_measurement(row)
        brand = cls._transform_brand(row)
        name = cls._transform_name(row)
        name, brand = cls._normalize_name_with_store_brand(name, brand)

        return name, brand, measure, weight

    @classmethod
    def _transform_name(cls, row: pd.Series) -> str:
        name = row["name"].lower()
        name = unidecode(name)

        ignore_patterns = [
            r"\b\d+(?:[.,]\d+)?\s*(?:" + "|".join(cls.MEASUREMENT) + r")\b\.?\s*(?:\bcada\b)?", # peso
            r"(?<!^)(?:c/|com)?\b(\d+(?:[.,]\d+)?)?\s*(?:" + "|".join(cls.DETAILS) + r")\b\.?\b",
            r"\b(?:" + "|".join(cls.PROMOTION) + r")",
            r"(?:c/|com)\s*(?:\d+(?:\/\d+)?)(?:\s*(?:" + "|".join(cls.UNIT) + r")\b)?.*", # com X unidades
            r"(?:\d+(?:\/\d+)?)(?:\s*(?:" + "|".join(cls.UNIT) + r")\b).*", # X unidades
            r"\b(?:" + "|".join(cls.UNIT) + r")\b.*", # Unidades
            r"(?:\+|\.)\s*$"
        ]

        for pattern in ignore_patterns:
            while True:
                new_name = re.sub(pattern, "", name, flags=re.IGNORECASE)
                if new_name == name:
                    break
                name = new_name

        replace_patterns = {
            r"\bp/(?!\s?\d)": "para ", # p/ -> para
            r"\bs/(?!\s?\d)": "sem ", # s/ -> sem
            r"\bc/(?!\s?\d)": "com ", # c/ -> com
            r"\b\s?/\s?(?!\s?\d)": " e ", # X/Y -> X e Y
            r"(?<!\d)\s*\+\s*": " + ",
            r"(?<!\d)\.(?!\d)": ". "
        }

        for pattern, replacement in replace_patterns.items():
            name = re.sub(pattern, replacement, name, flags=re.IGNORECASE)

        for abbr, replacement in ABBREVIATIONS.items():
            clean_abbr = abbr.rstrip('.').lower()
            pattern = re.compile(
                r'(?<!\S)' +
                re.escape(clean_abbr) + 
                r'\.?' +
                r'(?!\S)',
                flags=re.IGNORECASE
            )
            name = pattern.sub(replacement, name)

        name = name.replace("-", " ")
        name = strip_all(name)

        return name.title()

    @classmethod
    def _transform_brand(cls, row: pd.Series) -> str:
        brand = row["brand"]

        brand = unidecode(brand)
        brand = strip_all(brand)
        brand = "-".join(get_words(brand))

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
            solid_match = re.search(fr"(\d+)\s*({'|'.join(cls.SOLID_MEASUREMENT)})", name, re.IGNORECASE)
            liquid_match = re.search(fr"(\d+(?:[.,]\d+)?)\s*({'|'.join(cls.LIQUID_MEASUREMENT)})", name, re.IGNORECASE)
            unit_match = re.search(fr"(\d+)\s*({'|'.join(cls.UNIT)})", name, re.IGNORECASE)

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
    def _normalize_name_with_store_brand(cls, name, brand):
        if brand != cls.slug():
            return name, brand

        pattern = re.escape(brand).replace(r'\ ', r'\s+')
        match = re.search(pattern, name, flags=re.IGNORECASE)
        if match:
            name_without_brand = strip_all(name[:match.start()] + " " + name[match.end():])
        else:
            name_without_brand = name

        return name_without_brand.title(), ""
