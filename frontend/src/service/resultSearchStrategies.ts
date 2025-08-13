import getEnvVar from '../utils/EnvironmentVariables';

const API_URL = getEnvVar("API_URL");

export interface Market {
  id: number;
  name: string;
  address: string
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

export interface CartResponse {
  bestSingleStore: StoreResult | null;
  bestPerItemStores: StoreResult[];
  bestSingleStoreWithDistance: StoreResultDistanceTime | null;
  bestPerItemStoresWithDistance: StoreResultDistanceTime[];
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


export async function checkout(products, origin, destination, travelMode, stores): Promise<CartResponse> {
    const response = await fetch(`${API_URL}/checkout`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            origin: origin,
            destination: destination,
            travelMode: travelMode,
            stores: stores,
            products: getProductsRequestBody(products)
        }),
    });

    if (!response.ok) {
        throw new Error('Erro ao buscar o melhor mercado por custo/distância/tempo');
    }

    const store: CartResponse = await response.json();
    return {
        ...store,
        bestSingleStore: store.bestSingleStore ? {
            ...store.bestSingleStore,
            formattedTotalCost: formatPrice(store.bestSingleStore.totalCost),
            items: store.bestSingleStore.items.map(item => ({
                ...item,
                formattedPrice: formatPrice(item.price),
                formattedTotalPrice: formatPrice(item.totalPrice)
            }))
        } : null,
        bestPerItemStores: store.bestPerItemStores.map(store => ({
            ...store,
            formattedTotalCost: formatPrice(store.totalCost),
            items: store.items.map(item => ({
                ...item,
                formattedPrice: formatPrice(item.price),
                formattedTotalPrice: formatPrice(item.totalPrice)
            }))
        })),
        bestSingleStoreWithDistance: store.bestSingleStoreWithDistance ? {
            ...store.bestSingleStoreWithDistance,
            formattedTotalCost: formatPrice(store.bestSingleStoreWithDistance.totalCost),
            items: store.bestSingleStoreWithDistance.items.map(item => ({
                ...item,
                formattedPrice: formatPrice(item.price),
                formattedTotalPrice: formatPrice(item.totalPrice)
            }))
        } : null,
        bestPerItemStoresWithDistance: store.bestPerItemStoresWithDistance.map(store => ({
            ...store,
            formattedTotalCost: formatPrice(store.totalCost),
            items: store.items.map(item => ({
                ...item,
                formattedPrice: formatPrice(item.price),
                formattedTotalPrice: formatPrice(item.totalPrice)
            }))
        }))
    };
}

function getProductsRequestBody(products: any): Record<string, number> {
  return Object.fromEntries(products.map(p => [p.id, p.quantity]));
}

function formatPrice(price: number): string {
  return price.toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL'
  });
}
