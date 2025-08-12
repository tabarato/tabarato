import React, { createContext, useContext, useState, ReactNode } from 'react';

export interface Variation {
  productId: BigInteger;
  weight: number;
  measure: string;
  name: string;
  imageUrl: string;
  minPrice: number;
  maxPrice: number;
  stores: string[];
}

export interface CartItem extends Variation {
  quantity: number;
}

interface CartContextData {
  cart: CartItem[];
  addToCart: (item: Variation) => void;
  removeFromCart: (key: string) => void;
  updateQuantity: (key: string, quantity: number) => void;
  clearCart: () => void;
}

const CartContext = createContext<CartContextData | undefined>(undefined);

export function generateKey(item: Variation): string {
  return `${item.productId}-${item.name}-${item.weight}-${item.measure}`;
}

export function CartProvider({ children }: { children: ReactNode }) {
  const [cart, setCart] = useState<CartItem[]>([]);

  function addToCart(item: Variation) {

    const key = generateKey(item);

    setCart((prevCart) => {
      const index = prevCart.findIndex((ci) => generateKey(ci) === key);
      if (index >= 0) {
        const updated = [...prevCart];
        updated[index].quantity += 1;
        return updated;
      } else {
        return [...prevCart, { ...item, quantity: 1 }];
      }
    });
  }

  function updateQuantity(key: string, quantity: number) {
    setCart((prevCart) =>
      prevCart.map((item) =>
        generateKey(item) === key ? { ...item, quantity } : item
      )
    );
  }

  function removeFromCart(key: string) {
    setCart((prevCart) => prevCart.filter((item) => generateKey(item) !== key));
  }

  function clearCart() {
    setCart([]);
  }

  return (
    <CartContext.Provider value={{ cart, addToCart, removeFromCart, updateQuantity, clearCart }}>
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
}
