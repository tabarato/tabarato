import React from 'react';
import { useLocation } from 'react-router-dom';

export default function ResultPage() {
  const location = useLocation();
  const { location: userLocation, cart } = location.state || {};

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Dados Recebidos</h1>

      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-2">Localização do Usuário:</h2>
        {userLocation ? (
          <pre className="bg-gray-100 p-4 rounded text-black">
            {JSON.stringify(userLocation, null, 2)}
          </pre>
        ) : (
          <p>Localização não disponível ou permissão negada.</p>
        )}
      </section>

      <section>
        <h2 className="text-xl font-semibold mb-2">Produtos Selecionados:</h2>
        {cart && cart.length > 0 ? (
          <pre className="bg-gray-100 p-4 rounded overflow-auto max-h-96 text-black">
            {JSON.stringify(cart, null, 2)}
          </pre>
        ) : (
          <p>Nenhum produto selecionado.</p>
        )}
      </section>
    </div>
  );
}
