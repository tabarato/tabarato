from .transformer import Transformer
from tabarato.loader import Loader
import pandas as pd
import json

class BistekTransformer(Transformer):
    @classmethod
    def slug(cls) -> str:
        return "bistek"

    @classmethod
    def transform(cls, ti, df) -> pd.DataFrame:
        
        df.rename(columns={
            "productName": "name",
            "productId": "refId",
            "Peso Produto": "weight",
            "Unidade de Medida": "measure"},
            inplace=True)
        
        df[["cartLink", "price", "oldPrice"]] = df.apply(cls._extract_price_info, axis=1)
        
        return super().transform(ti, df)

    @classmethod
    def _extract_price_info(cls, row):
        items = row["items"]

        if not items:
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
