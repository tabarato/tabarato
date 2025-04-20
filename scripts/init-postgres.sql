CREATE TABLE IF NOT EXISTS brands (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    clustered_name TEXT NOT NULL UNIQUE,
    id_brand INT REFERENCES brands(id)
);

CREATE TABLE IF NOT EXISTS stores (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS store_products (
    id SERIAL PRIMARY KEY,
    id_store INT NOT NULL REFERENCES stores(id),
    id_product INT NOT NULL REFERENCES products(id),
    name TEXT NOT NULL,
    weight TEXT,
    measure TEXT,
    price NUMERIC,
    old_price NUMERIC,
    link TEXT,
    cart_link TEXT,
    image_url TEXT
);

INSERT INTO stores (id, name) VALUES
(1, 'angeloni'),
(2, 'bistek');

-- CREATE TABLE IF NOT EXISTS store_product_prices_history (
--     id SERIAL PRIMARY KEY,
--     id_store_product INT NOT NULL REFERENCES store_products(id),
--     price NUMERIC,
--     old_price NUMERIC,
--     date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );