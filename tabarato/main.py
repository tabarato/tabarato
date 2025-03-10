from data.dags.core.bistek import BistekETL
import asyncio


if __name__ == "__main__":
    asyncio.run(BistekETL.extract())