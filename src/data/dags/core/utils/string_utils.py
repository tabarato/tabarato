import re

def strip_all(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def get_words(text: str) -> list:
    return re.findall(r"\b[a-zA-ZÀ-ÿ0-9]+\b[./]*", text)