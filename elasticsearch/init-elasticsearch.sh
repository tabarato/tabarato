#!/bin/bash
set -e

echo "⏳ Esperando Elasticsearch subir..."
until curl -s http://localhost:9200 >/dev/null; do
  sleep 2
done

echo "✅ Elasticsearch disponível. Criando índice 'products'..."

curl -X PUT "http://localhost:9200/products" \
  -H 'Content-Type: application/json' \
  --data-binary "@/usr/share/elasticsearch/products-index.json"