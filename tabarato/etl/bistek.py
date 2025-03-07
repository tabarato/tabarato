from etl.etl import ETL
from etl.utils.dataframe_utils import normalize_measurement, normalize_product_name
from etl.utils.string_utils import tokenize
import hrequests
import os
import re
import itertools
import time
import json
import random
from dotenv import load_dotenv
from pandas import DataFrame

load_dotenv()

class BistekETL(ETL):
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

    def get_catalog_pages(self, session: hrequests.Session):
        response = session.get(self.CATALOG_URL)    
        pfo = response.html.find("ul", class_="bistek-custom-apps-0-x-pagination bistek-custom-apps-0-x-pagination--start")
        # pages = pfo.find_all("li", class_="bistek-custom-apps-0-x-paginationItem bistek-custom-apps-0-x-paginationItem--page")
        page_links = pfo.absolute_links

        page_pattern = re.compile(r'page=(\d+)')
        
        # Extraindo os números das páginas e convertendo para inteiros
        page_numbers = [int(match.group(1)) for page in page_links if (match := page_pattern.search(page))]
        max_page = max(page_numbers) if page_numbers else None
        return max_page

    def get_objects_id(self, session: hrequests.Session, url):
        req_object = session.get(url)
        json_element = req_object.html.find_all('script', type='application/ld+json')[-1]
        json_obj = json.loads(json_element.text)
        
        url_ids = [self.PRODUCT_API_URL.format(product['item']['sku']) for product in json_obj['itemListElement']]
        return url_ids

    def get_objects_json_data(session: hrequests.Session, url):
        req_object = session.get(url)
        print("URL: ", url, " Status: ", req_object.status_code)
        return req_object.json()[0]

    def extract(self) -> None:
        """Collect data from Bistek Online Market"""
        # try:
        #     with hrequests.Session() as session:
        #         req_object = session.get(cls.main_page_url)
        #         print("URL: ", cls.main_page_url, " Status: ", req_object.status_code)
        #         return req_object.json()[0]
        # except Exception as e:
        #     raise e

        with hrequests.Session() as session:
            pages = self.get_catalog_pages(session)
            urls = [self.PAGE_CATALOG_URL.format(page) for page in range(1, pages+1)]
            url_ids = [self.get_objects_id(session, url) for url in urls]
            url_ids = list(itertools.chain.from_iterable(url_ids))
            
            collected_data = []
            for url in url_ids:
                json_data = self.get_objects_json_data(session, url)
                collected_data.append(json_data)
                time.sleep(random.randint(1, 5))
            
            return collected_data

    def transform(self, data) -> DataFrame:
        df = DataFrame(data)

        brand_mapping = {brand: idx for idx, brand in enumerate(df["brand"].unique())}
        df["brand_encoded"] = df["brand"].map(brand_mapping)

        df[["measure", "weight"]] = df.apply(normalize_measurement, axis=1)

        df["normalized_product_name"] = df.apply(normalize_product_name, axis=1)
        df["tokens"] = df["normalized_product_name"].apply(tokenize)

        df.drop(["productId", "brandId", "brandImageUrl",
                "productReference", "productReferenceCode", "categoryId", 
                "metaTagDescription", "releaseDate", "clusterHighlights",
                "productClusters", "searchableClusters", "categories",
                "categoriesIds", "link", "Peso Produto",
                "Unidade de Medida", "Especificações", "allSpecifications",
                "allSpecificationsGroups", "description", "items",
                "productTitle", "linkText"], axis=1, inplace=True)
        
        return df
