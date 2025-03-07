import math
import re
import pandas

def normalize_product_name(row):
    product_name = row["productName"]
    brand = row["brand"]
    weight = int(row["weight"])
    measure = row["measure"]

    if weight < 1000:
        measurement_text = str(weight) + measure
    else:
        if measure == "g":
            measure = "KG"
        else:
            measure = "LT"

        measurement_text = str(weight / 1000) + measure

    product_name = re.sub(re.escape(brand), "", product_name, flags=re.IGNORECASE)

    product_name = re.sub(re.escape(measurement_text), "", product_name, flags=re.IGNORECASE)

    product_name = re.sub(r"\s+", " ", product_name).strip()

    return product_name

def normalize_measurement(row):
    raw_weight = row["Peso Produto"]
    raw_measure = row["Unidade de Medida"]
    
    weight = float(raw_weight[0]) if raw_weight and isinstance(raw_weight, list) else float(raw_weight)
    measure = str(raw_measure[0]) if raw_measure and isinstance(raw_measure, list) else str(raw_measure)

    if math.isnan(weight):
        product_name = row["productName"]
        match = re.search(r"(\d+)\s*(ml|g|kg|l|lt)", product_name, re.IGNORECASE)

        if match:
            weight = match.group(1)
            measure = match.group(2)
        else:
            weight = 0
            measure = ""

    if measure.upper() == "KG":
        weight *= 1000
        measure = "g"
    elif measure.upper() == "LT":
        weight *= 1000
        measure = "ml"
    
    return pandas.Series([measure, weight])