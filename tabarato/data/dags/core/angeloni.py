from core.etl import StoreETL
from core.utils.dataframe_utils import normalize_measurement, normalize_product_name
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

class AngeloniETL(StoreETL):
    main_page_url = os.getenv("ANGELONI_BASE_URL")
    product_details_url = os.getenv("ANGELONI_PRODUCT_DETAILS_URL")

    @classmethod
    def slug(cls) -> str:
        return "angeloni"

    @classmethod
    def extract(cls) -> pd.DataFrame:
        """Collect data from Angeloni Online Market"""

        async def scrap():
            try:
                async with aiohttp.ClientSession() as session:
                    categories_url = await cls._process_category(session=session)

                    categories_url_pages_tasks = [cls._process_category_pagination(session=session, url=url) for url in categories_url]

                    categories_url_pages = await asyncio.gather(*categories_url_pages_tasks)
                    categories_url_pages = list(itertools.chain.from_iterable(categories_url_pages))
                    print(categories_url_pages)
                    products_url_tasks = [cls._collect_product_id(session=session, url=url) for url in categories_url_pages]
                    products_url = await asyncio.gather(*products_url_tasks)
                    products_url = list(set(itertools.chain.from_iterable(filter(None, products_url))))

                    products_data_tasks = [cls._collect_product_data(session=session, url=url) for url in products_url]
                    products_data = list(await asyncio.gather(*products_data_tasks))
                    products_data = [i for i in products_data if i is not None]

                    df = pd.DataFrame(products_data)

                    df.drop(["clusterHighlights", "searchableClusters"], axis=1, inplace=True)

                    return df
            except Exception as e:
                raise e

        return asyncio.run(scrap())
        
        
    @classmethod
    def transform(cls, ti) -> pd.DataFrame:
        df = ti.xcom_pull(task_ids = "extract_task")

        df.rename(columns={"productName": "name", "productId": "refId"}, inplace=True)
        df["name"] = df["name"].str.title()
        df[["measure", "weight"]] = df.apply(lambda row: normalize_measurement(row, "Quantidade da embalagem", "Unidade de medida"), axis=1)
        df["title"] = df.apply(normalize_product_name, axis=1)
        df["brand"] = df["brand"].str.lower()

        df[["cartLink", "price", "oldPrice"]] = df.apply(cls._extract_price_info, axis=1)

        df.drop(["brandId", "brandImageUrl",
                "productReference", "productReferenceCode", "categoryId", 
                "metaTagDescription", "releaseDate", "productClusters",
                "categories", "categoriesIds",
                "Quantidade da embalagem", "Unidade de medida",
                "allSpecifications", "allSpecificationsGroups", "description", 
                "items", "linkText", "productTitle"], axis=1, inplace=True)
        
        return df
        
    @classmethod
    async def _process_category(cls, session: aiohttp.ClientSession):
        """Processes the URLs of the categories on the home page"""
        async with session.get(cls.main_page_url) as response:
            config = json.loads(re.findall(r'\n\s+__RUNTIME__ = (.+)\s+', await response.text())[0])
            categories = config["extensions"]["store.home\u002Fflex-layout.row#home-wrapper\u002Fflex-layout.col#main-menu\u002Fmain-menu#new"]["props"]["items"]
            categories_text = json.dumps(categories)
            href_pattern = re.compile(r'"href":\s*"([^"]+?)"')
            hrefs = href_pattern.findall(categories_text)
            hrefs = [codecs.decode(href, 'unicode_escape') for href in hrefs]
            
            hrefs = [(cls.main_page_url + href) for href in hrefs if len(href.split("/")) == 3]

            return hrefs
    
    @classmethod
    async def _process_category_pagination(cls, session: aiohttp.ClientSession, url: str):
        async with session.get(url) as response:
            soup = BeautifulSoup(await response.text(), 'html.parser')
            show_more = soup.find_all("div", class_="vtex-search-result-3-x-buttonShowMore vtex-search-result-3-x-buttonShowMore--result-content--fetchmore")
            if not show_more:
                return [url]

            next_href = show_more[-1].find("a").get("href")
            return await cls._process_category_pagination(session, url + next_href)

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
