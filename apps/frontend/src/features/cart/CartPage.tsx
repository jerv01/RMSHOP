import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useRef } from "react";
import { Link } from "react-router";
import { ApiError } from "@/shared/api/client";
import { formatCOP } from "@/shared/lib/formatCOP";
import { ErrorNotice, QueryFeedback } from "@/shared/ui/Feedback";
import { useCart, useReReserveCartItem, useRemoveCartItem, useUpdateCartItem } from "./api";
import { ReservationCountdown } from "./ReservationCountdown";

export function CartPage() {
  const { data: cart, dataUpdatedAt, isPending, error, refetch } = useCart();
  const removeItem = useRemoveCartItem();
  const updateItem = useUpdateCartItem();
  const reReserveItem = useReReserveCartItem();
  const busy = removeItem.isPending || updateItem.isPending || reReserveItem.isPending;
  const mutationError = removeItem.error ?? updateItem.error ?? reReserveItem.error;
  const client = useQueryClient();
  const refreshedReservations = useRef(new Set<string>());
  const handleExpiry = useCallback(
    (reservationKey: string) => {
      if (refreshedReservations.current.has(reservationKey)) return;
      refreshedReservations.current.add(reservationKey);
      void refetch();
      void client.invalidateQueries({ queryKey: ["catalog"] });
    },
    [client, refetch],
  );
  const maxAvailable =
    mutationError instanceof ApiError ? mutationError.fields.max_available : undefined;

  function remove(itemId: number) {
    if (busy) return;
    updateItem.reset();
    reReserveItem.reset();
    removeItem.mutate(itemId);
  }

  function update(itemId: number, quantity: number) {
    if (busy || quantity < 1) return;
    removeItem.reset();
    reReserveItem.reset();
    updateItem.mutate({ itemId, quantity });
  }

  function reReserve(itemId: number) {
    if (busy) return;
    removeItem.reset();
    updateItem.reset();
    reReserveItem.mutate(itemId);
  }

  return (
    <section className="space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-4">
        <h1 className="text-2xl font-bold">Tu carrito</h1>
        <Link to="/" className="btn-secondary">
          Seguir comprando
        </Link>
      </header>

      <QueryFeedback pending={isPending} error={error} retry={refetch} />
      {reReserveItem.error instanceof ApiError && reReserveItem.error.code === "out_of_stock" ? (
        <p role="alert" className="notice notice-error">
          Ya no hay unidades disponibles para volver a reservar.
        </p>
      ) : (
        <ErrorNotice error={mutationError} />
      )}
      {maxAvailable && <p className="text-sm">Máximo disponible: {maxAvailable.join(", ")}</p>}
      {busy && (
        <p role="status" className="text-sm text-muted">
          Actualizando carrito…
        </p>
      )}

      {cart &&
        (cart.items.length === 0 ? (
          <p className="rounded-[2px] border border-border p-8 text-center">
            Tu carrito está vacío
          </p>
        ) : (
          <>
            <ul aria-label="Artículos del carrito" className="space-y-4">
              {cart.items.map((item) => (
                <li
                  key={item.id}
                  aria-label={`${item.product_name}, ${item.color}, ${item.size}`}
                  className="rounded-[2px] border border-border bg-background p-4 sm:p-6"
                >
                  <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
                    <div className="space-y-2">
                      <h2 className="text-lg font-semibold">{item.product_name}</h2>
                      <p className="text-sm text-muted">
                        Color: {item.color} · Talla: {item.size}
                      </p>
                      <p className="text-sm">
                        Precio unitario: {formatCOP(Number(item.unit_price))}
                      </p>
                      <ReservationCountdown
                        item={item}
                        updatedAt={dataUpdatedAt}
                        busy={busy}
                        onExpire={handleExpiry}
                        onReReserve={() => reReserve(item.id)}
                      />
                    </div>
                    <div className="flex flex-wrap items-center gap-3">
                      <div
                        role="group"
                        aria-label={`Cantidad de ${item.product_name}, ${item.color}, ${item.size}`}
                        className="flex items-center gap-3"
                      >
                        <button
                          type="button"
                          className="btn-secondary min-w-11"
                          aria-label="Disminuir cantidad"
                          disabled={busy || item.quantity <= 1}
                          onClick={() => update(item.id, item.quantity - 1)}
                        >
                          −
                        </button>
                        <span aria-label="Cantidad" className="min-w-6 text-center font-semibold">
                          {item.quantity}
                        </span>
                        <button
                          type="button"
                          className="btn-secondary min-w-11"
                          aria-label="Aumentar cantidad"
                          disabled={busy}
                          onClick={() => update(item.id, item.quantity + 1)}
                        >
                          +
                        </button>
                      </div>
                      <button
                        type="button"
                        className="btn-secondary"
                        disabled={busy}
                        onClick={() => remove(item.id)}
                      >
                        Eliminar
                      </button>
                    </div>
                  </div>
                  <p className="mt-4 border-t border-border pt-3 text-right font-semibold">
                    Subtotal: {formatCOP(Number(item.subtotal))}
                  </p>
                </li>
              ))}
            </ul>
            <p
              aria-label="Total del carrito"
              className="border-t border-border pt-4 text-right text-xl font-bold"
            >
              Total: {formatCOP(Number(cart.total_price))}
            </p>
          </>
        ))}
    </section>
  );
}
