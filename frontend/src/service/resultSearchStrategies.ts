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
  total_price: number;
  quantity?: number;
  formattedTotalPrice?: string;
}

export interface StoreResult {
  store_name: string;
  buy_list: ProductItem[];
  buy_list_minimal_cost: number;
  formattedListPrice?: string;
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

export async function findBestMarketByCostDistanceTime(products, distances): Promise<StoreResultDistanceTime> {
    const response = await fetch(`${BACKEND_API_URL}get_cheapest_and_closest_store_with_all_items`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            products: products,
            distances: distances,
        }),
    });

    if (!response.ok) {
        throw new Error('Erro ao buscar o melhor mercado por custo/distância/tempo');
    }

    const json: StoreResultDistanceTime[] = await response.json();

    const store = json[0];
    
    return {
        ...store,
        formattedTotalPrice: formatPrice(store.buy_list_minimal_cost),
        buy_list: store.buy_list.map(item => ({
            ...item,
            formattedPrice: formatPrice(item.price),
            formattedTotalPrice: formatPrice(item.total_price),
            quantity: item.quantity
        }))
    };
}

export async function findMarketsByCostDistanceTime(products, distances): Promise<StoreResultDistanceTime[]> {
    const response = await fetch(`${BACKEND_API_URL}get_store_ranking_by_cost_distance_time`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            products: products,
            distances: distances,
        }),
    });

    if (!response.ok) {
        throw new Error('Erro ao buscar o melhor mercado por custo/distância/tempo');
    }

    const json: StoreResultDistanceTime[] = await response.json();

    return json.map(store => ({
        ...store,
        formattedTotalPrice: formatPrice(store.buy_list_minimal_cost),
        buy_list: store.buy_list.map(item => ({
            ...item,
            formattedPrice: formatPrice(item.price),
            formattedTotalPrice: formatPrice(item.total_price),
            quantity: item.quantity
        }))
    }));
}

export async function findLowestCostSingleMarket(products): Promise<StoreResult[]> {
  const url = `${BACKEND_API_URL}find_store_with_lowest_total_cost`;

  const response = await fetch(url, {
    method: 'POST',
    headers: defaultHeaders,
    body: JSON.stringify({products: products })
  });

  if (!response.ok) {
    throw new Error(`Erro ${response.status}: ${await response.text()}`);
  }

  const json: StoreResult[] = await response.json();

  return json.map(store => ({
    ...store,
    formattedListPrice: formatPrice(store.buy_list_minimal_cost),
    buy_list: store.buy_list.map(item => ({
      ...item,
      formattedPrice: formatPrice(item.price),
      formattedTotalPrice: formatPrice(item.total_price),
      quantity: item.quantity
    }))
  }));
}

export async function findLowestCostAcrossMarkets(
  products
): Promise<StoreResult[]> {
  const url = `${BACKEND_API_URL}get_cheapest_items_across_stores`;

  const response = await fetch(url, {
    method: 'POST',
    headers: defaultHeaders,
    body: JSON.stringify({ products: products })
  });

  if (!response.ok) {
    throw new Error(`Erro ${response.status}: ${await response.text()}`);
  }

  const json: StoreResult[] = await response.json();

  return json.map(store => ({
    store_name: store.store_name,
    buy_list: store.buy_list.map(item => ({
      ...item,
      formattedPrice: formatPrice(item.price),
      formattedTotalPrice: formatPrice(item.total_price),
      quantity: item.quantity
    })),
    buy_list_minimal_cost: store.buy_list_minimal_cost,
    formattedListPrice: formatPrice(store.buy_list_minimal_cost)
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

export function useMarketsRoutes(
  origin: string,
  destination: string,
  intermediates: string[],
  transport: string
) {
  const [marketAddresses, setMarketAddresses] = useState<Record<string, { distanceKm: string; durationMin: string }> | null>(null);
  const [marketLoading, setLoading] = useState(true);
  const [marketError, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchAndCalculateRoutes() {
      if (!origin || !destination || !transport || !intermediates?.length) {
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
            if (!data?.length) throw new Error(`Endereço não encontrado para o mercado ${marketName}`);
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