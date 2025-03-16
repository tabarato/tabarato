from datetime import datetime
import re


def strip_all(text):
    return re.sub(r"\s+", " ", text).strip()

def object_id(id):
    return str(id)

def timestamp(ts):
    return datetime.strptime(str(ts), "%Y-%m-%d %H:%M:%S.%f").timestamp()