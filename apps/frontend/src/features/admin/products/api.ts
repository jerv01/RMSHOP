import { useAuth } from "@clerk/react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useApi } from "@/shared/api/useApi";
import type { Product, ProductImage, Variant, StockMovement } from "./types";

export function useAdminQuery<T>(path: string, enabled = true) {
  const { userId } = useAuth();
  const api = useApi();
  return useQuery({
    queryKey: ["admin", userId, path],
    queryFn: () => api<T>(path),
    enabled: Boolean(userId) && enabled,
  });
}
export function useAdminRefresh() {
  const { userId } = useAuth();
  const client = useQueryClient();
  return () => client.invalidateQueries({ queryKey: ["admin", userId] });
}
export const productPath = (id: number) => `/admin/products/${id}`;
export const useAdminProducts = (enabled = true) =>
  useAdminQuery<Product[]>("/admin/products", enabled);
export const useProduct = (id: number) => useAdminQuery<Product>(productPath(id), id > 0);
export const useImages = (id: number) =>
  useAdminQuery<ProductImage[]>(`${productPath(id)}/images`, id > 0);
export const useVariants = (id: number) =>
  useAdminQuery<Variant[]>(`${productPath(id)}/variants`, id > 0);
export const useMovements = (id: number) =>
  useAdminQuery<StockMovement[]>(`/admin/variants/${id}/stock-movements`, id > 0);
