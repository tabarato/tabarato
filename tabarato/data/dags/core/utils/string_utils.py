from datetime import datetime
import re

def tokenize(text, words_to_ignore):
    text = text.lower()
    words = sorted(re.findall(r"\b[a-zA-ZÀ-ÿ0-9]+\b", text))

    return "-".join([word for word in words if word not in words_to_ignore])

def object_id(id):
    return str(id)

def timestamp(ts):
    return datetime.strptime(str(ts), "%Y-%m-%d %H:%M:%S.%f").timestamp()