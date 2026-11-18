export interface CartItem {
  id: number;
  variant_id: number;
  product_id: number;
  product_name: string;
  product_slug: string;
  color: string;
  size: string;
  unit_price: string;
  quantity: number;
  subtotal: string;
  reservation_expires_at: string | null;
  is_reservation_active: boolean;
  time_remaining_seconds: number | null;
  reservation_status: "active" | "expired" | "none";
  reservation_message: string | null;
}

export interface Cart {
  id: number;
  total_items: number;
  total_price: string;
  items: CartItem[];
}

export interface AddCartItemInput {
  variant_id: number;
  quantity: number;
}
