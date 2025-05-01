-- Create Extensions
CREATE EXTENSION IF NOT EXISTS vector;

-- PgREST users
CREATE ROLE authenticator WITH SUPERUSER;
CREATE ROLE anon WITH SUPERUSER;

-- Create an event trigger function
CREATE OR REPLACE FUNCTION pgrst_watch() RETURNS event_trigger
  LANGUAGE plpgsql
  AS $$
BEGIN
  NOTIFY pgrst, 'reload schema';
END;
$$;

-- This event trigger will fire after every ddl_command_end event
CREATE EVENT TRIGGER pgrst_watch
  ON ddl_command_end
  EXECUTE PROCEDURE pgrst_watch();

CREATE TABLE IF NOT EXISTS brands (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    clustered_name TEXT NOT NULL,
    id_brand INT REFERENCES brands(id),
    weight INTEGER,
    measure TEXT
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
    price NUMERIC,
    old_price NUMERIC,
    link TEXT,
    cart_link TEXT,
    image_url TEXT
);

CREATE TABLE product_family (
	id SERIAL PRIMARY KEY,
	id_brand INT REFERENCES brands(id),
	clustered_name TEXT,
	embedded_name vector(768)
);

INSERT INTO stores (id, name) VALUES
(1, 'angeloni'),
(2, 'bistek');