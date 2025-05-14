import React, { useState, useCallback } from 'react';
import axios from 'axios';
import debounce from 'lodash.debounce';
import { useCart } from '../context/CartContext';

interface Variation {
  weight: number;
  measure: string;
  name: string;
  image_url: string;
  min_price: number;
  max_price: number;
  stores: string[];
}

interface Product {
  id: string;
  brand: string;
  name: string;
  variations: Variation[];
}

export default function TabOneScreen() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Product[]>([]);
  const [showStores, setShowStores] = useState(false);
  const [secretCount, setSecretCount] = useState(0);
  const { cart, addToCart } = useCart();

  const handleSecretTap = () => {
    setSecretCount(prev => {
      const next = prev + 1;
      if (next >= 5) setShowStores(true);
      return next;
    });
  };

  const search = async (searchText: string) => {
    if (!searchText.trim()) {
      setResults([]);
      return;
    }

    try {
      const response = await axios.post('http://localhost:9200/products/_search', {
        query: {
          bool: {
            must: {
              multi_match: {
                query: searchText,
                type: 'most_fields',
                fields: ['name^3', 'brand']
              }
            }
          }
        }
      });

      const hits = response.data.hits.hits;
      const products = hits.map((hit: any) => ({
        id: hit._id,
        ...hit._source
      }));
      setResults(products);
    } catch (error) {
      console.error('Erro ao buscar:', error);
    }
  };

  const debouncedSearch = useCallback(debounce(search, 500), []);
  const handleQueryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const text = e.target.value;
    setQuery(text);
    debouncedSearch(text);
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <p
        onClick={handleSecretTap}
        className="text-center mb-4 text-gray-500 cursor-pointer hover:text-gray-700"
      >
        🛠️ Dev Mode
      </p>

      <input
        type="text"
        placeholder="Buscar produto"
        value={query}
        onChange={handleQueryChange}
        className="w-full px-4 py-2 mb-6 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      />

      {results.map(product => (
        <div
          key={product.id}
          className="bg-white rounded-xl shadow mb-6 p-4"
        >
          <div className="mb-2">
            <h3 className="text-lg font-semibold">{product.name}</h3>
            <p className="text-sm text-gray-500">Marca: {product.brand}</p>
          </div>

          {product.variations.map((variation, index) => {
            const priceDisplay =
              variation.min_price === variation.max_price
                ? `R$${variation.min_price.toFixed(2)}`
                : `R$${variation.min_price.toFixed(2)} - R$${variation.max_price.toFixed(2)}`;

            return (
              <div
                key={index}
                className="mt-4 pt-4 border-t border-gray-200"
              >
                <div className="flex gap-4">
                  {variation.image_url && (
                    <img
                      src={variation.image_url}
                      alt={variation.name}
                      className="w-24 h-24 object-contain rounded-lg"
                    />
                  )}
                  <div className="flex-1">
                    <p className="text-base font-medium">{variation.name}</p>
                    <p className="text-sm text-gray-500">
                      {variation.weight} {variation.measure}
                    </p>
                    <p className="text-base font-bold mt-1">{priceDisplay}</p>

                    {showStores && (
                      <div className="flex overflow-x-auto gap-2 mt-3">
                        {variation.stores.map((store, idx) => (
                          <div
                            key={idx}
                            className="bg-blue-50 text-blue-700 text-sm font-semibold px-3 py-1 rounded-full whitespace-nowrap"
                          >
                            🏬 {store}
                          </div>
                        ))}
                      </div>
                    )}

                    <button
                      onClick={() => addToCart(variation)}
                      className="mt-3 px-4 py-2 bg-blue-100 hover:bg-blue-200 text-blue-700 font-medium rounded-md"
                    >
                      Adicionar ao carrinho
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ))}

      {cart.length > 0 && (
        <div className="bg-white rounded-xl shadow mt-10 p-4">
          <h4 className="text-lg font-semibold mb-2">🛒 Shopping List</h4>
          <ul className="space-y-1">
            {cart.map((item, index) => (
              <li key={index}>
                • {item.name} – R${item.min_price.toFixed(2)}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
