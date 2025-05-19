import { useEffect, useState } from "react";
import { useLocation } from 'react-router-dom';
import {
  findLowestCostSingleMarket,
  findLowestCostAcrossMarkets,
  StoreResult,
  findBestMarketByCostDistanceTime, findMarketsRoutes
} from "../service/resultSearchStrategies";

export default function ResultPage() {
  const [storeDataSingle, setStoreDataSingle] = useState<StoreResult | null>(null);
  const [storeDataSplit, setStoreDataSplit] = useState<StoreResult[]>([]);
  const [bestMarketCombined, setBestMarketCombined] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const location = useLocation();
  const { originAddress, destinationAddress, travelMode, products, markets } = location.state || {};
  const { marketAddresses, marketLoading, marketError } = findMarketsRoutes(originAddress, destinationAddress, markets, travelMode);
  const cartProductsId = products?.map(item => item.product_id) || [];

  useEffect(() => {
    async function fetchData() {
      try {
        const single = await findLowestCostSingleMarket(cartProductsId);
        setStoreDataSingle(single[0]);

        const split = await findLowestCostAcrossMarkets(cartProductsId);
        setStoreDataSplit(split);

        if (marketAddresses) {
          const bestMarket = await findBestMarketByCostDistanceTime(cartProductsId, marketAddresses);
          console.log(bestMarket)
          setBestMarketCombined(bestMarket);
        }
      } catch (err: any) {
        setError(err.message || "Erro ao buscar dados.");
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, [marketAddresses]);

  return (
    <div className="carousel w-full">
      {/* Slide 1 - Apenas o menor custo sem considerar a localização num único mercado */}
      <div id="slide1" className="carousel-item relative w-full justify-center">
        <div className="card w-96 bg-base-100 shadow-sm">
          <div className="card-body">
            <span className="badge badge-xs badge-warning">Apenas o menor custo sem considerar a localização</span>
            {loading && <span className="text-sm">Carregando...</span>}
            {error && <span className="text-sm text-error">{error}</span>}
            {storeDataSingle && (
              <>
                <div className="flex justify-between">
                  <h2 className="text-xl font-bold">
                    {storeDataSingle.store_name}
                  </h2>
                  <span className="text-xl font-semibold">
                    {storeDataSingle.formattedTotalPrice}
                  </span>
                </div>
                <ul className="mt-4 flex flex-col gap-2 text-sm">
                  {storeDataSingle.buy_list.map((item, index) => (
                    <li key={index} className="flex justify-between">
                      <span>{item.name}</span>
                      <span>{item.formattedPrice}</span>
                    </li>
                  ))}
                </ul>
                <div className="mt-6">
                  <a
                    href={storeDataSingle.buy_list[0]?.cart_link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn btn-primary btn-block"
                  >
                    Ir ao Carrinho
                  </a>
                </div>
              </>
            )}
          </div>
        </div>
        <div className="absolute left-5 right-5 top-1/2 flex -translate-y-1/2 transform justify-between">
          <a href="#slide3" className="btn btn-circle">❮</a>
          <a href="#slide2" className="btn btn-circle">❯</a>
        </div>
      </div>

      {/* Slide 2 - Divisão de produtos entre mercados */}
      <div id="slide2" className="carousel-item relative w-full justify-center">
        <div className="card w-96 bg-base-100 shadow-sm">
          <div className="card-body">
            <span className="badge badge-xs badge-info">Divisão entre mercados</span>
            {loading && <span className="text-sm">Carregando...</span>}
            {error && <span className="text-sm text-error">{error}</span>}
            {storeDataSplit.length > 0 && (
              <>
                {storeDataSplit.map((store, i) => (
                  <div key={i} className="mb-4 border-b pb-2">
                    <div className="flex justify-between items-center">
                      <h2 className="font-semibold text-base capitalize">
                        {store.store_name}
                      </h2>
                      <span className="font-medium">{store.formattedTotalPrice}</span>
                    </div>
                    <ul className="mt-2 flex flex-col gap-1 text-sm">
                      {store.buy_list.map((item, idx) => (
                        <li key={idx} className="flex justify-between">
                          <span>{item.name}</span>
                          <span>{item.formattedPrice}</span>
                        </li>
                      ))}
                    </ul>
                    <div className="mt-2">
                      <a
                        href={store.buy_list[0].cart_link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn btn-sm btn-outline btn-primary w-full"
                      >
                        Comprar no {store.store_name}
                      </a>
                    </div>
                  </div>
                ))}
              </>
            )}
          </div>
        </div>
        <div className="absolute left-5 right-5 top-1/2 flex -translate-y-1/2 transform justify-between">
          <a href="#slide1" className="btn btn-circle">❮</a>
          <a href="#slide3" className="btn btn-circle">❯</a>
        </div>
      </div>

      {/* Slide 3 - Melhor mercado por custo, distância e tempo */}
      <div id="slide3" className="carousel-item relative w-full justify-center">
        <div className="card w-96 bg-base-100 shadow-sm">
          <div className="card-body">
            <span className="badge badge-xs badge-success">Melhor por custo + distância + tempo</span>
            {loading && <span className="text-sm">Carregando...</span>}
            {error && <span className="text-sm text-error">{error}</span>}
            {bestMarketCombined && (
              <>
                <div className="flex justify-between">
                  <h2 className="text-xl font-bold">
                    {bestMarketCombined.store_name}
                  </h2>
                  <span className="text-xl font-semibold">
                    {bestMarketCombined.formattedTotalPrice}
                  </span>
                </div>
                <ul className="mt-4 flex flex-col gap-2 text-sm">
                  {bestMarketCombined.buy_list.map((item, index) => (
                    <li key={index} className="flex justify-between">
                      <span>{item.name}</span>
                      <span>{item.formattedPrice}</span>
                    </li>
                  ))}
                </ul>
                {/* Informações de distância e duração */}
                <div className="mt-4 text-sm text-gray-600 flex justify-between">
                  <span>Distância: {bestMarketCombined.distance_km.toFixed(2)} km</span>
                  <span>Duração: {bestMarketCombined.duration_min} min</span>
                </div>
                <div className="mt-6">
                  <a
                    href={bestMarketCombined.buy_list[0]?.cart_link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn btn-primary btn-block"
                  >
                    Ir ao Carrinho
                  </a>
                </div>
              </>
            )}
          </div>
        </div>
        <div className="absolute left-5 right-5 top-1/2 flex -translate-y-1/2 transform justify-between">
          <a href="#slide2" className="btn btn-circle">❮</a>
          <a href="#slide1" className="btn btn-circle">❯</a>
        </div>
      </div>
    </div>
  );
}
