import math
import re
from unidecode import unidecode
import pandas
from core.utils.string_utils import strip_all

SYNONYMS = {
    "beb.": "bebida",
    "sem": "zero",
    "z.": "zero",
    "zr.": "zero",
    "lac.": "lactose",
    "cho.": "chocolate",
    "choc.": "chocolate",
    "lar.": "laranjinha",
    "laran.": "laranjinha",
    "frambo.": "framboesa",
    "mor.": "morango",
    "cappuc.": "cappuccino",
    "baun.": "baunilha",
    "liq.": "liquido",
    "conc.": "concentrado"
}

def transform_product_name(row):
    product_name = row["name"].lower()

    measurement_pattern = r'\b\d+(?:[.,]\d+)?\s*(?:lt|g|kg|ml|l|litro|litros|grama|gramas|quilo|quilos|quilograma|quilogramas)\b\.?\b'

    product_name = re.sub(measurement_pattern, "", product_name, flags=re.IGNORECASE)

    product_name = re.sub(r"(?<!\d)\.(?!\d)", ". ", product_name)

    product_name = strip_all(product_name)

    words = dict.fromkeys(product_name.split())

    # TODO: lemmatization or stemming
    normalized_words = [SYNONYMS.get(word, word) for word in words]

    product_name = " ".join(normalized_words)

    product_name = unidecode(product_name)

    return product_name.title()

def transform_product_brand(row):
    brand = row["brand"]

    brand = brand.replace("'", " ")
    brand = unidecode(brand)
    brand = strip_all(brand)
    brand = brand.replace(" ", "-")

    return brand.lower()

def transform_details(row):
    product_title = row["name"]

    details = []
    details_pattern = r'(?<!^)\b(\d+(?:[.,]\d+)?)?\s*(lata|vd|un|pct|cx|fd|pet|pacote|garrafa|frasco|saco|tablete|barra|cartela|fardo|balde|galão|tubo|ampola|lt|g|kg|ml|l|litro|litros|grama|gramas|quilo|quilos|quilograma|quilogramas)\b\.?\b'
    details_matches = re.findall(details_pattern, product_title, re.IGNORECASE)
    if details_matches:
        for match in details_matches:
            detail = strip_all(" ".join(match))
            product_title = product_title.replace(detail, "")
            details.append(detail)

        product_title = strip_all(product_title)

    return pandas.Series([product_title, details])

def transform_measurement(row, weight_col, measure_col):
    raw_weight = row[weight_col]
    raw_measure = row[measure_col]

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

    return pandas.Series([measure, int(weight)])

def tokenize(row):
    brand = row["brand"]
    title = re.sub(f"\\b{re.escape(brand)}\\b", "", row["title"], flags=re.IGNORECASE)
    title = strip_all(title)
    words = re.findall(r"\b[a-zA-ZÀ-ÿ0-9]+\b", title.lower())
    return "-".join(sorted(words))