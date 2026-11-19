import { useState } from "react";
import { Link, useParams } from "react-router";
import { PaymentMethodForm } from "@/features/checkout/PaymentMethodForm";
import { ESTIMATED_DELIVERY_RANGE } from "@/features/checkout/shippingZones";
import { ApiError } from "@/shared/api/client";
import { formatCOP } from "@/shared/lib/formatCOP";
import { QueryFeedback } from "@/shared/ui/Feedback";
import {
  formatPaymentErrorMessage,
  getCancellationReason,
  sanitizeHistoryNote,
  useStartOrderPayment,
  useSyncOrderPayment,
} from "./api";
import type { PaymentStatusCode, StartPaymentInput } from "./types";

const ACTIVE_PAYMENT_STATUSES: ReadonlySet<PaymentStatusCode> = new Set([
  "initiated",
  "processing",
  "action_required",
  "approved",
]);

function formatMethodLabel(method?: string): string {
  if (method === "debit_card") return "Tarjeta débito";
  if (method === "pse") return "PSE (Transferencia bancaria)";
  return "Pago en línea";
}

/** Detalle y resultado del pedido (HU-19 a HU-24): sincroniza estado con MercadoPago y permite reintentar si sigue pendiente sin pago activo. */
export function OrderResultPage() {
  const { numero = "" } = useParams();
  const { data, isPending, isFetching, error, refetch } = useSyncOrderPayment(numero);
  const startPayment = useStartOrderPayment();
  const [paymentError, setPaymentError] = useState<string | null>(null);
  const [conflictRedirectUrl, setConflictRedirectUrl] = useState<string | null>(null);

  const order = data?.order;
  const payment = data?.payment ?? null;
  const hasActivePayment = Boolean(payment?.status && ACTIVE_PAYMENT_STATUSES.has(payment.status));
  const cancellationReason =
    order?.status === "cancelled" ? getCancellationReason(order, payment) : null;

  async function handleRetryPayment(payload: StartPaymentInput) {
    if (!order || startPayment.isPending) return;
    setPaymentError(null);
    setConflictRedirectUrl(null);
    try {
      await startPayment.mutateAsync({
        orderNumber: order.order_number,
        payload,
      });
    } catch (err) {
      if (err instanceof ApiError && err.code === "payment_already_in_progress") {
        const redirect = err.fields.redirect_url?.[0];
        if (redirect) setConflictRedirectUrl(redirect);
      }
      setPaymentError(formatPaymentErrorMessage(err));
    }
  }

  return (
    <section className="space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-4">
        <div>
          <p className="eyebrow">Seguimiento de compra</p>
          <h1 className="text-2xl font-bold">Pedido {numero}</h1>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Link to="/pedidos" className="btn-secondary">
            Mis pedidos
          </Link>
          <Link to="/" className="btn-secondary">
            Volver al catálogo
          </Link>
        </div>
      </header>

      <QueryFeedback pending={isPending} error={error} retry={refetch} />

      {order && (
        <div className="space-y-6">
          {/* Estado principal del pedido en texto claro (HU-21) */}
          <div className="panel flex flex-wrap items-center justify-between gap-4">
            <div className="space-y-1">
              <p className="text-xl font-semibold">Estado: {order.status_label}</p>
              {payment && (
                <p className="text-sm text-muted">
                  Medio de pago: {formatMethodLabel(payment.method)} · Estado del pago:{" "}
                  <strong className="text-foreground">{payment.status_label}</strong>
                </p>
              )}
            </div>
            <button
              type="button"
              className="btn-secondary"
              disabled={isFetching || startPayment.isPending}
              onClick={() => void refetch()}
            >
              {isFetching ? "Actualizando…" : "Actualizar estado"}
            </button>
          </div>

          {/* HU-22: Pago aprobado */}
          {order.status === "payment_approved" && (
            <div role="status" className="notice notice-success space-y-2">
              <p className="font-bold">¡Pago aprobado! Tu compra fue exitosa.</p>
              <p className="text-sm">
                Hemos confirmado tu pago y las unidades quedaron asignadas a tu pedido. Entrega
                estimada: {ESTIMATED_DELIVERY_RANGE}.
              </p>
              <p className="text-xs">
                Nota: Los pedidos con pago aprobado están en firme y no pueden cancelarse desde la
                tienda web.
              </p>
            </div>
          )}

          {/* HU-23 y HU-24: Pedido cancelado (por rechazo o por vencimiento de 30 minutos) */}
          {order.status === "cancelled" && (
            <div role="alert" className="notice notice-error space-y-3">
              {cancellationReason === "rejected" ? (
                <p>
                  Tu pago fue rechazado y el pedido se canceló automáticamente. Las unidades
                  reservadas fueron liberadas y no se realizó ningún cobro. Puedes iniciar una{" "}
                  <Link to="/" className="font-semibold underline">
                    nueva compra
                  </Link>{" "}
                  sujeta al stock disponible.
                </p>
              ) : cancellationReason === "timeout" ? (
                <p>
                  El plazo de 30 minutos para recibir respuesta del pago venció y el pedido se
                  canceló automáticamente. El stock retenido fue reincorporado a la tienda. Puedes
                  hacer una{" "}
                  <Link to="/" className="font-semibold underline">
                    nueva compra
                  </Link>
                  .
                </p>
              ) : (
                <p>
                  Tu pago fue rechazado o venció y el pedido se canceló. Puedes hacer una{" "}
                  <Link to="/" className="font-semibold underline">
                    nueva compra
                  </Link>
                  .
                </p>
              )}
              <div>
                <Link to="/" className="btn-primary">
                  Iniciar un nuevo pedido
                </Link>
              </div>
            </div>
          )}

          {/* HU-21: Pedido Pendiente de Pago */}
          {order.status === "pending_payment" && (
            <div className="space-y-4">
              <div role="status" className="notice space-y-2">
                <p className="font-semibold">
                  Tu pedido se encuentra en estado «{order.status_label}».
                </p>
                <p className="text-sm text-muted">
                  Las unidades están retenidas hasta por 30 minutos mientras la pasarela confirma la
                  transacción. Si no se recibe respuesta en 30 minutos, el pedido se cancelará
                  automáticamente (HU-24).
                </p>
              </div>

              {(payment?.redirect_url || conflictRedirectUrl) && (
                <div
                  role="status"
                  className="panel flex flex-wrap items-center justify-between gap-4 border-border-strong bg-surface-alt"
                >
                  <div className="space-y-1">
                    <p className="font-bold">Autorización pendiente en tu banco (PSE)</p>
                    <p className="text-sm text-muted">
                      Abre el portal de la entidad financiera, completa el pago y luego regresa a{" "}
                      <code className="rounded-[2px] bg-surface px-1 py-0.5 font-mono text-xs text-foreground">
                        /pedidos/{order.order_number}
                      </code>{" "}
                      y pulsa «Actualizar estado». El sistema bloquea nuevos cobros mientras este
                      pago esté en curso.
                    </p>
                  </div>
                  <a
                    href={payment?.redirect_url || conflictRedirectUrl || "#"}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-primary"
                  >
                    Ir al portal del banco
                  </a>
                </div>
              )}

              {hasActivePayment && !payment?.redirect_url && (
                <div role="status" className="panel bg-surface-alt text-sm">
                  <p className="font-semibold">Pago en proceso de validación</p>
                  <p className="text-muted">
                    Este pedido ya tiene un intento de pago activo ({payment?.status_label}). Para
                    protegerte contra cobros duplicados, no se permite enviar un segundo pago sobre
                    este mismo pedido.
                  </p>
                </div>
              )}

              {paymentError && (
                <div role="alert" className="notice notice-error">
                  {paymentError}
                </div>
              )}

              {!hasActivePayment && (
                <div className="panel space-y-4">
                  <div className="border-b border-border pb-3">
                    <h2 className="text-lg font-bold">
                      {payment?.status === "error"
                        ? "Reintentar pago del pedido"
                        : "Completar pago del pedido"}
                    </h2>
                    <p className="text-sm text-muted">
                      Selecciona tu medio de pago para completar el pedido {order.order_number}.
                    </p>
                  </div>
                  <PaymentMethodForm
                    totalAmount={Number(order.total)}
                    defaultHolderName={order.recipient_name}
                    defaultPhone={order.phone}
                    busy={startPayment.isPending}
                    onSubmit={handleRetryPayment}
                  />
                </div>
              )}
            </div>
          )}

          {/* Desglose del pedido e historial */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <div className="panel space-y-4">
              <h2 className="border-b border-border pb-2 text-lg font-bold">Detalle del pedido</h2>
              {order.items && order.items.length > 0 && (
                <ul aria-label="Artículos del pedido" className="space-y-2 text-sm">
                  {order.items.map((item) => (
                    <li
                      key={item.id}
                      className="flex items-center justify-between gap-2 border-b border-border pb-2"
                    >
                      <span>
                        {item.quantity} × {item.product_name} ({item.color} / {item.size})
                      </span>
                      <span className="font-medium">{formatCOP(Number(item.subtotal))}</span>
                    </li>
                  ))}
                </ul>
              )}
              <dl className="space-y-1 text-sm">
                {order.subtotal !== undefined && (
                  <div className="flex justify-between">
                    <dt className="text-muted">Subtotal</dt>
                    <dd>{formatCOP(Number(order.subtotal))}</dd>
                  </div>
                )}
                {order.shipping_cost !== undefined && (
                  <div className="flex justify-between">
                    <dt className="text-muted">
                      Envío{order.municipality ? ` (${order.municipality})` : ""}
                    </dt>
                    <dd>{formatCOP(Number(order.shipping_cost))}</dd>
                  </div>
                )}
                <div className="flex justify-between border-t border-border pt-2 text-base font-bold">
                  <dt>Total</dt>
                  <dd>{formatCOP(Number(order.total))}</dd>
                </div>
              </dl>
              {order.address_line && (
                <div className="border-t border-border pt-3 text-xs text-muted space-y-1">
                  <p>
                    <strong className="text-foreground">Dirección de entrega:</strong>{" "}
                    {order.address_line}, {order.municipality}
                  </p>
                  <p>
                    <strong className="text-foreground">Recibe:</strong> {order.recipient_name} (
                    {order.phone})
                  </p>
                  <p>
                    <strong className="text-foreground">Entrega estimada:</strong>{" "}
                    {ESTIMATED_DELIVERY_RANGE}
                  </p>
                </div>
              )}
            </div>

            <div className="panel space-y-4">
              <h2 className="border-b border-border pb-2 text-lg font-bold">
                Historial de estados
              </h2>
              <ol aria-label="Historial del pedido" className="space-y-2 text-sm">
                {order.status_history.map((h) => {
                  const cleanNote = sanitizeHistoryNote(h.note);
                  return (
                    <li
                      key={h.created_at + h.to_status_label}
                      className="rounded-[2px] border border-border bg-surface-alt p-3"
                    >
                      <p className="font-semibold">{h.to_status_label}</p>
                      <p className="text-xs text-muted">
                        {new Date(h.created_at).toLocaleString("es-CO")}
                        {cleanNote && ` — ${cleanNote}`}
                      </p>
                    </li>
                  );
                })}
              </ol>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
