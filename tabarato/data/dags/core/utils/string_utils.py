import re

def tokenize(text):
    text = text.lower()
    words = re.findall(r"\b[a-zA-ZÀ-ÿ0-9]+\b", text)
    return words