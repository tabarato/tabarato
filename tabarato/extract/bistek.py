from .extractor import Extractor
import os
import pandas as pd
import aiohttp
import asyncio
import dotenv

dotenv.load_dotenv()


class BistekExtractor(Extractor):
    CATEGORIES_URL = os.getenv("BISTEK_CATEGORIES_URL")
    PRODUCTS_FROM_CATEGORY_URL = os.getenv("BISTEK_PRODUCTS_FROM_CATEGORY_URL")

    @classmethod
    def slug(cls) -> str:
        return "bistek"

    @classmethod
    def extract(cls) -> pd.DataFrame:
        async def scrap():
            try:
                async with aiohttp.ClientSession() as session:
                    categories = await cls._get_categories(session=session)

                    semaphore = asyncio.Semaphore(4)

                    async def fetch_category(path: str):
                        async with semaphore:
                            return await cls._get_products(session=session, category=path)

                    tasks = [asyncio.create_task(fetch_category(category)) for category in categories]

                    results = await asyncio.gather(*tasks, return_exceptions=False)

                    products = [item for sublist in results for item in sublist]

                    df = pd.DataFrame(products)

                    df.drop(["clusterHighlights", "searchableClusters"], axis=1, inplace=True)

                    return df
            except Exception as e:
                raise e

        return asyncio.run(scrap())

    @classmethod
    async def _get_categories(cls, session: aiohttp.ClientSession):
        paths = []

        async with session.get(cls.CATEGORIES_URL) as resp:
            data = await resp.json(content_type=None)

        def append_categories(node: dict, prefix: str) -> None:
            current = f"{prefix}/{node['id']}"
            children = node.get("children", [])
            if children:
                for child in children:
                    append_categories(child, current)
            else:
                paths.append(current + "/")

        for category in data:
            append_categories(category, "")

        return paths

    @classmethod
    async def _get_products(cls, session: aiohttp.ClientSession, category: int, _from: int = 0, _to: int = 10, products: list = []) -> list:
        url = cls.PRODUCTS_FROM_CATEGORY_URL.format(
            category_id=category, _from=_from, _to=_to
        )

        async with session.get(url) as response:
            try:
                data = await response.json(content_type=None)
                if not data or len(data) == 0:
                    return products

                return await cls._get_products(session=session, category=category, _from=_from + 10, _to=_to + 10, products=products + data)
            except Exception as e:
                print(url)
                print(f"Error: {e}")
                return products
