import hrequests
import re
import itertools
import time
import datetime
import json
import gzip
import logging
import random

CATALOG_URL = "https://www.bistek.com.br/exclusivo-site?order=OrderByTopSaleDESC"
PRODUCT_API_URL = "https://www.bistek.com.br/api/catalog_system/pub/products/search/?fq=productId:{}"
PAGE_CATALOG_URL = "https://www.bistek.com.br/exclusivo-site?order=OrderByTopSaleDESC&page={0}"




def get_catalog_pages(session: hrequests.Session):
    response = session.get(CATALOG_URL)    
    pfo = response.html.find("ul", class_="bistek-custom-apps-0-x-pagination bistek-custom-apps-0-x-pagination--start")
    # pages = pfo.find_all("li", class_="bistek-custom-apps-0-x-paginationItem bistek-custom-apps-0-x-paginationItem--page")
    page_links = pfo.absolute_links

    page_pattern = re.compile(r'page=(\d+)')
    
    # Extraindo os números das páginas e convertendo para inteiros
    page_numbers = [int(match.group(1)) for page in page_links if (match := page_pattern.search(page))]
    max_page = max(page_numbers) if page_numbers else None
    return max_page

def get_objects_id(session: hrequests.Session, url):
    req_object = session.get(url)
    json_element = req_object.html.find_all('script', type='application/ld+json')[-1]
    json_obj = json.loads(json_element.text)
    
    url_ids = [PRODUCT_API_URL.format(product['item']['sku']) for product in json_obj['itemListElement']]
    return url_ids


def get_objects_json_data(session: hrequests.Session, url):
    req_object = session.get(url)
    print("URL: ", url, " Status: ", req_object.status_code)
    return req_object.json()[0]


if __name__ == "__main__":
    with hrequests.Session() as session:
        pages = get_catalog_pages(session)
        urls = [PAGE_CATALOG_URL.format(page) for page in range(1, pages+1)]
        url_ids = [get_objects_id(session, url) for url in urls]
        url_ids = list(itertools.chain.from_iterable(url_ids))
        
        collected_data = []
        for url in url_ids:
            json_data = get_objects_json_data(session, url)
            collected_data.append(json_data)
            time.sleep(random.randint(1, 5))
        
        with open('data.json', 'w') as file:
            json.dump(collected_data, file, indent=4)