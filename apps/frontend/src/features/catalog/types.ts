import type {
  Category,
  ProductImage,
  ProductStatus,
  Variant,
} from "@/features/admin/products/types";

export interface CatalogProduct {
  id: number;
  name: string;
  slug: string;
  description: string;
  price: string;
  previous_price: string | null;
  material: string;
  design?: string | null;
  category: Category;
  status: ProductStatus;
  images?: ProductImage[];
  variants?: Variant[];
  in_stock?: boolean;
  is_new?: boolean;
  created_at: string;
  updated_at: string;
}

export interface CategoryFilterOption {
  label: string;
  slug: string | null;
}

export const CATALOG_CATEGORIES: readonly CategoryFilterOption[] = [
  { label: "Todos", slug: null },
  { label: "Camisetas / Tops", slug: "camisetas-tops" },
  { label: "Buzos / Sacos", slug: "buzos-sacos" },
  { label: "Pantalones / Jeans", slug: "pantalones-jeans" },
  { label: "Conjuntos", slug: "conjuntos" },
] as const;
