import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/shared/api/client";
import { env } from "@/shared/lib/env";
import type { CatalogProduct } from "./types";

export const catalogProductsKey = ["catalog", "products"] as const;
export const catalogProductDetailKey = (slug: string) => ["catalog", "product", slug] as const;

/** Resuelve URLs relativas de medios (`/media/...`) contra `VITE_API_URL`. */
export function resolveCatalogImageUrl(url: string | null | undefined): string | null {
  if (!url) return null;
  if (/^https?:\/\//i.test(url)) return url;
  return `${env.apiUrl}${url.startsWith("/") ? "" : "/"}${url}`;
}

/** Determina si una prenda tiene descuento válido (`previous_price > price`). */
export function hasValidDiscount(
  price: string | number,
  previousPrice: string | number | null | undefined,
): boolean {
  if (previousPrice === null || previousPrice === undefined || String(previousPrice).trim() === "")
    return false;
  const current = Number(price);
  const previous = Number(previousPrice);
  return Number.isFinite(current) && Number.isFinite(previous) && previous > current;
}

/** Determina si una prenda publicada tiene stock disponible en alguna de sus variantes. */
export function isProductInStock(product: CatalogProduct): boolean {
  if (typeof product.in_stock === "boolean") return product.in_stock;
  if (Array.isArray(product.variants) && product.variants.length > 0) {
    return product.variants.some((v) => v.stock_quantity > 0);
  }
  return false;
}

/** Filtra únicamente prendas publicadas con variantes publicadas y sin duplicados (HU-1). */
export function filterPublishedCatalogProducts(products: CatalogProduct[]): CatalogProduct[] {
  const seen = new Set<number | string>();
  const result: CatalogProduct[] = [];
  for (const product of products) {
    if (product.status && product.status !== "published") continue;
    if (Array.isArray(product.variants) && product.variants.length === 0) continue;
    const key = product.id ?? product.slug;
    if (seen.has(key)) continue;
    seen.add(key);
    result.push(product);
  }
  return result;
}

export function useCatalogProducts() {
  return useQuery({
    queryKey: catalogProductsKey,
    queryFn: () => apiFetch<CatalogProduct[]>("/products"),
  });
}

export function useCatalogProductDetail(slug: string) {
  return useQuery({
    queryKey: catalogProductDetailKey(slug),
    queryFn: () => apiFetch<CatalogProduct>(`/products/${encodeURIComponent(slug)}`),
    enabled: Boolean(slug),
  });
}
