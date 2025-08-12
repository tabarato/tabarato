import React, { useState, useCallback } from 'react';
import axios from 'axios';
import debounce from 'lodash.debounce';
import { useCart, generateKey, Variation } from '../context/CartContext';
import { useNavigate } from 'react-router-dom';
import getEnvVar from '../utils/EnvironmentVariables';

const API_URL = getEnvVar("API_URL");

interface Product {
    id: string;
    brand: string;
    name: string;
    variations: Variation[];
}

export default function Home() {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<Product[]>([]);
    const [showStores, setShowStores] = useState(false);
    const [secretCount, setSecretCount] = useState(0);
    const { cart, addToCart, updateQuantity, removeFromCart } = useCart();
    const [isCartOpen, setIsCartOpen] = useState(false);
    const [showEmptyCartAlert, setShowEmptyCartAlert] = useState(false);
    const [selectedTransport, setSelectedTransport] = useState<string | null>(null);
    const [originAddress, setOriginAddress] = useState('');
    const [destinationAddress, setDestinationAddress] = useState('');
    const transportOptions: { label: string; value: string }[] = [
        { label: 'Bicicleta', value: 'BICYCLE' },
        { label: 'Carro', value: 'DRIVE' },
        { label: 'Motocicleta', value: 'TWO_WHEELER' },
        { label: 'Caminhando', value: 'WALK' },
    ];


    const navigate = useNavigate();

    const handleCheckout = () => {
        const products = cart.map((item) => ({
            id: item.id,
            quantity: item.quantity,
        }));

        const allStores = cart.flatMap(item => item.stores ?? []);
        const distinctStores = Array.from(new Set(allStores));

        navigate('/result', {
            state: {
                originAddress,
                destinationAddress,
                travelMode: selectedTransport,
                products,
                markets: distinctStores,
            },
        });
    };

    const search = async (searchText: string) => {
        if (!searchText.trim()) {
            setResults([]);
            return;
        }

        try {
            const response = await axios.get(API_URL + `/products?query=${searchText}`);
            const products: Product[] = response.data;
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
        <div className="min-h-screen bg-base-200 p-8">
            <div className="max-w-3xl mx-auto">
                <div className="flex items-center justify-between mb-6">
                    <input
                        type="text"
                        placeholder="Buscar produto..."
                        className="input input-bordered input-lg flex-grow mr-4"
                        value={query}
                        onChange={handleQueryChange}
                    />

                    <button
                        className="relative btn btn-primary"
                        onClick={() => {
                            if (cart.length === 0) {
                                setShowEmptyCartAlert(true);
                                setTimeout(() => setShowEmptyCartAlert(false), 3000);
                                return;
                            }
                            setIsCartOpen(true);
                        }}
                        aria-label="Abrir carrinho"
                    >
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            className="h-6 w-6"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                            strokeWidth={2}
                        >
                            <path strokeLinecap="round" strokeLinejoin="round" d="M3 3h2l.4 2M7 13h10l4-8H5.4" />
                            <circle cx="7" cy="21" r="2" />
                            <circle cx="17" cy="21" r="2" />
                        </svg>
                        {cart.length > 0 && (
                            <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white bg-red-600 rounded-full transform translate-x-1/2 -translate-y-1/2">
                                {cart.reduce((acc, item) => acc + item.quantity, 0)}
                            </span>
                        )}
                    </button>
                </div>

                {showEmptyCartAlert && (
                    <div className="toast toast-top toast-end z-50">
                        <div className="alert alert-warning">
                            <span>Seu carrinho está vazio.</span>
                        </div>
                    </div>
                )}

                <div className="grid gap-6">
                    {results.map((product) => (
                        <div
                            key={product.id}
                            className="card bg-white shadow-lg rounded-2xl mb-6 p-4"
                        >
                            <div>
                                <h2 className="card-title text-xl font-bold text-gray-900">{product.name}</h2>
                                <p className="text-sm text-gray-600 mb-3">Marca: {product.brand}</p>
                            </div>

                            {product.variations.map((variation, idx) => {
                                const priceDisplay =
                                    variation.minPrice === variation.maxPrice
                                        ? `R$${variation.minPrice.toFixed(2)}`
                                        : `R$${variation.minPrice.toFixed(2)} - R$${variation.maxPrice.toFixed(2)}`;

                                return (
                                    <div
                                        key={idx}
                                        className="mt-4 pt-4 border-t border-gray-300 flex gap-4"
                                    >
                                        {variation.imageUrl && (
                                            <img
                                                src={variation.imageUrl}
                                                alt={variation.name}
                                                className="w-24 h-24 object-contain rounded-xl"
                                            />
                                        )}
                                        <div className="flex-1">
                                            <p className="text-base font-medium text-gray-900">{variation.name}</p>
                                            <p className="text-sm text-gray-700">
                                                {variation.weight} {variation.measure}
                                            </p>
                                            <p className="text-base font-bold mt-1 text-gray-900">{priceDisplay}</p>

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
                                                className="mt-3 btn btn-sm btn-outline btn-primary"
                                            >
                                                Adicionar ao carrinho
                                            </button>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    ))}

                    {results.length === 0 && query && (
                        <div className="text-center text-gray-400">Nenhum produto encontrado.</div>
                    )}
                </div>

                {isCartOpen && (
                    <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50 text-black">
                        <div className="bg-white rounded-lg w-full max-w-3xl p-8 relative">
                            <button
                                onClick={() => setIsCartOpen(false)}
                                className="absolute top-3 right-3 btn btn-sm btn-circle"
                                aria-label="Fechar modal"
                            >
                                ✕
                            </button>

                            <h3 className="text-2xl font-bold mb-6">🛒 Seu Carrinho</h3>

                            <div className="mb-4">
                                <label className="label font-semibold" htmlFor="origin-address">Endereço de origem:</label>
                                <input
                                    id="origin-address"
                                    type="text"
                                    className="input input-bordered w-full text-white"
                                    placeholder="Ex: Rua das Flores, 123 - Centro"
                                    value={originAddress}
                                    onChange={(e) => setOriginAddress(e.target.value)}
                                />
                            </div>

                            <div className="mb-4">
                                <label className="label font-semibold" htmlFor="destination-address">Endereço de destino:</label>
                                <input
                                    id="destination-address"
                                    type="text"
                                    className="input input-bordered w-full text-white"
                                    placeholder="Ex: Av. Brasil, 456 - Bairro"
                                    value={destinationAddress}
                                    onChange={(e) => setDestinationAddress(e.target.value)}
                                />
                            </div>


                            <div className="mt-6 mb-6">
                                <h4 className="font-semibold mb-2">Escolha o meio de transporte:</h4>
                                <div className="flex flex-wrap gap-3">
                                    {transportOptions.map(({ label, value }) => (
                                        <button
                                            key={value}
                                            className={`btn btn-sm ${selectedTransport === value ? 'btn-primary' : 'btn-outline'}`}
                                            onClick={() => setSelectedTransport(value)}
                                            type="button"
                                        >
                                            {label}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {cart.length === 0 ? (
                                <p className="text-center text-gray-500">Seu carrinho está vazio.</p>
                            ) : (
                                <ul className="space-y-2 max-h-80 overflow-y-auto">
                                    {cart.map((item, index) => {
                                        const key = generateKey(item);
                                        return (
                                            <li key={index} className="flex items-center gap-2 border-b pb-2">
                                                {item.imageUrl && (
                                                    <img
                                                        src={item.imageUrl}
                                                        alt={item.name}
                                                        className="w-16 h-16 object-contain rounded"
                                                    />
                                                )}
                                                <div className="flex-1">
                                                    <p className="font-semibold">
                                                        {item.name} {item.weight}{item.measure}
                                                    </p>
                                                </div>
                                                <select
                                                    className="select select-bordered w-16 text-white"
                                                    value={item.quantity}
                                                    onChange={(e) =>
                                                        updateQuantity(key, Number(e.target.value))
                                                    }
                                                >
                                                    {[...Array(10)].map((_, i) => (
                                                        <option key={i + 1} value={i + 1}>
                                                            {i + 1}
                                                        </option>
                                                    ))}
                                                </select>

                                                <button
                                                    onClick={() => removeFromCart(key)}
                                                    className="btn btn-sm btn-error ml-2 w-16"
                                                    aria-label={`Remover ${item.name} do carrinho`}
                                                >
                                                    Remover
                                                </button>
                                            </li>
                                        );
                                    })}
                                </ul>
                            )}

                            <button
                                onClick={handleCheckout}
                                className={`btn mt-6 w-full ${selectedTransport && originAddress.trim() && destinationAddress.trim()
                                    ? 'btn-primary'
                                    : 'btn-disabled cursor-not-allowed'
                                    }`}
                                disabled={!selectedTransport || !originAddress.trim() || !destinationAddress.trim()}
                            >
                                Obter resultados
                            </button>
                        </div>
                    </div>
                )}


            </div>
        </div>
    );
}
