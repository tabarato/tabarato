from .loader import Loader
import os
import pandas as pd
import psycopg2
import dotenv
from psycopg2.extras import execute_values
from sentence_transformers import SentenceTransformer

dotenv.load_dotenv()

class PostgresLoader:
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_DB = os.getenv("POSTGRES_DB")

    @classmethod
    def process(cls) -> pd.DataFrame:
        return Loader.read("gold", "products")

    @classmethod
    def load(cls, df: pd.DataFrame):
        # df = ti.xcom_pull(task_ids = "process_task")

        conn = psycopg2.connect(
            dbname=cls.POSTGRES_DB,
            user=cls.POSTGRES_USER,
            password=cls.POSTGRES_PASSWORD,
            host="localhost",
            port="5432"
        )
        cursor = conn.cursor()

        unique_brands = df["brand"].unique()
        cursor.executemany("""
            INSERT INTO brands (name)
            VALUES (%s)
            ON CONFLICT (name) DO NOTHING
        """, [(b,) for b in unique_brands])

        cursor.execute("SELECT id, name FROM brands WHERE name = ANY(%s)", (list(unique_brands),))
        brand_map = {name: bid for bid, name in cursor.fetchall()}
        
        df["id_brand"] = df["brand"].map(brand_map)

        product_family = df[["id_brand", "clustered_name"]].drop_duplicates(subset=["clustered_name"])
         
        # Generating embeddings for clustered names
        sentence_model = SentenceTransformer("all-mpnet-base-v2", device="cuda")
        product_family["embedded_name"] = product_family["clustered_name"].apply(lambda x: sentence_model.encode(x, normalize_embeddings=True).tolist())

        
        product_family_cols = ','.join(product_family.columns)
        product_family_values = [tuple(x) for x in  product_family.to_numpy()]
        product_family_query = f"INSERT INTO product_family ({product_family_cols}) VALUES %s"

        execute_values(cursor, product_family_query, product_family_values)

        # cursor.executemany("""
        #     INSERT INTO product_family (id_brand, name, embedded_name)
        #     VALUES (%s, %s, %s)
        # """, product_family)

        # df_merged_query = "INSERT INTO base_products (id_brand, name, embedded_name) VALUES %s"

        # execute_values(cursor, df_merged_query, product_family)

        # product_entries = []
        # for _, row in df.iterrows():
        #     for variation in row["variations"]:
        #         product_entries.append((
        #             row["clustered_name"],
        #             brand_map[row["brand"]],
        #             variation["weight"],
        #             variation["measure"]
        #         ))

        # cursor.executemany("""
        #     INSERT INTO products (clustered_name, id_brand, weight, measure)
        #     VALUES (%s, %s, %s, %s)
        # """, product_entries)

        # cursor.execute("""
        #     SELECT id, clustered_name, weight, measure 
        #     FROM products
        # """)
        # product_map = {(name, weight, measure): pid for pid, name, weight, measure in cursor.fetchall()}

        # store_product_rows = []
        # for _, row in df.iterrows():
        #     for variation in row["variations"]:
        #         for store in variation["sellers"]:
        #             store_product_rows.append((
        #                 store["store_id"],
        #                 product_map[(row["clustered_name"], variation["weight"], variation["measure"])],
        #                 variation["name"],
        #                 store["price"],
        #                 store["old_price"],
        #                 store["link"],
        #                 store["cart_link"],
        #                 variation["image_url"],
        #                 variation["embedded_name"]
        #             ))

        # cursor.executemany("""
        #     INSERT INTO store_products (
        #         id_store, id_product, name,
        #         price, old_price, link, cart_link, image_url, embedded_name
        #     )
        #     VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        # """, store_product_rows)

        conn.commit()
