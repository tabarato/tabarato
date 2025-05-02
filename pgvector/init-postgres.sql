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

CREATE TABLE brand (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE store (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE product_family (
	id SERIAL PRIMARY KEY,
	id_brand SERIAL REFERENCES brand(id),
	name TEXT,
	embedded_name vector(768)
);

CREATE TABLE product (
	id SERIAL PRIMARY KEY,
	id_product_family SERIAL REFERENCES product_family(id),
	name TEXT,
	embedded_name vector(768),
  weight INTEGER,
  measure TEXT
);

CREATE TABLE store_product (
  id SERIAL PRIMARY KEY,
  id_store SERIAL NOT NULL REFERENCES store(id),
  id_product SERIAL NOT NULL REFERENCES product(id),
  ref_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  price NUMERIC(10, 4),
  old_price NUMERIC(10, 4),
  link TEXT,
  cart_link TEXT,
  image_url TEXT,
  UNIQUE (id_store, id_product)
);

INSERT INTO store (id, name) VALUES
(1, 'angeloni'),
(2, 'bistek'),
(3, 'giassi');