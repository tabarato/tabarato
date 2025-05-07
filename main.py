import argparse
from concurrent.futures import ThreadPoolExecutor
from tabarato.extract.bistek import BistekExtractor
from tabarato.transform.bistek import BistekTransformer
from tabarato.extract.angeloni import AngeloniExtractor
from tabarato.transform.angeloni import AngeloniTransformer
from tabarato.extract.giassi import GiassiExtractor
from tabarato.transform.giassi import GiassiTransformer
from tabarato.clustering import Clustering
from tabarato.postgres_loader import PostgresLoader
from tabarato.postgres_upserter import PostgresUpserter
from tabarato.elasticsearch_loader import ElasticsearchLoader

def extract_and_load(store):
    extractors = {
        "angeloni": AngeloniExtractor,
        "bistek": BistekExtractor,
        "giassi": GiassiExtractor
    }
    df = extractors[store].extract()
    extractors[store].load(df)

def transform_and_load(store):
    transformers = {
        "angeloni": AngeloniTransformer,
        "bistek": BistekTransformer,
        "giassi": GiassiTransformer
    }
    df = transformers[store].transform()
    transformers[store].load(df)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--step",
        dest="step",
        default=0,
        help="Step on the pipeline to run: 0 = All, 1 = Extract; 2 = Tranform; 3 = Clustering; 4 = Postgres Loader; 5 = Postgres Upserter; 6 = Elasticsearch Loader",
    )
    parser.add_argument(
        "--store",
        dest="store",
        default=None,
        help="Store to process",
    )
    args = parser.parse_args()
    step = int(args.step)
    store = args.store

    all_stores = ["angeloni", "bistek", "giassi"]
    stores_to_process = [store] if store else all_stores

    with ThreadPoolExecutor(max_workers=len(stores_to_process)) as executor:
        if step == 1 or step == 0:
            print("Start extraction")
            list(executor.map(extract_and_load, stores_to_process))

        if step == 2 or step == 0:
            print("Start tranformation")
            list(executor.map(transform_and_load, stores_to_process))

    if step == 3 or step == 0:
        print("Start clusterization")
        if store == "angeloni" or store == None:
            df = Clustering.process("angeloni")
            Clustering.load(df)
 
        if store == "bistek" or store == None:
            df = Clustering.process("bistek")
            Clustering.load(df)
 
        if store == "giassi" or store == None:
            df = Clustering.process("giassi")
            Clustering.load(df)

    if step == 4 or step == 0:
        print("Start loading")
        df = PostgresLoader.process(store if store else "giassi")
        PostgresLoader.load(df)

    if step == 5 or step == 0:
        print("Start upserting")
        df = PostgresUpserter.process(store)
        PostgresUpserter.load(df)

    if step == 6 or step == 0:
        print("Start loading into ES")
        df = ElasticsearchLoader.process()
        ElasticsearchLoader.load(df)
