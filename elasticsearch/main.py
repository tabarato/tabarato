import json

import requests

DATA_PATH = "..\\scraping-bistek\\data.json"


def get_products():
    with open(DATA_PATH) as f:
        return json.load(f)


if __name__ == "__main__":
    products = get_products()

    request = ""
    for product in products:
        request += '{"index": {}}\n'
        request += json.dumps(product) + '\n'

    headers = {"Content-Type": "application/json"}
    response = requests.post('http://localhost:9200/products/_bulk', data=request, headers=headers)

    if response.status_code != 200:
        print(response.text)
