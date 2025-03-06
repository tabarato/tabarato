import hrequests
import os
from dotenv import load_dotenv

load_dotenv()

class BistekScraper:
    products_url = []
    main_page_url = os.getenv("BISTEK_MAIN_PAGE_URL")

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
    def scrap_market(cls) -> None:
        """Collect data from Bistek Online Market"""
        try:
            with hrequests.Session() as session:
                req_object = session.get(cls.main_page_url)
                print("URL: ", cls.main_page_url, " Status: ", req_object.status_code)
        except Exception as e:
            raise e
        