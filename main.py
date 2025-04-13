import argparse
from tabarato.extract.bistek import BistekExtractor
from tabarato.transform.bistek import BistekTransformer
from tabarato.extract.angeloni import AngeloniExtractor
from tabarato.transform.angeloni import AngeloniTransformer
from tabarato.clustering import Clustering


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--step",
        dest="step",
        default=0,
        help="Step on the pipeline to run: 0 = All, 1 = Extract; 2 = Tranform; 3 = Clustering",
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
    
    if step == 2 or step == 0:
        if store == "angeloni" or store == "":
            df = AngeloniTransformer.transform()
            AngeloniExtractor.load(df)
 
        if store == "bistek" or store == "":
            df = BistekTransformer.transform()
            BistekTransformer.load(df)

    if step == 3 or step == 0:
        df = Clustering.process()
        Clustering.load(df)
