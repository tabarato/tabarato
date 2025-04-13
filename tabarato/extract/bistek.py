from .extractor import Extractor
import os
import re
import itertools
import json
import pandas as pd
import codecs
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import dotenv

dotenv.load_dotenv()


class BistekExtractor(Extractor):
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

                    return df
            except Exception as e:
                raise e

        return asyncio.run(scrap())

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
