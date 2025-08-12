import json
import os
import requests
import pandas as pd
import psycopg2
import dotenv

dotenv.load_dotenv()

class ElasticsearchLoader:
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_DB = os.getenv("POSTGRES_DB")
    ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL")

    @classmethod
    def process(cls) -> pd.DataFrame:
        records = cls._get_products()

        products = cls._map_to_elasticsearch(records)

        return products

    @classmethod
    def load(cls, products: list):
        # df = ti.xcom_pull(task_ids = "process_task")

        bulk_request = ""
        for product in products:
            bulk_request += '{"index": {}}\n'
            bulk_request += json.dumps(product) + "\n"

        headers = {"Content-Type": "application/json"}
        response = requests.post(cls.ELASTICSEARCH_URL + "/products/_bulk", data=bulk_request, headers=headers, auth=('elastic', 'elastic'), verify=False)

        if response.status_code != 200:
            print(response.text)
            raise Exception(response.text)

    @classmethod
    def _get_products(cls) -> list:
        conn = psycopg2.connect(
            dbname=cls.POSTGRES_DB,
            user=cls.POSTGRES_USER,
            password=cls.POSTGRES_PASSWORD,
            host="localhost",
            port="5432"
        )
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                sp.id AS store_product_id,
                sp.name,
                sp.price,
                sp.old_price,
                sp.link,
                sp.cart_link,
                sp.image_url,
                s.slug as store_slug,
                p.id AS product_id,
                p.name,
                p.weight,
                p.measure,
                pf.id AS product_family_id,
                pf.name as product_family_name,
                b.slug AS brand
            FROM store_products sp
            JOIN products p ON sp.product_id = p.id
            JOIN product_families pf ON p.product_family_id = pf.id
            JOIN brands b ON pf.brand_id = b.id
            JOIN stores s ON sp.store_id = s.id
        """)
        rows = cursor.fetchall()
        colnames = [desc[0] for desc in cursor.description]
        cursor.close()
        conn.close()

        return [dict(zip(colnames, row)) for row in rows]

    @classmethod
    def _map_to_elasticsearch(cls, records: list) -> list:
        grouped_products = {}

        for record in records:
            key = record["product_family_id"]
            variation_key = record["product_id"]

            if key not in grouped_products:
                grouped_products[key] = {
                    "name": record["product_family_name"],
                    "brand": record["brand"],
                    "variations": {}
                }

            product = grouped_products[key]

            if variation_key not in product["variations"]:
                product["variations"][variation_key] = {
                    "product_id": record["product_id"],
                    "name": record["name"],
                    "weight": int(record["weight"]) if record["weight"] else None,
                    "measure": record["measure"],
                    "image_url": record["image_url"],
                    "prices": [],
                    "stores": set()
                }

            price = float(record["price"]) if record["price"] else None
            if price:
                product["variations"][variation_key]["prices"].append(price)

            store = record["store_slug"]
            stores = product["variations"][variation_key]["stores"]
            if store and store not in stores:
                stores.add(store)

        for product in grouped_products.values():
            variations_list = []
            for variation in product["variations"].values():
                prices = variation.pop("prices")
                variation["min_price"] = min(prices) if prices else None
                variation["max_price"] = max(prices) if prices else None
                variation["stores"] = list(variation["stores"])
                variations_list.append(variation)
            product["variations"] = sorted(variations_list, key=lambda v: v["weight"] or 0)

        return list(grouped_products.values())
