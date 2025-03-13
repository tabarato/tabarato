import math
import re
from unidecode import unidecode
import pandas

def normalize_product_name(row):
    product_name = row["name"]
    weight = row["weight"]
    weight_divided = weight / 1000
    weight_divided_str = str(weight_divided)

    measurement_pattern = r'\b\d+(?:[.,]\d+)?\s*(?:lt|g|kg|ml|l|litro|litros|grama|gramas|quilo|quilos|quilograma|quilogramas)\b\.?\b' #|lata|un|pct|cx|fd|pacote|garrafa|frasco|saco|tablete|barra|cartela|fardo|balde|galão|tubo|ampola

    product_name = re.sub(measurement_pattern, "", product_name, flags=re.IGNORECASE)

    product_name = re.sub(r"\s+", " ", product_name).strip()

    product_name = ' '.join(dict.fromkeys(product_name.split()))

    product_name = unidecode(product_name)

    return product_name

def normalize_measurement(row, weight_col, measure_col):
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
