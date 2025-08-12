## How to initialize the project:

First you must follow the instructions on where to create the environment variables in the `.env.example` file.
Contact repository administrators to get environment variable values.

With the environment configured, run the following command:

```
docker-compose up -d --build
```

To remove all data, run the following command:

```
docker-compose down --volumes
```

After starting the containers, run the migrations to initialize the database schema and apply any pending updates:

```
dotnet ef database update --project TabaratoApi.Infra --startup-project TabaratoApi
```

The Python environment should be configured with the following commands:

`python -m venv env .\env\Scripts\activate pip install -r .\requirements.txt`

The ETL pipeline can be run with the following commands:

- `python .\main.py --step {0} --store {1}`:
  - step:
    - 0 (default): run all the pipeline;
    - 1: extract data;
    - 2: transform data;
    - 3: execute clustering;
    - 4: load data into PostgreSQL;
    - 5: upsert data into PostgreSQL;
    - 6: load data into Elasticsearch.
  - store: the id of the store to execute, executes for all stores if nothing is passed
- You can only run steps 4, 5 and 6 to test the search results.

The frontend can be run with the following commands:

`npx expo start`

## Routes

* http://localhost:3000 - PostgREST API.

<!-- AIRFLOW_UID="1000"
AIRFLOW_PROJ_DIR="./src/data"
AIRFLOW_OUTPUT_DIR="./data"
MONGODB_CONNECTION="mongodb://airflow:airflow@mongodb:27017/"
MONGODB_DATABASE="tabarato"
`docker-compose up airflow-init` -->
