export type OrderStatusCode =
  | "pending_payment"
  | "payment_approved"
  | "payment_rejected"
  | "in_preparation"
  | "shipped"
  | "delivered"
  | "cancelled";

export type PaymentMethodCode = "debit_card" | "pse";

export type PaymentStatusCode =
  "initiated" | "processing" | "action_required" | "approved" | "rejected" | "error";

export interface OrderItem {
  id: number;
  variant_id: number | null;
  product_name: string;
  color: string;
  size: string;
  unit_price: string;
  quantity: number;
  subtotal: string;
}

export interface OrderStatusHistoryEntry {
  from_status?: string;
  to_status?: string;
  to_status_label: string;
  note: string;
  created_at: string;
}

export interface OrderDetail {
  order_number: string;
  status: OrderStatusCode;
  status_label: string;
  subtotal: string;
  shipping_cost: string;
  total: string;
  municipality: string;
  address_line: string;
  recipient_name: string;
  phone: string;
  payment_expires_at?: string;
  created_at?: string;
  updated_at?: string;
  items?: OrderItem[];
  status_history: OrderStatusHistoryEntry[];
}

export interface OrderSummary {
  order_number: string;
  status: OrderStatusCode;
  status_label: string;
  total: string;
  created_at: string;
}

export interface PaymentInfo {
  method?: PaymentMethodCode;
  status?: PaymentStatusCode;
  status_label: string;
  status_detail?: string;
  amount?: string;
  redirect_url?: string;
  created_at?: string;
}

export interface PaymentResult {
  order: OrderDetail;
  payment: PaymentInfo | null;
}

export interface PseBank {
  id: string;
  description: string;
}

export interface CheckoutInput {
  municipality: string;
  address_line: string;
  recipient_name: string;
  phone: string;
}

export interface DebitPaymentInput {
  method: "debit_card";
  token: string;
  payment_method_id: string;
  payment_type?: string;
  first_name?: string;
  last_name?: string;
  identification_type?: string;
  identification_number?: string;
}

export interface PsePaymentInput {
  method: "pse";
  financial_institution: string;
  entity_type: "individual" | "association";
  first_name?: string;
  last_name?: string;
  identification_type: string;
  identification_number: string;
  phone_area_code: string;
  phone_number: string;
  zip_code: string;
  street_number: string;
  neighborhood: string;
}

export type StartPaymentInput = DebitPaymentInput | PsePaymentInput;
