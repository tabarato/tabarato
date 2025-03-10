# How to initialize the project:

Create a `.env` file at the root directory with the following values:

```
AIRFLOW_UID=1000
AIRFLOW_PROJ_DIR=./tabarato/data
BISTEK_BASE_URL="https://www.bistek.com.br"
BISTEK_PRODUCT_DETAILS_URL="https://www.bistek.com.br/api/catalog_system/pub/products/search/?fq=productId:{id}"
```

With the environment configured, run the following commands:

`docker-compose up airflow-init`

`docker-compose up`
