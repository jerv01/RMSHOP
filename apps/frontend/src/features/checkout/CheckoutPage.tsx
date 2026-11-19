import { useState } from "react";
import { Link, useNavigate } from "react-router";
import { useCart } from "@/features/cart/api";
import {
  formatPaymentErrorMessage,
  useCreateCheckoutOrder,
  useStartOrderPayment,
} from "@/features/orders/api";
import type { OrderDetail, StartPaymentInput } from "@/features/orders/types";
import { ApiError } from "@/shared/api/client";
import { formatCOP } from "@/shared/lib/formatCOP";
import { QueryFeedback } from "@/shared/ui/Feedback";
import { PaymentMethodForm } from "./PaymentMethodForm";
import {
  ESTIMATED_DELIVERY_RANGE,
  findShippingZone,
  MUNICIPALITY_NOT_COVERED_MESSAGE,
  SHIPPING_ZONES,
} from "./shippingZones";

export function CheckoutPage() {
  const navigate = useNavigate();
  const { data: cart, isPending: cartPending, error: cartError, refetch: refetchCart } = useCart();
  const createOrder = useCreateCheckoutOrder();
  const startPayment = useStartOrderPayment();

  const [municipality, setMunicipality] = useState<string>("Cali");
  const [addressLine, setAddressLine] = useState<string>("");
  const [recipientName, setRecipientName] = useState<string>("");
  const [phone, setPhone] = useState<string>("");

  // Una vez creado el pedido en POST /checkout, se conserva en estado "Pendiente de Pago"
  // para que cualquier reintento de pago opere sobre el mismo pedido sin duplicar órdenes (HU-21).
  const [createdOrder, setCreatedOrder] = useState<OrderDetail | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [addressError, setAddressError] = useState<string | null>(null);
  const [paymentError, setPaymentError] = useState<string | null>(null);
  const [redirectUrl, setRedirectUrl] = useState<string | null>(null);

  const selectedZone = findShippingZone(municipality);
  const busy = createOrder.isPending || startPayment.isPending;

  const subtotal = createdOrder ? Number(createdOrder.subtotal) : Number(cart?.total_price ?? 0);
  const shippingCost = createdOrder ? Number(createdOrder.shipping_cost) : (selectedZone?.fee ?? 0);
  const total = createdOrder ? Number(createdOrder.total) : subtotal + shippingCost;

  function validateShipping(): boolean {
    setAddressError(null);
    if (!selectedZone) {
      setFormError(MUNICIPALITY_NOT_COVERED_MESSAGE);
      return false;
    }
    if (!addressLine.trim()) {
      const message = "Ingresa la dirección de entrega.";
      setAddressError(message);
      setFormError(message);
      return false;
    }
    if (!recipientName.trim()) {
      setFormError("Ingresa el nombre de la persona que recibirá el pedido.");
      return false;
    }
    const cleanPhone = phone.trim();
    if (!/^\+?[0-9 ]{7,20}$/.test(cleanPhone)) {
      setFormError("Ingresa un teléfono de contacto válido (solo números).");
      return false;
    }
    return true;
  }

  async function handlePaymentSubmit(paymentPayload: StartPaymentInput) {
    if (busy) return;
    setFormError(null);
    setPaymentError(null);

    let order = createdOrder;
    if (!order) {
      if (!validateShipping()) return;
      try {
        order = await createOrder.mutateAsync({
          municipality: selectedZone ? selectedZone.municipality : municipality,
          address_line: addressLine.trim(),
          recipient_name: recipientName.trim(),
          phone: phone.trim(),
        });
        setCreatedOrder(order);
      } catch (err) {
        setFormError(formatPaymentErrorMessage(err));
        return;
      }
    }

    try {
      const result = await startPayment.mutateAsync({
        orderNumber: order.order_number,
        payload: paymentPayload,
      });
      setCreatedOrder(result.order);
      if (result.payment?.redirect_url) {
        setRedirectUrl(result.payment.redirect_url);
      }
      void navigate(`/pedidos/${result.order.order_number}`);
    } catch (err) {
      if (err instanceof ApiError && err.code === "payment_already_in_progress") {
        const existingRedirect = err.fields.redirect_url?.[0];
        if (existingRedirect) {
          setRedirectUrl(existingRedirect);
        }
      }
      setPaymentError(formatPaymentErrorMessage(err));
    }
  }

  if (!createdOrder && (cartPending || cartError)) {
    return (
      <section className="space-y-4">
        <h1 className="text-2xl font-bold">Finalizar compra</h1>
        <QueryFeedback pending={cartPending} error={cartError} retry={refetchCart} />
      </section>
    );
  }

  if (!createdOrder && (!cart || cart.items.length === 0)) {
    return (
      <section className="space-y-4">
        <h1 className="text-2xl font-bold">Finalizar compra</h1>
        <div className="rounded-[2px] border border-border p-8 text-center space-y-4">
          <p>Tu carrito está vacío. Agrega productos antes de iniciar el pago.</p>
          <Link to="/" className="btn-primary">
            Explorar catálogo
          </Link>
        </div>
      </section>
    );
  }

  return (
    <section className="space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-4">
        <div>
          <p className="eyebrow">Checkout seguro · RM Shop</p>
          <h1 className="text-2xl font-bold">Finalizar compra</h1>
        </div>
        {createdOrder ? (
          <Link to={`/pedidos/${createdOrder.order_number}`} className="btn-secondary">
            Ver pedido {createdOrder.order_number}
          </Link>
        ) : (
          <Link to="/carrito" className="btn-secondary">
            Volver al carrito
          </Link>
        )}
      </header>

      {createdOrder && (
        <div
          role="status"
          aria-label="Estado actual del pedido"
          className="rounded-[2px] border border-border-strong bg-surface-alt p-4 space-y-1"
        >
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="font-bold">
              Pedido {createdOrder.order_number} · Estado:{" "}
              <span className="inline-block rounded-[2px] border border-border-strong bg-background px-2.5 py-0.5 text-sm font-bold">
                {createdOrder.status_label}
              </span>
            </p>
            <Link
              to={`/pedidos/${createdOrder.order_number}`}
              className="text-sm font-semibold underline"
            >
              Consultar estado e historial
            </Link>
          </div>
          <p className="text-xs text-muted">
            Tu stock quedó retenido durante 30 minutos mientras se confirma el pago.
          </p>
        </div>
      )}

      {busy && (
        <p role="status" className="notice">
          {createOrder.isPending
            ? "Creando tu pedido y reservando unidades…"
            : "Comunicándose con la pasarela de pagos (máximo 5 segundos)…"}
        </p>
      )}

      {formError && (
        <div role="alert" className="notice notice-error">
          {formError}
        </div>
      )}

      {paymentError && (
        <div role="alert" className="notice notice-error space-y-2">
          <p>{paymentError}</p>
          {redirectUrl && (
            <p>
              <a
                href={redirectUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-primary mt-2"
              >
                Continuar pago en el portal del banco (PSE)
              </a>
            </p>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          {/* Paso 1: Datos de envío (HU-25 a HU-28) */}
          <div className="panel space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border pb-3">
              <h2 className="text-lg font-bold">1. Dirección de envío</h2>
              {(createdOrder || selectedZone) && (
                <span className="badge">Entrega estimada: {ESTIMATED_DELIVERY_RANGE}</span>
              )}
            </div>

            {createdOrder ? (
              <div className="space-y-1 text-sm">
                <p>
                  <strong>Destinatario:</strong> {createdOrder.recipient_name} ({createdOrder.phone}
                  )
                </p>
                <p>
                  <strong>Dirección:</strong> {createdOrder.address_line},{" "}
                  {createdOrder.municipality} (Valle del Cauca)
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <label className="field">
                  <span>Municipio de entrega</span>
                  <select
                    aria-label="Municipio de entrega"
                    disabled={busy}
                    value={municipality}
                    onChange={(e) => {
                      setMunicipality(e.target.value);
                      setFormError(null);
                    }}
                  >
                    {SHIPPING_ZONES.map((zone) => (
                      <option key={zone.municipality} value={zone.municipality}>
                        {zone.municipality} ({formatCOP(zone.fee)})
                      </option>
                    ))}
                  </select>
                </label>

                <label className="field">
                  <span>Teléfono de contacto</span>
                  <input
                    type="tel"
                    inputMode="numeric"
                    disabled={busy}
                    placeholder="3001234567"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                  />
                </label>

                <label className="field sm:col-span-2">
                  <span>Dirección de entrega</span>
                  <input
                    aria-invalid={addressError ? "true" : "false"}
                    aria-describedby={addressError ? "address-error" : undefined}
                    maxLength={255}
                    type="text"
                    disabled={busy}
                    placeholder="Calle 10 # 20-30 Apto 401"
                    value={addressLine}
                    onChange={(e) => {
                      setAddressLine(e.target.value);
                      if (addressError) setAddressError(null);
                      if (formError === "Ingresa la dirección de entrega.") setFormError(null);
                    }}
                  />
                  {addressError && (
                    <span id="address-error" role="alert" className="field-error">
                      {addressError}
                    </span>
                  )}
                </label>

                <label className="field sm:col-span-2">
                  <span>Nombre de quien recibe</span>
                  <input
                    type="text"
                    disabled={busy}
                    placeholder="Ana Pérez"
                    value={recipientName}
                    onChange={(e) => setRecipientName(e.target.value)}
                  />
                </label>

                {!selectedZone && (
                  <p role="alert" className="notice notice-error sm:col-span-2">
                    {MUNICIPALITY_NOT_COVERED_MESSAGE}
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Paso 2: Medio de pago (HU-19 y HU-20) */}
          <div className="panel space-y-4">
            <div className="border-b border-border pb-3">
              <h2 className="text-lg font-bold">2. Pago en línea</h2>
            </div>

            <PaymentMethodForm
              totalAmount={total}
              defaultHolderName={createdOrder?.recipient_name || recipientName}
              defaultPhone={createdOrder?.phone || phone}
              busy={busy || (!createdOrder && !selectedZone)}
              onSubmit={handlePaymentSubmit}
            />
          </div>
        </div>

        {/* Resumen del pedido (HU-16, HU-26, HU-27) */}
        <aside aria-label="Resumen de la compra" className="panel h-fit space-y-4">
          <h2 className="border-b border-border pb-3 text-lg font-bold">Resumen del pedido</h2>

          <ul className="space-y-3 text-sm">
            {(createdOrder?.items ?? cart?.items ?? []).map((item) => (
              <li
                key={item.id}
                className="flex items-start justify-between gap-2 border-b border-border pb-2"
              >
                <div>
                  <p className="font-semibold">{item.product_name}</p>
                  <p className="text-xs text-muted">
                    {item.color} / {item.size} × {item.quantity}
                  </p>
                </div>
                <span className="font-medium">{formatCOP(Number(item.subtotal))}</span>
              </li>
            ))}
          </ul>

          <dl className="space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-muted">Subtotal prendas</dt>
              <dd className="font-medium">{formatCOP(subtotal)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted">
                Envío (
                {createdOrder?.municipality ?? (selectedZone?.municipality || "Sin cobertura")})
              </dt>
              <dd className="font-medium">
                {selectedZone || createdOrder ? formatCOP(shippingCost) : "No disponible"}
              </dd>
            </div>
            {(createdOrder || selectedZone) && (
              <div className="flex justify-between gap-3">
                <dt className="text-muted">Entrega estimada</dt>
                <dd className="font-medium">{ESTIMATED_DELIVERY_RANGE}</dd>
              </div>
            )}
            <div className="flex justify-between border-t border-border pt-3 text-base font-bold">
              <dt>Total</dt>
              <dd aria-label="Total a pagar">{formatCOP(total)}</dd>
            </div>
          </dl>
        </aside>
      </div>
    </section>
  );
}
