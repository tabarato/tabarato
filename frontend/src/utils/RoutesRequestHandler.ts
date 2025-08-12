import getEnvVar from './EnvironmentVariables';

const ROUTES_API_KEY = getEnvVar("ROUTES_API_KEY");
const ROUTES_API_URL = getEnvVar("ROUTES_API_URL");

const defaultHeaders = {
  'Content-Type': 'application/json',
  'X-Goog-Api-Key': ROUTES_API_KEY
};

export interface Polyline {
  encodedPolyline: string;
}

export interface RouteLeg {
  distanceMeters: number;
  duration: string;
  polyline?: Polyline;
}

export interface Route {
  duration: string;
  distanceMeters: number;
  polyline?: Polyline;
}

export interface RouteData {
  legs: RouteLeg[];
}

export interface MarketInfo {
  market: string;
  distanceKm: string;
  durationMin: string;
}

export interface Market {
  id: number;
  name: string;
  address: string
};


export function extractDistancesAndDurations(
  routeData: RouteData,
  marketAddresses: string[]
): MarketInfo[] {
  if (!routeData.legs || !Array.isArray(routeData.legs)) {
    throw new Error("Dados de rota inválidos ou ausentes");
  }

  return routeData.legs.map((leg, index) => {
    const market = marketAddresses[index] || `Destino ${index + 1}`;
    const distanceKm = (leg.distanceMeters / 1000).toFixed(2);
    const durationSeconds = parseInt(leg.duration.replace("s", ""), 10);
    const durationMin = Math.round(durationSeconds / 60);

    return {
      market,
      distanceKm: `${distanceKm}`,
      durationMin: `${durationMin}`,
    };
  });
}

export async function getSingleDestinationRoute(
  origin: string,
  destination: string,
  transport: string
): Promise<Route> {
  const data = {
    origin: { address: origin },
    destination: { address: destination },
    travelMode: transport,
    routingPreference: 'TRAFFIC_UNAWARE',
    computeAlternativeRoutes: false,
    routeModifiers: {
      avoidTolls: false,
      avoidHighways: false,
      avoidFerries: false
    },
    languageCode: 'en-US',
    units: 'METRIC'
  };

  const headers = {
    ...defaultHeaders,
    'X-Goog-FieldMask': 'routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline'
  };

  const response = await fetch(ROUTES_API_URL, {
    method: 'POST',
    headers,
    body: JSON.stringify(data)
  });

  if (!response.ok) {
    throw new Error(`Erro ${response.status}: ${await response.text()}`);
  }

  const json = await response.json();
  return json.routes?.[0];
}

export async function getIntermediateRoutes(
  origin: string,
  destination: string,
  intermediates: string[],
  transport: string
): Promise<RouteData> {
  const intermediateAddresses = intermediates.map(address => ({ address }));

  const data = {
    origin: { address: origin },
    destination: { address: destination },
    intermediates: intermediateAddresses,
    travelMode: transport,
    optimizeWaypointOrder: true
  };

  const headers = {
    ...defaultHeaders,
    'X-Goog-FieldMask': 'routes,geocodingResults.intermediates.intermediateWaypointRequestIndex'
  };

  const response = await fetch(ROUTES_API_URL, {
    method: 'POST',
    headers,
    body: JSON.stringify(data)
  });

  if (!response.ok) {
    throw new Error(`Erro ${response.status}: ${await response.text()}`);
  }

  const json = await response.json();
  return json.routes?.[0];
}

export async function getSeparateIntermediateRoutesAsObject(
  origin: string,
  destination: string,
  intermediates: Market[],
  transport: string
): Promise<Record<number, { distanceKm: string; durationMin: string }>> {
  const results: Record<number, { distanceKm: string; durationMin: string }> = {};

  for (const intermediate of intermediates) {
    const data = {
      origin: { address: origin },
      destination: { address: destination },
      intermediates: [{ address: intermediate.address }],
      travelMode: transport,
      optimizeWaypointOrder: false,
    };

    const headers = {
      ...defaultHeaders,
      'X-Goog-FieldMask': 'routes,geocodingResults.intermediates.intermediateWaypointRequestIndex'
    };

    const response = await fetch(ROUTES_API_URL, {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`Erro ${response.status}: ${await response.text()}`);
    }

    const json = await response.json();
    const routeData: RouteData = json.routes?.[0];

    if (!routeData) {
      throw new Error("Rota não encontrada para intermediate: " + intermediate.name);
    }

    const marketInfo = extractDistancesAndDurations(routeData, [intermediate.address])[0];
    
    results[intermediate.id] = {
      distanceKm: marketInfo.distanceKm,
      durationMin: marketInfo.durationMin,
    };
  }

  return results;
}