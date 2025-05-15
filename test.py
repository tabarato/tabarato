import duckdb
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import dotenv
import os

dotenv.load_dotenv()

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
df = duckdb.query("SELECT name, embedded_name FROM 'data\\gold\\angeloni.parquet' where brand = 'tirol' and name = 'Leite Tirol Semidesnatado'").to_df()

conn = psycopg2.connect(
    dbname=POSTGRES_DB,
    user=POSTGRES_USER,
    password=POSTGRES_PASSWORD,
    host="localhost",
    port="5432"
)
cur = conn.cursor()

def _to_vector(embedding):
    return "[" + ",".join(f"{x:.6f}" for x in embedding) + "]"

values = [(row['name'], row['embedded_name']) for _, row in df.iterrows()]

for tp in values:
    name = tp[0]
    value = tp[1]
    print("=================")
    print("Obtendo similar com", name)
    print("Cosine")
    cur.execute(
        """
        SELECT id, name, 1 - (embedded_name <=> %s::vector) AS similarity
        FROM product_family
        where id_brand = (select id from brand where name = 'tirol')
        ORDER BY embedded_name <=> %s::vector
        LIMIT 3
        """,
        (_to_vector(value), _to_vector(value))
    )
    results = cur.fetchall()
    for result in results:
        print(result[1], result[2])
    print("Inner product")
    cur.execute(
        """
        SELECT id, name, -1 * (embedded_name <#> %s::vector) AS similarity
        FROM product_family
        where id_brand = (select id from brand where name = 'tirol')
        ORDER BY embedded_name <#> %s::vector
        LIMIT 3
        """,
        (_to_vector(value), _to_vector(value))
    )
    results = cur.fetchall()
    for result in results:
        print(result[1], result[2])
