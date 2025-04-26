#!/bin/bash
set -e

until curl -s http://localhost:9200 >/dev/null; do
  sleep 2
done

curl -X PUT "http://localhost:9200/products" \
  -H 'Content-Type: application/json' \
  --data-binary "@/usr/share/elasticsearch/products-index.json"