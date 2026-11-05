export type ProductStatus = "draft" | "published" | "archived";
export interface Category {
  id: number;
  name: string;
  slug: string;
}
export interface Product {
  id: number;
  name: string;
  slug: string;
  description: string;
  price: string;
  previous_price: string | null;
  material: string;
  category: Category;
  status: ProductStatus;
  created_at: string;
  updated_at: string;
  warning?: string | null;
}
export interface ProductInput {
  name: string;
  description: string;
  price: string;
  previous_price?: string;
  material: string;
  category_id: number;
  status?: ProductStatus;
}
export interface ProductImage {
  id: number;
  product_id: number;
  image_url: string | null;
  alt_text: string;
  position: number;
  created_at: string;
}
export interface Variant {
  id: number;
  product_id: number;
  color: string;
  size: string;
  stock_quantity: number;
  created_at: string;
  updated_at: string;
}
export interface StockMovement {
  id: number;
  variant_id: number;
  delta: number;
  resulting_stock: number;
  reason: string;
  created_at: string;
  admin: { id: number; email: string; first_name: string; last_name: string } | null;
}
