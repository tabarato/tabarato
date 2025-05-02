from .loader import Loader
import os
import pandas as pd
import psycopg2
import dotenv
from psycopg2.extras import execute_values


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
        
        brand_map = cls._insert_brands(df, cursor)
        df["id_brand"] = df["brand"].map(brand_map)
        
        family_map = cls._insert_product_families(df, cursor)

        product_map = cls._insert_products(df, cursor, family_map)

        cls._insert_product_stores(df, cursor, product_map)

        conn.commit()

    @classmethod
    def _insert_brands(cls, df, cursor):
        unique_brands = df["brand"].unique()
        cursor.executemany("""
            INSERT INTO brand (name)
            VALUES (%s)
            ON CONFLICT (name) DO NOTHING
        """, [(b,) for b in unique_brands])

        cursor.execute("SELECT id, name FROM brand")
        return {name: bid for bid, name in cursor.fetchall()}

    @classmethod
    def _insert_product_families(cls, df, cursor):
        product_family = df[["id_brand", "name", "embedded_name"]].drop_duplicates(subset=["name"])

        product_family_cols = ','.join(product_family.columns)
        product_family_values = [
            (
                row["id_brand"],
                row["name"],
                cls._to_vector(row["embedded_name"]),
            )
            for _, row in product_family.iterrows()
        ]
        product_family_query = f"INSERT INTO product_family ({product_family_cols}) VALUES %s"

        execute_values(cursor, product_family_query, product_family_values)

        cursor.execute("SELECT id, name FROM product_family")
        return {name: pid for pid, name in cursor.fetchall()}

    @classmethod
    def _insert_products(cls, df, cursor, family_map):
        product_rows = []
        for _, row in df.iterrows():
            name = row["name"]
            family_id = family_map.get(name)
            if not family_id:
                print(f"[WARN] Product sem Product Family: {name}")
                continue

            for variation in row["variations"]:
                product_rows.append((
                    family_id,
                    variation["name"],
                    cls._to_vector(variation["embedded_name"]),
                    variation["weight"],
                    variation["measure"]
                ))
        
        execute_values(
            cursor,
            """
            INSERT INTO product (id_product_family, name, embedded_name, weight, measure)
            VALUES %s
            """,
            product_rows
        )

        cursor.execute("SELECT id, name, weight, measure FROM product")
        return {(name, weight, measure): pid for pid, name, weight, measure in cursor.fetchall()}

    @classmethod
    def _insert_product_stores(cls, df, cursor, product_map):
        store_product_rows = []
        for _, row in df.iterrows():
            for variation in row["variations"]:
                name = variation["name"]
                weight = variation["weight"]
                measure = variation["measure"]
                pid = product_map.get((name, weight, measure))
                if not pid:
                    print(f"[WARN] Store Product sem product: {name}, {weight}, {measure}")
                    continue

                for seller in variation["sellers"]:
                    store_product_rows.append((
                        seller["store_id"],
                        pid,
                        name,
                        seller["price"],
                        seller["old_price"],
                        seller["link"],
                        seller["cart_link"],
                        variation["image_url"],
                        seller["ref_id"]
                    ))

        execute_values(
            cursor,
            """
            INSERT INTO store_product (
                id_store, id_product, name,
                price, old_price, link, cart_link, image_url, ref_id
            ) VALUES %s
            ON CONFLICT (id_store, id_product) DO NOTHING
            """,
            store_product_rows
        )

    @classmethod
    def _to_vector(cls, embedding):
        return "[" + ",".join(f"{x:.6f}" for x in embedding) + "]"