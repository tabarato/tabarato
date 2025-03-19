from core.utils.string_utils import strip_all
from core.loader import Loader
import datetime as dt
import math
import re
import pandas as pd
from abc import ABC, abstractmethod
from unidecode import unidecode

class Transformer(ABC):
    MEASUREMENT = [
        "mililitros",
        "mililitro",
        "ml",
        "litros",
        "litro",
        "lt",
        "l",
        "quilogramas",
        "quilograma",
        "quilos",
        "quilo",
        "kg",
        "gramas",
        "grama",
        "g"
    ]
    PACKAGING = [
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
        "pote"
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
    def transform(cls, ti, df) -> pd.DataFrame:
        df[["measure", "weight"]] = df.apply(cls._transform_measurement, axis=1)
        df["name"] = df.apply(cls._transform_name, axis=1)
        df["brand"] = df.apply(cls._transform_brand, axis=1)
        df[["name", "details"]] = df.apply(cls._transform_details, axis=1)

        return df.filter(items=[
            "name", "brand", "refId",
            "measure", "weight", "link", "cartLink",
            "price", "oldPrice", "description", "details"
        ])

    @classmethod
    @abstractmethod
    def load(cls, ti) -> None:
        df = ti.xcom_pull(task_ids = "transform_task")
        if df.empty:
            return

        df["storeSlug"] = cls.slug()
        df["insertedAt"] = dt.datetime.now(dt.timezone.utc)

        Loader.load(df, layer="silver", name=cls.slug())
    
    @classmethod
    def _transform_name(cls, row: pd.Series) -> str:
        name = row["name"].lower()

        ignore_patterns = [
            r"\b\d+(?:[.,]\d+)?\s*(?:" + "|".join(cls.MEASUREMENT) + r")\b\.?\b",
            r"\b(tradicional|trad\.|trad)\b",
            r"\d+%\w+\.?"
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

        details = {
            "packaging": [],
            "units": []
        }

        packaging_pattern = r"(?<!^)\b(\d+(?:[.,]\d+)?)?\s*(" + "|".join(cls.PACKAGING) + "|" + "|".join(cls.MEASUREMENT) + r")\b\.?\b"
        matches = re.findall(packaging_pattern, name, re.IGNORECASE)

        if matches:
            for match in matches:
                detail = strip_all(" ".join(match))
                name = name.replace(detail, "")
                details["packaging"].append(detail)

        unit_pattern = r"(?:c/|com)\s*(\d+(?:/\d+)?)(?:\s*(?:" + "|".join(cls.UNIT) + r"))?"  
        unit_match = re.search(unit_pattern, name, re.IGNORECASE)
        if unit_match:
            details["units"] = [int(u) for u in unit_match.group(1).split("/") if u.isdigit()]
            name = name.replace(unit_match.group(0), "").strip()
        else:
            unit_pattern = r"(\d+(?:/\d+)?)(?:\s*(?:unidades|unidade|unidadaes|un))?(?!\s*\w)"
            unit_match = re.search(unit_pattern, name, re.IGNORECASE)
            if unit_match:
                details["units"] = [int(u) for u in unit_match.group(1).split("/") if u.isdigit()]
                name = name.replace(unit_match.group(0), "").strip()
            else:
                unit_pattern = "|".join(cls.UNIT)
                unit_match = re.search(unit_pattern, name, re.IGNORECASE)
                if unit_match:
                    details["units"] = [1]
                    name = name.replace(unit_match.group(0), "").strip()

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

        valid_solid_measures = ["g", "kg", "grama", "quilo", "quilograma"]
        valid_liquid_measures = ["ml", "l", "lt", "litro", "mililitro"]

        if not weight or not measure or math.isnan(weight) or (measure not in valid_solid_measures and measure not in valid_liquid_measures):
            product_name = row["name"]
            solid_match = re.search(f"(\d+)\s*({'|'.join(valid_solid_measures)})", product_name, re.IGNORECASE)
            liquid_match = re.search(f"(\d+)\s*({'|'.join(valid_liquid_measures)})", product_name, re.IGNORECASE)

            if solid_match:
                weight = float(solid_match.group(1))
                measure = str(solid_match.group(2)).lower()
            elif liquid_match:
                weight = float(liquid_match.group(1))
                measure = str(liquid_match.group(2)).lower()
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
