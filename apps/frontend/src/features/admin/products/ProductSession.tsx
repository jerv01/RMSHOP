import { createContext, useContext, useState, type ReactNode } from "react";
import type { Product } from "./types";

const SessionContext = createContext<{
  products: Product[];
  remember: (product: Product, created?: boolean) => void;
}>({ products: [], remember: () => {} });

// Solo memoria de esta sesión: no representa un listado del catálogo ni persiste tokens.
export function ProductSessionProvider({ children }: { children: ReactNode }) {
  const [products, setProducts] = useState<Product[]>([]);
  function remember(product: Product, created = false) {
    setProducts((current) =>
      created || current.some((item) => item.id === product.id)
        ? [product, ...current.filter((item) => item.id !== product.id)]
        : current,
    );
  }
  return (
    <SessionContext.Provider value={{ products, remember }}>{children}</SessionContext.Provider>
  );
}
export const useProductSession = () => useContext(SessionContext);
