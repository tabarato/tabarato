from core.etl import StoreETL

class AngeloniETL(StoreETL):
    @classmethod
    def slug(cls) -> str:
        return "angeloni"