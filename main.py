import argparse
from tabarato.extract.bistek import BistekExtractor
from tabarato.transform.bistek import BistekTransformer
from tabarato.extract.angeloni import AngeloniExtractor
from tabarato.transform.angeloni import AngeloniTransformer
from tabarato.extract.giassi import GiassiExtractor
from tabarato.transform.giassi import GiassiTransformer
from tabarato.clustering import Clustering
from tabarato.postgres_loader import PostgresLoader
from tabarato.elasticsearch_loader import ElasticsearchLoader
from tabarato.model import Model

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--step",
        dest="step",
        default=0,
        help="Step on the pipeline to run: 0 = All, 1 = Extract; 2 = Tranform; 3 = Word2Vec Training; 4 = Clustering; 5 = Postgres Loader; 6 = Elasticsearch Loader",
    )
    parser.add_argument(
        "--store",
        dest="store",
        default="",
        help="Store to process",
    )
    args = parser.parse_args()
    step = int(args.step)
    store = str(args.store)
    print(str(step), "|", store)

    if step == 1 or step == 0:
        if store == "angeloni" or store == "":
            df = AngeloniExtractor.extract()
            AngeloniExtractor.load(df)

        if store == "bistek" or store == "":
            df = BistekExtractor.extract()
            BistekExtractor.load(df)

        if store == "giassi" or store == "":
            df = GiassiExtractor.extract()
            GiassiExtractor.load(df)
    
    if step == 2 or step == 0:
        if store == "angeloni" or store == "":
            df = AngeloniTransformer.transform()
            AngeloniTransformer.load(df)
 
        if store == "bistek" or store == "":
            df = BistekTransformer.transform()
            BistekTransformer.load(df)
 
        if store == "giassi" or store == "":
            df = GiassiTransformer.transform()
            GiassiTransformer.load(df)

    if step == 3 or step == 0:
        Model.train_model()

    if step == 4 or step == 0:
        df = Clustering.process()
        Clustering.load(df)

    if step == 5 or step == 0:
        df = PostgresLoader.process()
        PostgresLoader.load(df)

    # if step == 6 or step == 0:
    #     df = ElasticsearchLoader.process()
    #     ElasticsearchLoader.load(df)
