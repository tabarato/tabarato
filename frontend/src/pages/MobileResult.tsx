import { useEffect, useState, useRef } from "react";
import {
  findLowestCostSingleMarket,
  findLowestCostAcrossMarkets,
  StoreResult,
  findBestMarketByCostDistanceTime,
  findMarketsByCostDistanceTime,
  findMarketsRoutes
} from "../service/resultSearchStrategies";
import InfoLabelMobile from "../utils/InfoLabelMobile";

const originAddress = "Rua Pascoal Meler, 73";
const destinationAddress = "Rua Domênico Sônego, 542";
const travelMode = "DRIVE";
const products = [
  { "product_id": 975, "quantity": 1 },
  { "product_id": 3397, "quantity": 2 },
  { "product_id": 7126, "quantity": 1 },
  { "product_id": 4061, "quantity": 1 },
  { "product_id": 6629, "quantity": 1 },
  { "product_id": 4646, "quantity": 1 },
  { "product_id": 2506, "quantity": 1 },
  { "product_id": 7779, "quantity": 1 },
  { "product_id": 3143, "quantity": 1 }
];
const markets = ["giassi", "angeloni", "bistek"];

export default function MobileResultPage() {
  const [storeDataSingle, setStoreDataSingle] = useState<StoreResult | null>(null);
  const [storeDataSplit, setStoreDataSplit] = useState<StoreResult[]>([]);
  const [bestMarketCombined, setBestMarketCombined] = useState<any>(null);
  const [bestMarkets, setBestMarkets] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentSlide, setCurrentSlide] = useState(0);

  const carouselRef = useRef<HTMLDivElement>(null);
  const touchStartXRef = useRef(0);
  const { marketAddresses } = findMarketsRoutes(originAddress, destinationAddress, markets, travelMode);

  useEffect(() => {
    async function fetchData() {
      try {
        const single = await findLowestCostSingleMarket(products);
        setStoreDataSingle(single);

        const split = await findLowestCostAcrossMarkets(products);
        setStoreDataSplit(split);

        if (marketAddresses) {
          const bestMarket = await findBestMarketByCostDistanceTime(products, marketAddresses);
          setBestMarketCombined(bestMarket);
          const bestMarketsData = await findMarketsByCostDistanceTime(products, marketAddresses);
          setBestMarkets(bestMarketsData);
        }
      } catch (err: any) {
        setError(err.message || "Erro ao buscar dados.");
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [marketAddresses]);

  function buildVTEXCartLink(buyList: { cartLink: string }[]): string {
    if (buyList.length === 0) return "#";

    const baseUrl = new URL(buyList[0].cartLink);
    const params = new URLSearchParams();

    buyList.forEach(item => {
      const url = new URL(item.cartLink);
      url.searchParams.forEach((value, key) => {
        params.append(key, value);
      });
    });

    return `${baseUrl.origin}${baseUrl.pathname}?${params.toString()}`;
  }

  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartXRef.current = e.touches[0].clientX;
  };

  const handleTouchEnd = (e: React.TouchEvent) => {
    const touchEndX = e.changedTouches[0].clientX;
    const diff = touchStartXRef.current - touchEndX;
    const threshold = 50;

    if (diff > threshold) {
      scrollToSlide((currentSlide + 1) % slides.length);
    } else if (diff < -threshold) {
      scrollToSlide((currentSlide - 1 + slides.length) % slides.length);
    }
  };

  const scrollToSlide = (index: number) => {
    if (carouselRef.current) {
      const slideWidth = carouselRef.current.clientWidth;
      carouselRef.current.scrollTo({
        left: index * slideWidth,
        behavior: "smooth",
      });
      setCurrentSlide(index);
    }
  };

  const slides = [
    {
      id: "slide1",
      content: (
        <>
          <InfoLabelMobile text="🏆 Menor custo total num único mercado com todos os produtos" color="accent" />
          {loading && <span className="text-sm">Carregando...</span>}
          {error && <span className="text-sm text-error">{error}</span>}
          {storeDataSingle && (
            <div className="mb-6 rounded-xl border border-base-300 bg-base-200 p-4 shadow-sm">
              <div className="flex justify-between items-center mb-4">
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full bg-warning"></div>
                  <h2 className="text-lg font-bold capitalize">
                    Mercado {storeDataSingle.storeName[0].toUpperCase()}
                  </h2>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="table table-sm">
                  <thead>
                    <tr>
                      <th>Produto</th>
                      <th>Preço Unit.</th>
                      <th>Qtd</th>
                      <th className="text-right">Preço Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {storeDataSingle.items.map((item, index) => (
                      <tr key={index}>
                        <td>{item.name}</td>
                        <td className="text-center">{item.formattedPrice}</td>
                        <td className="text-center">{item.quantity}</td>
                        <td className="text-right">{item.formattedTotalPrice}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="mt-12">
                <div className="flex justify-end mb-3 pr-2">
                  <span className="text-md font-semibold">
                    Subtotal: {storeDataSingle.formattedTotalCost}
                  </span>
                </div>
                <a
                  href={buildVTEXCartLink(storeDataSingle.items)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-sm btn-outline btn-primary w-full"
                >
                  Ir ao Carrinho do Mercado {storeDataSingle.storeName[0].toUpperCase()}
                </a>
              </div>
            </div>
          )}
        </>
      ),
    },
    {
      id: "slide2",
      content: (
        <>
          <InfoLabelMobile text="💸 Melhor preço por item, escolhendo o melhor de cada mercado" color="accent" />
          {loading && <span className="text-sm">Carregando...</span>}
          {error && <span className="text-sm text-error">{error}</span>}
          {storeDataSplit.length > 0 && (
            <>
              {storeDataSplit.map((store, i) => (
                <div key={i} className="mb-6 rounded-xl border border-base-300 bg-base-200 p-4 shadow-sm">
                  <div className="flex justify-between items-center mb-4">
                    <div className="flex items-center gap-2">
                      <div className="h-3 w-3 rounded-full bg-primary"></div>
                      <h2 className="text-lg font-bold capitalize">
                        Mercado {store.storeName[0].toUpperCase()}
                      </h2>
                    </div>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="table table-sm">
                      <thead>
                        <tr>
                          <th>Produto</th>
                          <th>Preço Unit.</th>
                          <th>Qtd</th>
                          <th className="text-right">Preço Total</th>
                        </tr>
                      </thead>
                      <tbody>
                        {store.items.map((item, idx) => (
                          <tr key={idx}>
                            <td>{item.name}</td>
                            <td className="text-center">{item.formattedPrice}</td>
                            <td className="text-center">{item.quantity}</td>
                            <td className="text-right">{item.formattedTotalPrice}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div className="mt-12">
                    <div className="flex justify-end mb-3 pr-2">
                      <span className="text-md font-semibold">
                        Subtotal: {store.formattedTotalCost}
                      </span>
                    </div>
                    <a
                      href={buildVTEXCartLink(store.items)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn btn-sm btn-outline btn-primary w-full"
                    >
                      Ir ao carrinho do Mercado {store.storeName[0].toUpperCase()}
                    </a>
                  </div>
                </div>
              ))}
            </>
          )}
        </>
      ),
    },
    {
      id: "slide3",
      content: (
        <>
          <InfoLabelMobile text="🚗💸 Economize tempo e dinheiro num só mercado" color="accent" />
          {loading && <span className="text-sm">Carregando...</span>}
          {error && <span className="text-sm text-error">{error}</span>}
          {bestMarketCombined && (
            <div className="mb-6 rounded-xl border border-base-300 bg-base-200 p-4 shadow-sm">
              <div className="flex justify-between items-center mb-1">
                <div className="flex items-center gap-2">
                  <div className="h-3 w-3 rounded-full bg-success"></div>
                  <h2 className="text-lg font-bold capitalize">
                    Mercado {bestMarketCombined.storeName[0].toUpperCase()}
                  </h2>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="table table-sm">
                  <thead>
                    <tr>
                      <th>Produto</th>
                      <th>Preço Unit.</th>
                      <th>Qtd</th>
                      <th className="text-right">Preço Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {bestMarketCombined.items.map((item, index) => (
                      <tr key={index}>
                        <td>{item.name}</td>
                        <td className="text-center">{item.formattedPrice}</td>
                        <td className="text-center">{item.quantity}</td>
                        <td className="text-right">{item.formattedTotalPrice}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="mt-8 flex justify-between text-sm text-gray">
                <span>{bestMarketCombined.distanceKm.toFixed(2)} km até o destino</span>
                <span>{bestMarketCombined.durationMin} min de trajeto</span>
              </div>

              <div className="mt-12">
                <div className="flex justify-end mb-3 pr-2">
                  <span className="text-md font-semibold">
                    Subtotal: {bestMarketCombined.formattedTotalPrice}
                  </span>
                </div>

                <a
                  href={buildVTEXCartLink(bestMarketCombined.items)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-sm btn-outline btn-primary w-full"
                >
                  Ir ao Carrinho do Mercado {bestMarketCombined.storeName[0].toUpperCase()}
                </a>
              </div>
            </div>
          )}
        </>
      ),
    },
    {
      id: "slide4",
      content: (
        <>
          <InfoLabelMobile text="🏅 Ranking de mercados: menor preço, custo, distância e tempo" color="success" />
          {loading && <span className="text-sm">Carregando...</span>}
          {error && <span className="text-sm text-error">{error}</span>}
          {bestMarkets && bestMarkets.length > 0 && (
            <>
              {bestMarkets.map((market: any, idx: number) => (
                <div key={idx} className="mb-6 rounded-xl border border-base-300 bg-base-200 p-4 shadow-sm">
                  <div className="flex justify-between items-center mb-4">
                    <div className="flex items-center gap-2">
                      <div className="h-3 w-3 rounded-full bg-accent"></div>
                      <h2 className="text-lg font-bold capitalize">
                        Mercado {market.storeName[0].toUpperCase()}
                      </h2>
                    </div>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="table table-sm">
                      <thead>
                        <tr>
                          <th>Produto</th>
                          <th>Preço Unit.</th>
                          <th>Qtd</th>
                          <th className="text-right">Preço Total</th>
                        </tr>
                      </thead>
                      <tbody>
                        {market.items.map((item: any, i: number) => (
                          <tr key={i}>
                            <td>{item.name}</td>
                            <td className="text-center">{item.formattedPrice}</td>
                            <td className="text-center">{item.quantity}</td>
                            <td className="text-right">{item.formattedTotalPrice}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div className="mt-6 flex justify-between text-sm text-gray-600">
                    <span>{market.distanceKm.toFixed(2)} km até o destino</span>
                    <span>Tempo: {market.durationMin} min de trajeto</span>
                  </div>

                  <div className="mt-8">
                    <div className="flex justify-end mb-2 pr-2">
                      <span className="text-md font-semibold">
                        Subtotal: {market.formattedTotalPrice}
                      </span>
                    </div>
                    <a
                      href={buildVTEXCartLink(market.items)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn btn-sm btn-outline btn-primary w-full"
                    >
                      Ir ao carrinho do Mercado {market.storeName[0].toUpperCase()}
                    </a>
                  </div>
                </div>
              ))}
              <div className="mt-6 border-t border-base-300 pt-4 flex justify-between text-lg font-bold">
                <span>Custo total acumulado:</span>
                <span>
                  {new Intl.NumberFormat("pt-BR", {
                    style: "currency",
                    currency: "BRL",
                  }).format(
                    storeDataSplit.reduce((acc, store) => acc + store.totalCost, 0)
                  )}
                </span>
              </div>
            </>
          )}
        </>
      ),
    },
  ];

  return (
    <div className="relative w-full overflow-hidden">
      <div
        className="flex snap-x snap-mandatory overflow-x-auto scroll-smooth w-full"
        ref={carouselRef}
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
      >
        {slides.map((slide, idx) => (
          <div
            key={slide.id}
            className="carousel-item snap-start w-full flex-shrink-0 flex justify-center"
          >
            <div className="card w-full max-w-[525px] bg-primary shadow-md">
              <div className="overflow-y-auto p-4 pr-2 h-[700px]"> {/* Scroll vertical por slide */}
                <div className="card-body p-0">{slide.content}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
