# Use a imagem oficial do PostgreSQL baseada no Alpine
FROM postgres:15-alpine

# Instale as dependências necessárias para compilar extensões do PostgreSQL,
# incluindo build-base (gcc, make, etc.), git, desenvolvimento do PostgreSQL,
# clang e LLVM
RUN apk add --no-cache build-base git postgresql-dev clang llvm-dev

# Cria um link simbólico para que o comando "clang-19" aponte para o clang instalado
RUN ln -sf /usr/bin/clang /usr/bin/clang-19

# Clone, compile e instale o pgvector
RUN git clone https://github.com/pgvector/pgvector.git /tmp/pgvector && \
    cd /tmp/pgvector && \
    make && make install && \
    rm -rf /tmp/pgvector

# Comando padrão para iniciar o PostgreSQL
CMD ["postgres"]
