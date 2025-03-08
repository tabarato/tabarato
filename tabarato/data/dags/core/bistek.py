from core.etl import StoreETL
from core.utils.dataframe_utils import normalize_measurement, normalize_product_name
import hrequests
import os
import re
import itertools
import time
import json
import random
import pandas as pd
from dotenv import load_dotenv
from pandas import DataFrame

load_dotenv()

class BistekETL(StoreETL):
    products_url = []
    main_page_url = os.getenv("BISTEK_MAIN_PAGE_URL")
    CATALOG_URL = "https://www.bistek.com.br/exclusivo-site?order=OrderByTopSaleDESC"
    PRODUCT_API_URL = "https://www.bistek.com.br/api/catalog_system/pub/products/search/?fq=productId:{}"
    PAGE_CATALOG_URL = "https://www.bistek.com.br/exclusivo-site?order=OrderByTopSaleDESC&page={0}"

    @classmethod
    def _process_category(cls):
        """Processes the URLs of the categories on the home page"""
        pass
    
    @classmethod
    def _process_category_pagination(cls):
        """Processes the pagination URLs of the category being explored"""
        pass

    @classmethod
    def _collect_product_id(cls):
        """Collects the IDs of the products on the category page being explored."""
        pass
    
    @classmethod
    def _collect_product_data(cls):
        """Collect data from the product in JSON format."""
        pass

    @classmethod
    def get_catalog_pages(cls, session: hrequests.Session):
        response = session.get(cls.CATALOG_URL)    
        pfo = response.html.find("ul", class_="bistek-custom-apps-0-x-pagination bistek-custom-apps-0-x-pagination--start")
        # pages = pfo.find_all("li", class_="bistek-custom-apps-0-x-paginationItem bistek-custom-apps-0-x-paginationItem--page")
        page_links = pfo.absolute_links

        page_pattern = re.compile(r'page=(\d+)')
        
        # Extraindo os números das páginas e convertendo para inteiros
        page_numbers = [int(match.group(1)) for page in page_links if (match := page_pattern.search(page))]
        max_page = max(page_numbers) if page_numbers else None
        return max_page

    @classmethod
    def get_objects_id(cls, session: hrequests.Session, url):
        req_object = session.get(url)
        json_element = req_object.html.find_all('script', type='application/ld+json')[-1]
        json_obj = json.loads(json_element.text)
        
        url_ids = [cls.PRODUCT_API_URL.format(product['item']['sku']) for product in json_obj['itemListElement']]
        return url_ids

    @classmethod
    def get_objects_json_data(cls, session: hrequests.Session, url):
        req_object = session.get(url)
        print("URL: ", url, " Status: ", req_object.status_code)
        return req_object.json()[0]

    @classmethod
    def slug(cls) -> str:
        return "bistek"

    @classmethod
    def extract(cls) -> DataFrame:
        """Collect data from Bistek Online Market"""
        # try:
        #     with hrequests.Session() as session:
        #         req_object = session.get(cls.main_page_url)
        #         print("URL: ", cls.main_page_url, " Status: ", req_object.status_code)
        #         return req_object.json()[0]
        # except Exception as e:
        #     raise e

        with hrequests.Session() as session:
            pages = cls.get_catalog_pages(session)
            urls = [cls.PAGE_CATALOG_URL.format(page) for page in range(1, pages+1)]
            url_ids = [cls.get_objects_id(session, url) for url in urls]
            url_ids = list(itertools.chain.from_iterable(url_ids))
            
            collected_data = []
            for url in url_ids:
                json_data = cls.get_objects_json_data(session, url)
                collected_data.append(json_data)
                time.sleep(random.randint(1, 5))
            
            df = pd.DataFrame(collected_data)

            df.drop(["clusterHighlights", "searchableClusters"], axis=1, inplace=True)

            return df

    @classmethod
    def transform(cls, ti) -> DataFrame:
        df = ti.xcom_pull(task_ids = "extract_task")

        df.rename(columns={"productName": "name"}, inplace=True)
        df[["measure", "weight"]] = df.apply(normalize_measurement, axis=1)
        df["weight"] = df["weight"].astype(int)
        df["title"] = df.apply(normalize_product_name, axis=1)

        df.drop(["productId", "brandId", "brandImageUrl",
                "productReference", "productReferenceCode", "categoryId", 
                "metaTagDescription", "releaseDate", "productClusters",
                "categories", "categoriesIds", "link",
                "Peso Produto", "Unidade de Medida", "Especificações", 
                "allSpecifications", "allSpecificationsGroups", "description", 
                "items", "linkText", "productTitle"], axis=1, inplace=True)
        
        return df
