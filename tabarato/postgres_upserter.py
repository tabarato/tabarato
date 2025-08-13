from .loader import Loader
from .utils.string_utils import get_words
import os
import pandas as pd
import psycopg2
import dotenv
from tqdm import tqdm
from rapidfuzz.distance import Levenshtein
from rapidfuzz.utils import default_process


dotenv.load_dotenv()

def mixed_similarity(str1: str, str2: str, w_lev=0.6, w_jaccard=0.4):
    if not str1 or not str2:
        return 0

    str1 = default_process(str1)
    str2 = default_process(str2)

    lev_score = 100 - Levenshtein.normalized_distance(str1, str2) * 100

    tokens1 = set(get_words(str1.lower()))
    tokens2 = set(get_words(str2.lower()))
    jaccard_score = jaccard_similarity(tokens1, tokens2) * 100

    final_score = w_lev * lev_score + w_jaccard * jaccard_score
    return final_score

def jaccard_similarity(tokens1, tokens2):
    """Calcula a similaridade de Jaccard entre dois conjuntos"""
    intersection = tokens1 & tokens2
    union = tokens1 | tokens2
    if not union:
        return 0
    return len(intersection) / len(union)

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

        cursor.execute("SELECT id, slug FROM brands")
        brand_map = {slug: bid for bid, slug in cursor.fetchall()}
        df["brand_id"] = df["brand"].map(brand_map)

        family_product_cache = {}

        new_variations = 0
        new_store_products = 0
        ignored_products = 0
        existent_products = 0

        all_brands = cls._get_all_brands(cursor)
        for _, row in tqdm(df.iterrows(), total=len(df)):
            embedded_vector = row["embedded_name"]
            name = row["name"]

            brand_id = cls._match_similar_brand(row["brand"], all_brands)
            if not brand_id:
                ignored_products += 1
                continue

            already_exists = False

            for variation in row["variations"]:
                for seller in variation["sellers"]:
                    cursor.execute("""
                        SELECT product_id FROM store_products
                        WHERE store_id = %s AND ref_id = %s
                        LIMIT 1
                    """, (seller["store_id"], seller["ref_id"]))
                    result = cursor.fetchone()
                    if result:
                        # Já existe, então atualiza com os novos dados
                        product_id = result[0]
                        cursor.execute("""
                            UPDATE store_products
                            SET price = %s,
                                old_price = %s,
                                name = %s,
                                link = %s,
                                cart_link = %s,
                                image_url = %s
                            WHERE store_id = %s AND ref_id = %s
                        """, (
                            seller["price"], seller["old_price"], variation["name"],
                            seller["link"], seller["cart_link"], variation["image_url"],
                            seller["store_id"], seller["ref_id"]
                        ))
                        existent_products += 1
                        already_exists = True

            if already_exists:
                continue

            family_id = cls._match_product_family(cursor, embedded_vector, brand_id, name)
            if not family_id:
                ignored_products += 1
                continue

            if family_id not in family_product_cache:
                cursor.execute("""
                    SELECT id, weight, measure FROM products
                    WHERE product_family_id = %s
                """, (family_id,))
                family_product_cache[family_id] = {
                    (weight, measure): pid for pid, weight, measure in cursor.fetchall()
                }

            products = family_product_cache[family_id]

            for variation in row["variations"]:
                product = products.get((variation["weight"], variation["measure"]), None)
                if not product:
                    cursor.execute("""
                        INSERT INTO products (product_family_id, name, weight, measure)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id
                    """, (
                        family_id,
                        variation["name"],
                        # cls._to_vector(embedded_vector),
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
                        INSERT INTO store_products (
                            store_id, product_id, name, price, old_price,
                            link, cart_link, image_url, ref_id
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (store_id, product_id) DO UPDATE
                        SET price = EXCLUDED.price;
                    """, (
                        seller["store_id"], product_id, variation["name"],
                        seller["price"], seller["old_price"],
                        seller["link"], seller["cart_link"],
                        variation["image_url"], seller["ref_id"]
                    ))

        print("New products in stores ", str(new_store_products))
        print("New variations in products ", str(new_variations))
        print("Existent products ", str(existent_products))
        print("Ignored products ", str(ignored_products))

    @classmethod
    def _get_all_brands(cls, cursor):
        cursor.execute("SELECT id, slug FROM brands")
        return [(bid, name, None) for bid, name in cursor.fetchall()]

    @classmethod
    def _match_similar_brand(cls, brand, all_brand_vectors, threshold=50):
        best_score = 0
        best_id = None

        for bid, bname, _ in all_brand_vectors:
            if brand == bname:
                return bid

        for bid, bname, _ in all_brand_vectors:
            score = mixed_similarity(brand, bname)
            if score > best_score:
                best_score = score
                best_id = bid

        if best_score >= threshold:
            return best_id

        return None

    @classmethod
    def _match_product_family(cls, cursor, embedded_vector, brand_id, name, similarity_threshold=0.9):
        cursor.execute(
            """
            SELECT id, 1 - (embedded_name <=> %s::vector) AS similarity
            FROM product_families
            WHERE brand_id = %s and name like %s
            ORDER BY embedded_name <=> %s::vector
            LIMIT 1
            """,
            (cls._to_vector(embedded_vector), brand_id, f"{get_words(name)[0]}%", cls._to_vector(embedded_vector))
        )
        result = cursor.fetchone()
        if result and result[1] >= similarity_threshold:
            return result[0]
        return None

    @classmethod
    def _to_vector(cls, embedding):
        return "[" + ",".join(f"{x:.6f}" for x in embedding) + "]"
