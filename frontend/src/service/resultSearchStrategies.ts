import { useState, useEffect } from 'react';
import getEnvVar from '../utils/EnvironmentVariables';
import { getSeparateIntermediateRoutesAsObject, Market } from "../utils/RoutesRequestHandler"

const BACKEND_API_URL = getEnvVar("POSTGREST_URL");

const defaultHeaders = {
  'Content-Type': 'application/json'
};

export interface ProductItem {
  name: string;
  price: number;
  cart_link: string;
  formattedPrice?: string;
}

export interface StoreResult {
  store_name: string;
  buy_list: ProductItem[];
  buy_list_minimal_cost: number;
  formattedTotalPrice?: string;
}

export interface StoreResultDistanceTime {
  store_name: string;
  buy_list: ProductItem[];
  buy_list_minimal_cost: number;
  formattedTotalPrice?: string;
  distance_km: number;
  duration_min: number;
}

export function formatPrice(price: number): string {
  return price.toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  });
}

export async function findBestMarketByCostDistanceTime(productIds, distances): Promise<StoreResultDistanceTime> {
    const response = await fetch(`${BACKEND_API_URL}find_best_market_by_cost_distance_time`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            products_ids: productIds,
            distances: distances,
        }),
    });

    if (!response.ok) {
        throw new Error('Erro ao buscar o melhor mercado por custo/distância/tempo');
    }

    const json: StoreResultDistanceTime[] = await response.json();

    const store = json[0];
    
    console.log(formatPrice(store.buy_list_minimal_cost))
    
    return {
        ...store,
        formattedTotalPrice: formatPrice(store.buy_list_minimal_cost),
        buy_list: store.buy_list.map(item => ({
            ...item,
            formattedPrice: formatPrice(item.price)
        }))
    };
}

export async function findLowestCostSingleMarket(
  idProducts: number[]
): Promise<StoreResult[]> {
  const url = `${BACKEND_API_URL}get_cheapest_store_with_all_products`;

  const response = await fetch(url, {
    method: 'POST',
    headers: defaultHeaders,
    body: JSON.stringify({ id_products: idProducts })
  });

  if (!response.ok) {
    throw new Error(`Erro ${response.status}: ${await response.text()}`);
  }

  const json: StoreResult[] = await response.json();

  return json.map(store => ({
    ...store,
    formattedTotalPrice: formatPrice(store.buy_list_minimal_cost),
    buy_list: store.buy_list.map(item => ({
      ...item,
      formattedPrice: formatPrice(item.price)
    }))
  }));
}

export async function findLowestCostAcrossMarkets(
  idProducts: number[]
): Promise<StoreResult[]> {
  const url = `${BACKEND_API_URL}get_minimal_cost_product_list`;

  const response = await fetch(url, {
    method: 'POST',
    headers: defaultHeaders,
    body: JSON.stringify({ id_products: idProducts })
  });

  if (!response.ok) {
    throw new Error(`Erro ${response.status}: ${await response.text()}`);
  }

  const json: StoreResult[] = await response.json();

  return json.map(store => ({
    store_name: store.store_name,
    buy_list: store.buy_list.map(item => ({
      ...item,
      formattedPrice: formatPrice(item.price)
    })),
    buy_list_minimal_cost: store.buy_list_minimal_cost,
    formattedTotalPrice: formatPrice(store.buy_list_minimal_cost)
  }));
}

// Opção 4: Busca rápida pelo mercado mais próximo
export function findNearestMarket(): any {
    return BACKEND_API_URL;
}

// Opção 5: Economia suprema com melhor trajeto para mercados com menor preço dos produtos
export function findOptimalRouteForCheapestMarkets(): any {
    return BACKEND_API_URL;
}

export function findMarketsRoutes(
    origin: string,
    destination: string,
    intermediates: string[],
    transport: string
): {
    marketAddresses: Record<string, { distanceKm: string; durationMin: string }> | null;
    marketLoading: boolean;
    marketError: string | null;
} {
    const [marketAddresses, setMarketAddresses] = useState<Record<string, { distanceKm: string; durationMin: string }> | null>(null);
    const [marketLoading, setLoading] = useState(true);
    const [marketError, setError] = useState<string | null>(null);

    useEffect(() => {
        async function fetchAndCalculateRoutes() {
            if (!origin || !destination || !transport || !intermediates || intermediates.length === 0) {
                setError("Dados insuficientes para calcular rotas intermediárias.");
                setLoading(false);
                return;
            }

            setLoading(true);
            setError(null);

            try {
                const markets: Market[] = await Promise.all(
                    intermediates.map(async (marketName) => {
                        const res = await fetch(`http://localhost:3000/store?name=eq.${marketName}`);
                        if (!res.ok) throw new Error(`Erro ao buscar endereço do mercado ${marketName}`);
                        const data = await res.json();
                        if (!data || data.length === 0) throw new Error(`Endereço não encontrado para o mercado ${marketName}`);
                        return { name: marketName, address: data[0].address };
                    })
                );

                const results = await getSeparateIntermediateRoutesAsObject(origin, destination, markets, transport);
                setMarketAddresses(results);
            } catch (err: any) {
                setError(err.message || "Erro desconhecido ao buscar rotas.");
            } finally {
                setLoading(false);
            }
        }

        fetchAndCalculateRoutes();
    }, [origin, destination, intermediates, transport]);

    return { marketAddresses, marketLoading, marketError };
}
