from datetime import datetime
import re

def tokenize(text):
    text = text.lower()
    words = re.findall(r"\b[a-zA-ZÀ-ÿ0-9]+\b", text)
    return words

def object_id(id):
    return str(id)

def timestamp(ts):
    return datetime.strptime(str(ts), "%Y-%m-%d %H:%M:%S.%f").timestamp()