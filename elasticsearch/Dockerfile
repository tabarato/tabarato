FROM docker.elastic.co/elasticsearch/elasticsearch:9.0.4

COPY init-elasticsearch.sh /usr/share/elasticsearch/init-elasticsearch.sh
COPY products-index.json /usr/share/elasticsearch/products-index.json

CMD ["/bin/bash", "-c", "/usr/local/bin/docker-entrypoint.sh & /usr/share/elasticsearch/init-elasticsearch.sh && wait"]
