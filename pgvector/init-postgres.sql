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
  name TEXT NOT NULL UNIQUE,
  address TEXT NOT NULL
);

CREATE TABLE product_family (
	id SERIAL PRIMARY KEY,
	id_brand SERIAL REFERENCES brand(id),
	name TEXT,
	embedded_name vector(768)
);

CREATE TABLE product (
	id SERIAL PRIMARY KEY,
	id_product_family SERIAL REFERENCES product_family(id) ON DELETE CASCADE,
	name TEXT,
  weight INTEGER,
  measure TEXT
);

CREATE TABLE store_product (
  id SERIAL PRIMARY KEY,
  id_store SERIAL NOT NULL REFERENCES store(id),
  id_product SERIAL NOT NULL REFERENCES product(id) ON DELETE CASCADE,
  ref_id INTEGER NOT NULL,
  name TEXT NOT NULL,
  price NUMERIC(10, 4),
  old_price NUMERIC(10, 4),
  link TEXT,
  cart_link TEXT,
  image_url TEXT,
  UNIQUE (id_store, id_product)
);

CREATE INDEX idx_product_family_vector ON product_family
USING ivfflat (embedded_name vector_l2_ops) WITH (lists = 100);

INSERT INTO store (id, name, address) VALUES
(1, 'angeloni', 'angeloni centenario'),
(2, 'bistek', 'supermercado bistek avenida centenario'),
(3, 'giassi', 'giassi santa barbara');

CREATE OR REPLACE FUNCTION public.get_cheapest_items_across_stores(products jsonb)
 RETURNS TABLE(store_name text, buy_list json, buy_list_minimal_cost numeric)
 LANGUAGE plpgsql
AS $function$
BEGIN
    RETURN QUERY
    WITH product_list AS (
        SELECT
            (p.value->>'id_product')::integer AS id_product,
            (p.value->>'quantity')::numeric AS quantity
        FROM jsonb_array_elements(products) AS p
    ),
    minimal_products AS (
        SELECT DISTINCT ON (s.id_product)
            s.id_product,
            s.name AS product_name,
            s.id_store,
            st.name AS q_store_name,
            s.price * pl.quantity AS total_price,
			pl.quantity,
			s.price,
            s.cart_link
        FROM store_product s
        JOIN store st ON st.id = s.id_store
        JOIN product_list pl ON pl.id_product = s.id_product
        ORDER BY s.id_product, s.price ASC
    )
    SELECT
        q_store_name,
        json_agg(json_build_object(
            'name', product_name,
            'price', price,
            'cart_link', cart_link,
			'total_price', total_price,
			'quantity', quantity
        )) AS buy_list,
        SUM(total_price) AS buy_list_minimal_cost
    FROM minimal_products
    GROUP BY q_store_name;
END;
$function$
;


CREATE OR REPLACE FUNCTION public.get_cheapest_and_closest_store_with_all_items(products jsonb, distances jsonb)
 RETURNS TABLE(store_name text, buy_list jsonb, buy_list_minimal_cost numeric, distance_km numeric, duration_min integer)
 LANGUAGE plpgsql
AS $function$
BEGIN
    RETURN QUERY
    WITH product_list AS (
        SELECT
            (p.value->>'id_product')::integer AS id_product,
            (p.value->>'quantity')::numeric AS quantity
        FROM jsonb_array_elements(products) AS p
    ),
    minimal_cost_selected_products AS (
        SELECT
            sp.id_product,
            pl.quantity,
            sp.name,
            sp.id_store,
            s.name AS q_store_name,
            (sp.price * pl.quantity) AS total_price,
            sp.cart_link,
			sp.price
        FROM store_product sp
        JOIN store s ON sp.id_store = s.id
        JOIN product_list pl ON pl.id_product = sp.id_product
    ),
    store_aggregates AS (
        SELECT
            msp.id_store,
            msp.q_store_name,
            COUNT(DISTINCT msp.id_product) AS product_count,
            SUM(msp.total_price) AS buy_list_minimal_cost,
            jsonb_agg(jsonb_build_object(
                'name', msp.name,
                'price', msp.price,
                'cart_link', msp.cart_link,
				'total_price', msp.total_price,
				'quantity', msp.quantity
            )) AS buy_list
        FROM minimal_cost_selected_products msp
        GROUP BY msp.id_store, msp.q_store_name
        HAVING COUNT(DISTINCT msp.id_product) = (SELECT COUNT(*) FROM product_list)
    ),
    distance_time AS (
        SELECT
            key AS q_store_name,
            (value ->> 'distanceKm')::numeric AS distance_km,
            (value ->> 'durationMin')::int AS duration_min
        FROM jsonb_each(distances)
    ),
    combined AS (
        SELECT
            sa.q_store_name AS combined_store_name,
            sa.buy_list AS combined_buy_list,
            sa.buy_list_minimal_cost AS combined_buy_list_minimal_cost,
            dt.distance_km AS combined_distance_km,
            dt.duration_min AS combined_duration_min
        FROM store_aggregates sa
        JOIN distance_time dt ON sa.q_store_name = dt.q_store_name
    )
    SELECT
        combined.combined_store_name AS store_name,
        combined.combined_buy_list AS buy_list,
        combined.combined_buy_list_minimal_cost AS buy_list_minimal_cost,
        combined.combined_distance_km AS distance_km,
        combined.combined_duration_min AS duration_min
    FROM combined
    ORDER BY
        combined.combined_buy_list_minimal_cost ASC,
        combined.combined_distance_km ASC,
        combined.combined_duration_min ASC
    LIMIT 1;
END;
$function$
;


CREATE OR REPLACE FUNCTION public.find_store_with_lowest_total_cost(products jsonb)
 RETURNS TABLE(store_name text, buy_list json, buy_list_minimal_cost numeric)
 LANGUAGE plpgsql
AS $function$
BEGIN
    RETURN QUERY
    WITH product_list AS (
        SELECT
            (p.value->>'id_product')::integer AS id_product,
            (p.value->>'quantity')::numeric AS quantity
        FROM jsonb_array_elements(products) AS p
    ),
    minimal_cost_selected_products AS (
        SELECT
            sp.id_product,
            pl.quantity,
            sp.name,
            sp.id_store,
            (SELECT name FROM store WHERE id = sp.id_store) AS q_store_name,
            (sp.price * pl.quantity) AS total_price,
			sp.price,
            sp.cart_link
        FROM store_product sp
        JOIN product_list pl ON pl.id_product = sp.id_product
    ),
    store_aggregates AS (
        SELECT
            id_store,
            q_store_name,
            COUNT(DISTINCT id_product) AS product_count,
            SUM(total_price) AS buy_list_minimal_cost,
            JSON_AGG(JSON_BUILD_OBJECT(
                'name', name,
                'price', price,
                'cart_link', cart_link,
				'total_price', total_price,
				'quantity', quantity
            )) AS buy_list
        FROM minimal_cost_selected_products
        GROUP BY id_store, q_store_name
        HAVING COUNT(DISTINCT id_product) = (SELECT COUNT(*) FROM product_list)
    ),
    min_cost_store AS (
        SELECT *
        FROM store_aggregates
        ORDER BY buy_list_minimal_cost ASC
        LIMIT 1
    )
    SELECT
        min_cost_store.q_store_name AS store_name,
        min_cost_store.buy_list,
        min_cost_store.buy_list_minimal_cost
    FROM min_cost_store;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.get_store_ranking_by_cost_distance_time(products jsonb, distances jsonb)
 RETURNS TABLE(store_name text, buy_list jsonb, buy_list_minimal_cost numeric, distance_km numeric, duration_min integer)
 LANGUAGE plpgsql
AS $function$
BEGIN
    RETURN QUERY
    WITH product_list AS (
        SELECT
            (p.value->>'id_product')::integer AS id_product,
            (p.value->>'quantity')::numeric AS quantity
        FROM jsonb_array_elements(products) AS p
    ),
    minimal_products AS (
        SELECT DISTINCT ON (s.id_product)
            s.id_product,
            s.name AS product_name,
            s.id_store,
            st.name AS q_store_name,
            (s.price * pl.quantity) AS total_price,
			pl.quantity,
			s.price,
            s.cart_link
        FROM store_product s
        JOIN store st ON st.id = s.id_store
        JOIN product_list pl ON pl.id_product = s.id_product
        ORDER BY s.id_product, total_price ASC
    ),
    store_aggregates AS (
        SELECT
            msp.id_store,
            msp.q_store_name,
            COUNT(DISTINCT msp.id_product) AS product_count,
            SUM(msp.total_price) AS buy_list_minimal_cost,
            jsonb_agg(jsonb_build_object(
                'name', msp.product_name,
                'price', msp.price,
                'cart_link', msp.cart_link,
				'total_price', msp.total_price,
				'quantity', msp.quantity
            )) AS buy_list
        FROM minimal_products msp
        GROUP BY msp.id_store, msp.q_store_name
    ),
    distance_time AS (
        SELECT
            key AS store_name,
            (value ->> 'distanceKm')::numeric AS distance_km,
            (value ->> 'durationMin')::int AS duration_min
        FROM jsonb_each(distances)
    ),
    combined AS (
        SELECT
            sa.q_store_name AS combined_store_name,
            sa.buy_list AS combined_buy_list,
            sa.buy_list_minimal_cost AS combined_buy_list_minimal_cost,
            dt.distance_km AS combined_distance_km,
            dt.duration_min AS combined_duration_min
        FROM store_aggregates sa
        JOIN distance_time dt ON LOWER(sa.q_store_name) = LOWER(dt.store_name)
    )
    SELECT
        combined.combined_store_name AS store_name,
        combined.combined_buy_list AS buy_list,
        combined.combined_buy_list_minimal_cost AS buy_list_minimal_cost,
        combined.combined_distance_km AS distance_km,
        combined.combined_duration_min AS duration_min
    FROM combined
    ORDER BY
        combined.combined_buy_list_minimal_cost ASC,
        combined.combined_distance_km ASC,
        combined.combined_duration_min ASC;
END;
$function$
;