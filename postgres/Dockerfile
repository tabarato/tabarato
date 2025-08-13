FROM postgres:15

RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    postgresql-server-dev-15 \
    clang \
    llvm \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/pgvector/pgvector.git /tmp/pgvector && \
    cd /tmp/pgvector && \
    make && make install && \
    rm -rf /tmp/pgvector

CMD ["postgres"]
