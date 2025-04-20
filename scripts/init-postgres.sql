-- Create Extensions
CREATE EXTENSION PostGIS;
CREATE EXTENSION pgRouting;

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
    clustered_name TEXT NOT NULL UNIQUE,
    id_brand INT REFERENCES brands(id)
);

CREATE TABLE IF NOT EXISTS stores (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    geometry public.GEOMETRY(POINT, 4326)
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

INSERT INTO stores (id, name, geometry) VALUES
(1, 'angeloni', 'POINT (-49.37666810299541 -28.680083083584385)'),
(2, 'bistek', 'POINT (-49.36981307150592 -28.68114410287651)');