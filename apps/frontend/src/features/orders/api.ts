import { useAuth } from "@clerk/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError } from "@/shared/api/client";
import { useApi } from "@/shared/api/useApi";
import type {
  CheckoutInput,
  OrderDetail,
  OrderSummary,
  PaymentInfo,
  PaymentResult,
  PseBank,
  StartPaymentInput,
} from "./types";

/** Genera una clave única por intento de pago para enviarla en X-Idempotency-Key. */
export function createIdempotencyKey(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `idemp-${Date.now()}-${Math.random().toString(16).slice(2, 10)}`;
}

/** Traduce cualquier código de error de checkout/pagos a un mensaje claro en español (HU-60). */
export function formatPaymentErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    switch (error.code) {
      case "only_debit_allowed":
        return "Solo se aceptan tarjetas débito. Intenta con una tarjeta débito Visa o Mastercard.";
      case "payment_already_in_progress":
        return "Este pedido ya tiene un pago en curso o aprobado. No se generó un segundo cobro.";
      case "payment_window_expired":
        return "El tiempo de 30 minutos para pagar este pedido terminó. Vuelve a hacer tu pedido.";
      case "order_not_payable":
        return error.message || "Este pedido ya no se puede pagar.";
      case "payment_gateway_unavailable":
        return "No pudimos comunicarnos con el servicio de pagos. Tu pedido sigue Pendiente de Pago; intenta de nuevo en unos minutos.";
      case "payment_gateway_not_configured":
        return "Los pagos en línea no están disponibles en este momento. Intenta más tarde.";
      case "payment_request_invalid":
        return "No pudimos procesar los datos del pago. Revísalos e intenta de nuevo.";
      case "municipality_not_covered":
        return "Solo enviamos a Cali, Palmira, Jamundí y Yumbo.";
      case "empty_cart":
        return "Tu carrito está vacío. Agrega productos antes de pagar.";
      case "out_of_stock":
      case "reservation_expired":
        return (
          error.message ||
          "Una o más reservas de tu carrito expiraron o ya no tienen stock disponible."
        );
      case "network_error":
        return "No pudimos conectar con el servidor. Revisa tu conexión e intenta de nuevo.";
      default:
        return error.message || "No se pudo procesar la solicitud. Intenta de nuevo.";
    }
  }
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return "Ocurrió un error inesperado al procesar el pago. Intenta de nuevo.";
}

/** Sanea notas internas de MercadoPago en el historial para no exponer códigos técnicos en inglés (HU-23, HU-60). */
export function sanitizeHistoryNote(note: string): string {
  const trimmed = (note ?? "").trim();
  if (!trimmed) return "";
  if (/^MercadoPago:/i.test(trimmed)) {
    const lower = trimmed.toLowerCase();
    if (lower.includes("processed") || lower.includes("accredited")) {
      return "Confirmación recibida de la pasarela de pagos.";
    }
    if (
      lower.includes("failed") ||
      lower.includes("rejected") ||
      lower.includes("canceled") ||
      lower.includes("cancelled") ||
      lower.includes("expired")
    ) {
      return "Pago rechazado por la entidad financiera o la pasarela.";
    }
    return "Actualización recibida de la pasarela de pagos.";
  }
  return trimmed;
}

/** Determina la causa de cancelación del pedido para diferenciar HU-23 (rechazo) de HU-24 (30 min). */
export function getCancellationReason(
  order: OrderDetail,
  payment: PaymentInfo | null,
): "rejected" | "timeout" | "other" {
  const history = order.status_history ?? [];
  const hasRejectedStep = history.some(
    (entry) =>
      entry.to_status === "payment_rejected" ||
      entry.to_status_label.toLowerCase().includes("rechazado") ||
      entry.note.toLowerCase().includes("pago rechazado"),
  );
  if (hasRejectedStep || payment?.status === "rejected") {
    return "rejected";
  }
  const hasTimeoutNote = history.some(
    (entry) =>
      entry.note.toLowerCase().includes("30 minutos") ||
      entry.note.toLowerCase().includes("sin respuesta"),
  );
  if (hasTimeoutNote) {
    return "timeout";
  }
  if (order.payment_expires_at && new Date(order.payment_expires_at).getTime() <= Date.now()) {
    return "timeout";
  }
  return "other";
}

export function usePseBanks(enabled = true) {
  const api = useApi();
  return useQuery({
    queryKey: ["pse-banks"],
    queryFn: () => api<PseBank[]>("/payments/pse-banks"),
    enabled,
    staleTime: 30 * 60 * 1000,
  });
}

export function useCreateCheckoutOrder() {
  const api = useApi();
  const client = useQueryClient();
  return useMutation({
    mutationFn: (input: CheckoutInput) =>
      api<OrderDetail>("/checkout", { method: "POST", json: input }),
    onSuccess: (order) => {
      client.setQueryData<PaymentResult>(["order-payment", order.order_number], {
        order,
        payment: null,
      });
      void client.invalidateQueries({ queryKey: ["cart"] });
      void client.invalidateQueries({ queryKey: ["orders"] });
      void client.invalidateQueries({ queryKey: ["catalog"] });
    },
  });
}

export function useStartOrderPayment() {
  const api = useApi();
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({
      orderNumber,
      payload,
      idempotencyKey = createIdempotencyKey(),
    }: {
      orderNumber: string;
      payload: StartPaymentInput;
      idempotencyKey?: string;
    }) =>
      api<PaymentResult>(`/orders/${encodeURIComponent(orderNumber)}/payments`, {
        method: "POST",
        headers: { "X-Idempotency-Key": idempotencyKey },
        json: payload,
      }),
    onSuccess: (result) => {
      client.setQueryData<PaymentResult>(["order-payment", result.order.order_number], result);
      void client.invalidateQueries({ queryKey: ["orders"] });
      void client.invalidateQueries({ queryKey: ["catalog"] });
    },
  });
}

export function useSyncOrderPayment(orderNumber: string) {
  const api = useApi();
  return useQuery({
    queryKey: ["order-payment", orderNumber],
    queryFn: () =>
      api<PaymentResult>(`/orders/${encodeURIComponent(orderNumber)}/payments/sync`, {
        method: "POST",
      }),
    enabled: Boolean(orderNumber),
    staleTime: 2_000,
  });
}

export function useCustomerOrders() {
  const api = useApi();
  const { isLoaded, isSignedIn, userId } = useAuth();
  return useQuery({
    queryKey: ["orders", userId],
    queryFn: () => api<OrderSummary[]>("/orders"),
    enabled: isLoaded && Boolean(isSignedIn),
  });
}
