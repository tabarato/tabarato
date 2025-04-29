## How to initialize the project:

Create a `.env` file at the root directory with the following values:

```
BISTEK_PRODUCTS_FROM_CATEGORY_URL="https://www.bistek.com.br/api/catalog_system/pub/products/search/?fq=C:{category_id}&_from={_from}&_to={_to}"
BISTEK_CATEGORIES_URL="https://www.bistek.com.br/api/catalog_system/pub/category/tree/3/"
ANGELONI_PRODUCTS_FROM_CATEGORY_URL="https://www.angeloni.com.br/super/api/catalog_system/pub/products/search/?fq=C:{category_id}&_from={_from}&_to={_to}"
ANGELONI_CATEGORIES_URL="https://www.angeloni.com.br/super/api/catalog_system/pub/category/tree/3/"
GIASSI_PRODUCTS_FROM_CATEGORY_URL="https://www.giassi.com.br/api/catalog_system/pub/products/search/?fq=C:{category_id}&_from={_from}&_to={_to}"
GIASSI_CATEGORIES_URL="https://www.giassi.com.br/api/catalog_system/pub/category/tree/3/"
ELASTICSEARCH_URL="http://localhost:9200"
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=tabarato
DB_ANON_ROLE=anon
DB_SCHEMA=public
```

With the environment configured, run the following command:

```
docker-compose up -d --build
```

To remove all data, run the following command:

```
docker-compose down --volumes
```

The Python environment should be configured with the following commands:

`
python -m venv env
.\env\Scripts\activate
pip install -r .\requirements.txt
`

The ETL pipeline can be run with the following commands:

- `python .\main.py --step {0} --store {1}`:
  - step:
    - 0 (default): run all the pipeline;
    - 1: extract data;
    - 2: transform data;
    - 3: train the model;
    - 4: execute clustering;
    - 5: load data into PostgreSQL;
    - 6: load data into Elasticsearch.
  - store: the id of the store to execute, executes for all stores if nothing is passed
- You can only run steps 5 and 6 to test the searching results;

The frontend can be run with the following commands:

`
npx expo start
`

## Routes

* http://localhost:3000 - PostgREST API.

<!-- AIRFLOW_UID="1000"
AIRFLOW_PROJ_DIR="./src/data"
AIRFLOW_OUTPUT_DIR="./data"
MONGODB_CONNECTION="mongodb://airflow:airflow@mongodb:27017/"
MONGODB_DATABASE="tabarato"
`docker-compose up airflow-init` -->
