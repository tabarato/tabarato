## How to initialize the project:

Create a `.env` file at the root directory with the following values:

```
BISTEK_BASE_URL="https://www.bistek.com.br"
BISTEK_PRODUCT_DETAILS_URL="https://www.bistek.com.br/api/catalog_system/pub/products/search/?fq=productId:{id}"
ANGELONI_BASE_URL="https://www.angeloni.com.br/super"
ANGELONI_PRODUCT_DETAILS_URL="https://www.angeloni.com.br/super/api/catalog_system/pub/products/search/?fq=productId:{id}"
ELASTICSEARCH_URL="http://localhost:9200"
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="postgres123"
POSTGRES_DB="tabarato"
DB_ANON_ROLE="anon"
DB_SCHEMA="public"
```

With the environment configured, run the following commands:

`docker-compose up`

## Routes

* http://localhost:3000 - PostgREST API. 


<!-- AIRFLOW_UID="1000"
AIRFLOW_PROJ_DIR="./src/data"
AIRFLOW_OUTPUT_DIR="./data"
MONGODB_CONNECTION="mongodb://airflow:airflow@mongodb:27017/"
MONGODB_DATABASE="tabarato"
`docker-compose up airflow-init` -->