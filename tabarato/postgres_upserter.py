from .loader import Loader
import os
import pandas as pd
import psycopg2
import dotenv
from tqdm import tqdm


dotenv.load_dotenv()

class PostgresUpserter:
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_DB = os.getenv("POSTGRES_DB")

    @classmethod
    def process(cls, store) -> pd.DataFrame:
        return Loader.read("gold", store)

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

        cls._insert_similar_products(df, cursor)

        conn.commit()

    @classmethod
    def _insert_similar_products(cls, df, cursor):
        total = len(df)
        print(f"Starting upserting {str(total)} products")

        cursor.execute("SELECT id, name FROM brand")
        brand_map = {name: bid for bid, name in cursor.fetchall()}
        df["id_brand"] = df["brand"].map(brand_map)

        family_product_cache = {}

        new_variations = 0
        new_store_products = 0
        ignored_products = 0

        for _, row in tqdm(df.iterrows(), total=len(df)):
            embedded_vector = row["embedded_name"]
            id_brand = row["id_brand"]

            already_exists = False

            # Verifica se já existe pelo menos um store_product para esse produto
            for variation in row["variations"]:
                for seller in variation["sellers"]:
                    cursor.execute("""
                        SELECT id_product FROM store_product
                        WHERE id_store = %s AND ref_id = %s
                        LIMIT 1
                    """, (seller["store_id"], seller["ref_id"]))
                    result = cursor.fetchone()
                    if result:
                        # Já existe, então atualiza com os novos dados
                        product_id = result[0]
                        cursor.execute("""
                            UPDATE store_product
                            SET price = %s,
                                old_price = %s,
                                name = %s,
                                link = %s,
                                cart_link = %s,
                                image_url = %s
                            WHERE id_store = %s AND ref_id = %s
                        """, (
                            seller["price"], seller["old_price"], variation["name"],
                            seller["link"], seller["cart_link"], variation["image_url"],
                            seller["store_id"], seller["ref_id"]
                        ))
                        already_exists = True

            if already_exists:
                continue  # pula o processamento de similaridade e inserção

            # fluxo normal se ainda não existe store_product
            family_id = cls._match_product_family(cursor, embedded_vector, id_brand)
            if not family_id:
                ignored_products += 1
                continue

            if family_id not in family_product_cache:
                cursor.execute("""
                    SELECT id, weight, measure FROM product
                    WHERE id_product_family = %s
                """, (family_id,))
                family_product_cache[family_id] = {
                    (weight, measure): pid for pid, weight, measure in cursor.fetchall()
                }

            products = family_product_cache[family_id]

            for variation in row["variations"]:
                product = products.get((variation["weight"], variation["measure"]), None)
                if not product:
                    cursor.execute("""
                        INSERT INTO product (id_product_family, name, embedded_name, weight, measure)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        family_id,
                        variation["name"],
                        cls._to_vector(embedded_vector),
                        variation["weight"],
                        variation["measure"]
                    ))
                    product_id = cursor.fetchone()[0]
                    new_variations += 1
                else:
                    product_id = product
                    new_store_products += 1

                for seller in variation["sellers"]:
                    cursor.execute("""
                        INSERT INTO store_product (
                            id_store, id_product, name, price, old_price,
                            link, cart_link, image_url, ref_id
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id_store, id_product) DO UPDATE
                        SET price = EXCLUDED.price;
                    """, (
                        seller["store_id"], product_id, variation["name"],
                        seller["price"], seller["old_price"],
                        seller["link"], seller["cart_link"],
                        variation["image_url"], seller["ref_id"]
                    ))

        print("New products in stores ", str(new_store_products))
        print("New variations in products ", str(new_variations))
        print("Ignored products ", str(ignored_products))

    @classmethod
    def _match_product_family(cls, cursor, embedded_vector, id_brand, similarity_threshold=0.8):
        cursor.execute(
            """
            SELECT id, 1 - (embedded_name <#> %s::vector) AS similarity
            FROM product_family
            WHERE id_brand = %s
            ORDER BY embedded_name <#> %s::vector
            LIMIT 1
            """,
            (cls._to_vector(embedded_vector), id_brand, cls._to_vector(embedded_vector))
        )
        result = cursor.fetchone()
        if result and result[1] >= similarity_threshold:
            return result[0]
        return None

    @classmethod
    def _to_vector(cls, embedding):
        return "[" + ",".join(f"{x:.6f}" for x in embedding) + "]"
