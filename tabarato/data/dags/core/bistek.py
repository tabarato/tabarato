from core.etl import StoreETL
from core.utils.dataframe_utils import transform_measurement, transform_product_name, transform_product_brand, transform_details
import os
import re
import itertools
import json
import pandas as pd
import codecs
import aiohttp
import asyncio
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()

class BistekETL(StoreETL):
    main_page_url = os.getenv("BISTEK_BASE_URL")
    product_details_url = os.getenv("BISTEK_PRODUCT_DETAILS_URL")

    @classmethod
    def slug(cls) -> str:
        return "bistek"

    @classmethod
    def extract(cls) -> pd.DataFrame:
        """Collect data from Bistek Online Market"""

        async def scrap():
            try:
                async with aiohttp.ClientSession() as session:
                    categories_url = await cls._process_category(session=session)

                    categories_url_pages_tasks = [cls._process_category_pagination(session=session, url=url) for url in categories_url]

                    categories_url_pages = await asyncio.gather(*categories_url_pages_tasks)
                    categories_url_pages = list(itertools.chain.from_iterable(categories_url_pages))
                    
                    products_url_tasks = [cls._collect_product_id(session=session, url=url) for url in categories_url_pages]
                    products_url = await asyncio.gather(*products_url_tasks)
                    products_url = list(set(itertools.chain.from_iterable(filter(None, products_url))))
                    
                    products_data_tasks = [cls._collect_product_data(session=session, url=url) for url in products_url]
                    products_data = list(await asyncio.gather(*products_data_tasks))

                    df = pd.DataFrame(products_data)

                    df.drop(["clusterHighlights", "searchableClusters"], axis=1, inplace=True)

                    cls.save(df, "bronze")

                    return df
            except Exception as e:
                raise e

        return asyncio.run(scrap())

    @classmethod
    def transform(cls, ti) -> pd.DataFrame:
        df = ti.xcom_pull(task_ids = "extract_task")

        df.rename(columns={"productName": "name", "productId": "refId"}, inplace=True)
        df[["measure", "weight"]] = df.apply(lambda row: transform_measurement(row, "Peso Produto", "Unidade de Medida"), axis=1)
        df["name"] = df.apply(transform_product_name, axis=1)
        df["brand"] = df.apply(transform_product_brand, axis=1)
        df[["title", "details"]] = df.apply(transform_details, axis=1)
        df[["cartLink", "price", "oldPrice"]] = df.apply(cls._extract_price_info, axis=1)

        df = df.filter(items=[
            "name", "title", "brand", "refId",
            "measure", "weight", "link", "cartLink",
            "price", "oldPrice", "description", "details"
        ])

        return df

    @classmethod
    async def _process_category(cls, session: aiohttp.ClientSession):
        """Processes the URLs of the categories on the home page"""
        async with session.get(cls.main_page_url) as response:
            soup = BeautifulSoup(await response.text(), 'html.parser')
            categories_data = soup.find_all("template")[4]
            script = categories_data.find('script')
            
            href_pattern = re.compile(r'"href":\s*"([^"]+?)"')
            hrefs = href_pattern.findall(script.text)
            hrefs = [codecs.decode(href, 'unicode_escape') for href in hrefs]
            
            hrefs = [(cls.main_page_url + href)for href in hrefs if len(href.split("/")) == 3]

            return hrefs

    @classmethod
    async def _process_category_pagination(cls, session: aiohttp.ClientSession, url: str):
        async with session.get(url) as response:
            soup = BeautifulSoup(await response.text(), 'html.parser')
            pages = soup.find_all("li", class_="bistek-custom-apps-0-x-paginationItem bistek-custom-apps-0-x-paginationItem--page")
            if not pages:
                return [url]
            
            max_page = pages[-1].find("span").find("a").get_text()
            return [url + f"?page={page}" for page in range(1, int(max_page) + 1)]

    @classmethod
    async def _collect_product_id(cls, session: aiohttp.ClientSession, url: str):
        """Collects the IDs of the products on the category page being explored."""
        async with session.get(url) as response:
            try:
                await asyncio.sleep(0.5)
                soup = BeautifulSoup(await response.text(), 'html.parser')
                script = soup.find_all('script', type='application/ld+json')[-1]
                script = json.loads(script.text)

                urls = []
                for product in script['itemListElement']:
                    if not product.get("item", None):
                        continue
                    
                    urls.append(cls.product_details_url.replace("{id}", product['item']['sku']))

                return urls
            except Exception as e:
                print(str(e))
                print("Erro ao coletar id: ", url, " Status: ", response.status)

    @classmethod
    async def _collect_product_data(cls, session: aiohttp.ClientSession, url: str):
        """Collect data from the product in JSON format."""
        async with session.get(url) as response:
            try:
                await asyncio.sleep(0.5)
                product = await response.json()
                return product[0]
            except Exception as e:
                print(str(e))
                print("Erro ao coletar produto: ", url, " Status: ", response.status)

    @classmethod
    def _extract_price_info(cls, row):
        items = row["items"]

        if not items.any():
            return pd.Series({"cartLink": None, "price": None, "oldPrice": None})

        item = items[0]
        if "sellers" in item and item["sellers"]:
            seller = item["sellers"][0]
            commertial_offer = seller.get("commertialOffer", {})

            return pd.Series({
                "cartLink": seller.get("addToCartLink", None),
                "price": commertial_offer.get("Price", None),
                "oldPrice": commertial_offer.get("ListPrice", None)
            })
