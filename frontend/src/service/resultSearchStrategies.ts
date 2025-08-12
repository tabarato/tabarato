import { useState, useEffect } from 'react';
import getEnvVar from '../utils/EnvironmentVariables';
import { getSeparateIntermediateRoutesAsObject, Market } from "../utils/RoutesRequestHandler"

const API_URL = getEnvVar("API_URL");

const defaultHeaders = {
  'Content-Type': 'application/json'
};

export interface ProductItem {
  name: string;
  price: number;
  cartLink: string;
  formattedPrice?: string;
  totalPrice: number;
  quantity?: number;
  formattedTotalPrice?: string;
}

export interface StoreResult {
  storeName: string;
  items: ProductItem[];
  totalCost: number;
  formattedTotalCost?: string;
}

export interface StoreResultDistanceTime {
  storeName: string;
  items: ProductItem[];
  totalCost: number;
  formattedTotalCost?: string;
  distanceInfo: DistanceInfo;
}

export interface DistanceInfo {
  distanceKm: number;
  durationMin: number;
}

export function formatPrice(price: number): string {
  return price.toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  });
}

export async function findBestMarketByCostDistanceTime(products, distances): Promise<StoreResultDistanceTime> {
    const response = await fetch(`${API_URL}/checkout/cheapest-store-with-distance`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            products: getProductsRequestBody(products),
            distances: distances,
        }),
    });

    if (!response.ok) {
        throw new Error('Erro ao buscar o melhor mercado por custo/distância/tempo');
    }

    const store: StoreResultDistanceTime = await response.json();
    return {
        ...store,
        formattedTotalCost: formatPrice(store.totalCost),
        items: store.items.map(item => ({
            ...item,
            formattedPrice: formatPrice(item.price),
            formattedTotalPrice: formatPrice(item.totalPrice)
        }))
    };
}

export async function findMarketsByCostDistanceTime(products, distances): Promise<StoreResultDistanceTime[]> {
    const response = await fetch(`${API_URL}/checkout/cheapest-stores-ranking-with-distance`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            products: getProductsRequestBody(products),
            distances: distances,
        }),
    });

    if (!response.ok) {
        throw new Error('Erro ao buscar o melhor mercado por custo/distância/tempo');
    }

    const stores: StoreResultDistanceTime[] = await response.json();
    return stores.map(store => ({
        ...store,
        formattedTotalCost: formatPrice(store.totalCost),
        items: store.items.map(item => ({
            ...item,
            formattedPrice: formatPrice(item.price),
            formattedTotalPrice: formatPrice(item.totalPrice)
        }))
    }));
}

export async function findLowestCostSingleMarket(products): Promise<StoreResult> {
  const url = `${API_URL}/checkout/cheapest-store`;

  const response = await fetch(url, {
    method: 'POST',
    headers: defaultHeaders,
    body: JSON.stringify({ products: getProductsRequestBody(products) })
  });

  if (!response.ok) {
    throw new Error(`Erro ${response.status}: ${await response.text()}`);
  }

  const store: StoreResult = await response.json();
  return {
      ...store,
      formattedTotalCost: formatPrice(store.totalCost),
      items: store.items.map(item => ({
          ...item,
          formattedPrice: formatPrice(item.price),
          formattedTotalPrice: formatPrice(item.totalPrice)
      }))
  };
}

export async function findLowestCostAcrossMarkets(
  products
): Promise<StoreResult[]> {
  const url = `${API_URL}/checkout/cheapest-items`;

  const response = await fetch(url, {
    method: 'POST',
    headers: defaultHeaders,
    body: JSON.stringify({ products: getProductsRequestBody(products) })
  });

  if (!response.ok) {
    throw new Error(`Erro ${response.status}: ${await response.text()}`);
  }

  const stores: StoreResult[] = await response.json();
  return stores.map(store => ({
    ...store,
    formattedTotalCost: formatPrice(store.totalCost),
    items: store.items.map(item => ({
      ...item,
      formattedPrice: formatPrice(item.price),
      formattedTotalPrice: formatPrice(item.totalPrice)
    }))
  }));
}

export function findMarketsRoutes(
    origin: string,
    destination: string,
    intermediates: string[],
    transport: string
): {
    marketAddresses: Record<number, { distanceKm: string; durationMin: string }> | null;
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
                const res = await fetch(`${API_URL}/stores?slugs=`+ intermediates.join('&slugs='));
                if (!res.ok) throw new Error('Erro ao buscar endereços dos mercados');
                const markets: Market[] = await res.json();
                if (!markets || markets.length === 0) throw new Error(`Endereços não encontrados para os mercados`);

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

function getProductsRequestBody(products: { productId: string; quantity: number }[]): Record<string, number> {
  return Object.fromEntries(products.map(p => [p.productId, p.quantity]));
}