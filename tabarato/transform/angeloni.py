from .transformer import Transformer
from tabarato.loader import Loader
import pandas as pd


class AngeloniTransformer(Transformer):
    @classmethod
    def slug(cls) -> str:
        return "angeloni"

    @classmethod
    def transform(cls) -> pd.DataFrame:
        df = Loader.read("bronze", cls.slug())

        df.rename(columns={
            "productName": "name",
            "productId": "refId",
            "Quantidade da embalagem": "weight",
            "Unidade de medida": "measure"},
            inplace=True)

        df[["imageUrl", "cartLink", "price", "oldPrice"]] = df.apply(cls._extract_item_info, axis=1)

        return super().transform(df)

    @classmethod
    def _extract_item_info(cls, row):
        items = row["items"]
        
        if not items.any():
            return pd.Series({"cartLink": None, "price": None, "oldPrice": None})

        values = pd.Series({"imageUrl": None, "cartLink": None, "price": None, "oldPrice": None})

        item = items[0]
        if "sellers" in item and item["sellers"].any():
            seller = item["sellers"][0]
            commertial_offer = seller.get("commertialOffer", {})

            values["cartLink"] = seller.get("addToCartLink", None)
            values["price"] = commertial_offer.get("Price", None)
            values["oldPrice"] = commertial_offer.get("ListPrice", None)
        
        if "images" in item and item["images"].any():
            image = item["images"][0]
            values["imageUrl"] = image.get("imageUrl", None)
        
        return values
