-- Quero saber o melhor mercado para comprar os produtos desejados que tenha o menor custo total, a menor distância até mim e o menor tempo de deslocamento
WITH selected_products AS (
	SELECT * FROM store_products where id in (718, 721, 3208, 3207, 36, 37, 6496, 6497)
)

SELECT
	store_name,
	SUM(price) OVER (PARTITION BY (store_name)) AS "total_cost",
	MIN(distance) OVER (PARTITION BY (store_name)) AS "min_distance",
	MIN(travel_time_car) OVER (PARTITION BY (store_name)) AS "min_travel_time_car",
	MIN(travel_time_motorcycle) OVER (PARTITION BY (store_name)) AS "min_travel_time_motorcycle",
	MIN(travel_time_bicycle) OVER (PARTITION BY (store_name)) AS "min_travel_time_bicycle",
	MIN(travel_time_walk) OVER (PARTITION BY (store_name)) AS "min_travel_time_walk",
	array_agg(cart_link) OVER (PARTITION BY (store_name)) AS "cart_link_agg"
FROM selected_products
ORDER BY (travel_time_car, travel_time_motorcycle, travel_time_bicycle, travel_time_walk) ASC
LIMIT 1


-- Quero saber em qual mercado devo comprar os produtos escolhidos levando em consideração apenas o custo mínimo possível
WITH minimal_cost_selected_products AS (
	SELECT DISTINCT ON (id_product)
        id_product,
        name,
        store_name,
        price,
        cart_link
    FROM store_products
	WHERE id IN (718, 721, 3208, 3207, 36, 37, 6496, 6497)
    ORDER BY id_product, price ASC
) 
    
SELECT
	store_name,
	json_agg(json_build_object(
		'name', name,
		'price', price,
		'cart_link', cart_link
	)) AS "buy_list",
	SUM(price) AS "buy_list_minimal_cost"
FROM minimal_cost_selected_products
GROUP BY store_name