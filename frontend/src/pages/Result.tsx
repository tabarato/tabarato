import { useEffect, useState } from "react";
import { useLocation } from 'react-router-dom';
import {
  findLowestCostSingleMarket,
  findLowestCostAcrossMarkets,
  StoreResult,
  StoreResultDistanceTime,
  findBestMarketByCostDistanceTime,
  findMarketsByCostDistanceTime,
  findMarketsRoutes
} from "../service/resultSearchStrategies";

import InfoLabel from "../utils/InfoLabel";

export default function ResultPage() {
  const [storeDataSingle, setStoreDataSingle] = useState<StoreResult | null>(null);
  const [storeDataSplit, setStoreDataSplit] = useState<StoreResult[]>([]);
  const [bestMarketCombined, setBestMarketCombined] = useState<StoreResultDistanceTime | null>(null);
  const [bestMarkets, setBestMarkets] = useState<StoreResultDistanceTime[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const location = useLocation();
  const { originAddress, destinationAddress, travelMode, products, markets } = location.state || {};

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

  function buildVTEXCartLink(items: { cartLink: string }[]): string {
    if (items.length === 0) return "#";

    const baseUrl = new URL(items[0].cartLink);
    const params = new URLSearchParams();

    items.forEach(item => {
      const url = new URL(item.cartLink);
      url.searchParams.forEach((value, key) => {
        params.append(key, value);
      });
    });

    return `${baseUrl.origin}${baseUrl.pathname}?${params.toString()}`;
  }

  
  const tableClasses = "table table-sm";

  const cardClasses = "w-full max-w-3xl bg-base-100 border border-base-300 shadow-xl rounded-xl p-6 pb-8";

  const slideNavClasses = "flex px-6 mt-6 z-10 pointer-events-none";

  const navButtonClasses = `
    btn btn-circle pointer-events-auto mx-2
  `;

  return (
    <div className="flex min-h-screen w-full items-center justify-center bg-primary">
      <div className="carousel w-full max-w-7xl pt-10">
        {/* Slide 1 */}
        <div id="slide1" className="carousel-item relative w-full flex flex-col items-center justify-start">
          <div className={cardClasses}>
            <InfoLabel text="🏆 Menor custo total num único mercado com todos os produtos" color="accent" />

            {loading && <span className="text-sm">Carregando...</span>}
            {error && <span className="text-sm text-error">{error}</span>}

            {storeDataSingle && (
              <>
                <div className="mt-4 rounded-xl border border-base-300 bg-base-200 p-4 shadow-sm/20">
                  <div className="flex justify-between items-center mb-4">
                    <div className="flex items-center gap-2">
                      <div className="h-3 w-3 rounded-full bg-warning"></div>
                      <h2 className="text-lg font-bold capitalize">
                        Mercado {storeDataSingle.storeName[0].toUpperCase()}
                      </h2>
                    </div>
                  </div>

                  <div className="overflow-x-auto">
                    <table className={tableClasses}>
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
                  <div className="flex justify-end mt-8 pr-2">
                    <span className="text-md font-semibold">
                      Subtotal: {storeDataSingle.formattedTotalCost}
                    </span>
                  </div>

                  <div className="mt-6">
                    <a
                      href={buildVTEXCartLink(storeDataSingle.items)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="btn btn-primary btn-outline w-full"
                    >
                      Ir ao Carrinho do Mercado {storeDataSingle.storeName[0].toUpperCase()}
                    </a>
                  </div>
                </div>
              </>
            )}
          </div>

          <div className={slideNavClasses}>
            <a href="#slide4" className={navButtonClasses}>❮</a>
            <a href="#slide2" className={navButtonClasses}>❯</a>
          </div>
        </div>

        {/* Slide 2 */}
        <div id="slide2" className="carousel-item relative w-full flex flex-col items-center justify-start">
          <div className="flex w-full gap-4 overflow-x-auto px-6 pb-4">
            {storeDataSplit.length > 0 && storeDataSplit.map((store, i) => (
              <div key={i} className={cardClasses + " min-w-[380px] flex flex-col justify-between"}>
                <div>
                  <InfoLabel text="💸 Menor preço por item, escolhendo o melhor de cada mercado" color="accent" />
                  <div className="flex justify-between items-center mb-4 mt-2">
                    <div className="flex items-center gap-2">
                      <div className="h-3 w-3 rounded-full bg-primary"></div>
                        <h2 className="text-lg font-bold capitalize">
                          Mercado {store.storeName[0].toUpperCase()}
                        </h2>
                    </div>
                  </div>

                  <div className="overflow-x-auto">
                    <table className={tableClasses}>
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
                </div>
                <div className="mt-6">
                  <div className="flex justify-end mb-6 pr-2">
                    <span className="text-md font-semibold">
                      Subtotal: {store.formattedTotalCost}
                    </span>
                  </div>
                  <a
                    href={buildVTEXCartLink(store.items)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn btn-primary btn-outline w-full"
                  >
                    Ir ao carrinho
                  </a>
                </div>
              </div>
            ))}
          </div>

          <div className={slideNavClasses}>
            <a href="#slide1" className={navButtonClasses}>❮</a>
            <a href="#slide3" className={navButtonClasses}>❯</a>
          </div>
        </div>

        {/* Slide 3 */}
        <div id="slide3" className="carousel-item relative w-full flex flex-col items-center justify-start">
          <div className={cardClasses}>
            <InfoLabel text="🚗💸 Economize tempo e dinheiro num só mercado" color="accent" />
            {bestMarketCombined && (
              <div className="rounded-xl border border-base-300 bg-base-200 p-4 shadow-md">
                <div className="flex justify-between items-center mb-1">
                  <div className="flex items-center gap-2">
                    <div className="h-3 w-3 rounded-full bg-success"></div>
                    <h2 className="text-lg font-bold capitalize">
                      Mercado {bestMarketCombined.storeName[0].toUpperCase()}
                    </h2>
                  </div>
                </div>

                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-2">
                    <div className="h-3 w-3 rounded-full"></div>
                    <span className="text-sm">
                      {bestMarketCombined.distanceInfo.distanceKm.toFixed(2)} km até o destino
                    </span>
                  </div>
                </div>

                <div className="flex justify-between items-center mb-4">
                  <div className="flex items-center gap-2">
                    <div className="h-3 w-3 rounded-full"></div>
                    <span className="text-sm">
                      {bestMarketCombined.distanceInfo.durationMin} min de trajeto
                    </span>
                  </div>
                </div>

                <div className="overflow-x-auto">
                  <table className={tableClasses}>
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

                <div className="mt-6">
                  <div className="flex justify-end mb-6 pr-2">
                    <span className="text-md font-semibold">
                      Subtotal: {bestMarketCombined.formattedTotalCost}
                    </span>
                  </div>
                  <a
                    href={buildVTEXCartLink(bestMarketCombined.items)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn btn-primary btn-outline w-full"
                  >
                    Ir ao Carrinho
                  </a>
                </div>
              </div>
            )}
          </div>

          <div className={slideNavClasses}>
            <a href="#slide2" className={navButtonClasses}>❮</a>
            <a href="#slide4" className={navButtonClasses}>❯</a>
          </div>
        </div>

        {/* Slide 4 */}
        <div id="slide4" className="carousel-item relative w-full flex flex-col items-center justify-start">
          <div className="flex w-full gap-4 overflow-x-auto px-6 pb-4">
            {bestMarkets && bestMarkets.map((market: StoreResultDistanceTime, idx: number) => (
              <div key={idx} className={cardClasses + " min-w-[380px] flex flex-col justify-between"}>
                <div>
                  <InfoLabel text="🏅 Ranking de mercados: menor preço, custo, distância e tempo" color="success" />
                  <div className="flex justify-between items-center mb-1 mt-2">
                    <div className="flex items-center gap-2">
                      <div className="h-3 w-3 rounded-full bg-accent"></div>
                      <h2 className="text-lg font-bold capitalize">
                        Mercado {market.storeName[0].toUpperCase()}
                      </h2>
                    </div>
                  </div>

                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2">
                      <div className="h-3 w-3 rounded-full"></div>
                      <span className="text-sm">
                        {market.distanceInfo.distanceKm.toFixed(2)} km até o destino
                      </span>
                    </div>
                  </div>

                  <div className="flex justify-between items-center mb-4">
                    <div className="flex items-center gap-2">
                      <div className="h-3 w-3 rounded-full"></div>
                      <span className="text-sm">
                        {market.distanceInfo.durationMin} min de trajeto
                      </span>
                    </div>
                  </div>


                  <div className="overflow-x-auto">
                    <table className={tableClasses}>
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

                </div>

                <div className="mt-6">
                  <div className="flex justify-end mb-6 pr-2">
                    <span className="text-md font-semibold">
                      Subtotal: {market.formattedTotalPrice}
                    </span>
                  </div>
                  <a
                    href={buildVTEXCartLink(market.items)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn btn-primary btn-outline w-full"
                  >
                    Ir ao Carrinho
                  </a>
                </div>
              </div>
            ))}
          </div>

          <div className={slideNavClasses}>
            <a href="#slide3" className={navButtonClasses}>❮</a>
            <a href="#slide1" className={navButtonClasses}>❯</a>
          </div>
        </div>
      </div>
    </div>
  );
}
