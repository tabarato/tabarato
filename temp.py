from sentence_transformers import SentenceTransformer
import pandas as pd
import json

def set_full_name(file):
    for obj in file:
        for variation in obj["variations"]:
            variation["full_name"] = "{0} {1}{2}".format(
                variation["name"],
                variation["weight"],
                variation["measure"],
            )
    
    with open("reviewed_products.json", "w", encoding="utf-8") as f:
        json.dump(file, f, indent=4, ensure_ascii=False)

def get_name_embeddings(row, model):
    variations = row['variations']
    for variation in variations:
        full_name = variation['full_name']
        embedding = model.encode(full_name)
        variation['embedded_name'] = embedding.tolist()



if __name__ == "__main__":

    model = SentenceTransformer('all-MiniLM-L6-v2')
    df = pd.read_json("reviewed_products.json", encoding="utf-8")
    df.apply(lambda row: get_name_embeddings(row, model), axis=1)
    df.to_parquet("reviewed_products.parquet", index=False)
    # df['variations'] = df['variations'].apply(lambda x: x['embedded_name'])
    
