from etl.bistek import BistekETL
from etl.angeloni import AngeloniETL


if __name__ == "__main__":
    processes = [
        BistekETL(),
        AngeloniETL()
    ]

    for process in processes:
        data = process.extract()
        transformed_data = process.transform(data)
        process.load(transformed_data)