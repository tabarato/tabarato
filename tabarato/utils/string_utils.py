import re

def strip_all(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def get_words(text: str) -> list:
    return re.findall(r"{*\b[a-zA-ZÀ-ÿ0-9]+\b[./}]*", text)

def replace_full_word(text: str, old: str, new: str):
    return re.sub(rf"\b{re.escape(old)}\b", new, text, flags=re.IGNORECASE)
