FROM docker.elastic.co/elasticsearch/elasticsearch:7.7.0

COPY init-elasticsearch.sh /usr/share/elasticsearch/init-elasticsearch.sh
COPY products-index.json /usr/share/elasticsearch/products-index.json

RUN chmod +x /usr/share/elasticsearch/init-elasticsearch.sh

CMD ["/bin/bash", "-c", "/usr/local/bin/docker-entrypoint.sh & /usr/share/elasticsearch/init-elasticsearch.sh && wait"]
