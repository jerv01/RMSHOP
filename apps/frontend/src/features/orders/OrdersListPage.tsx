import { Link } from "react-router";
import { formatCOP } from "@/shared/lib/formatCOP";
import { QueryFeedback } from "@/shared/ui/Feedback";
import { useCustomerOrders } from "./api";

/** Listado de pedidos del cliente con estado visible en texto (HU-21, HU-24, HU-29, HU-30). */
export function OrdersListPage() {
  const { data: orders, isPending, error, refetch } = useCustomerOrders();

  return (
    <section className="space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-4">
        <div>
          <p className="eyebrow">Cuenta del cliente</p>
          <h1 className="text-2xl font-bold">Mis pedidos</h1>
        </div>
        <Link to="/" className="btn-secondary">
          Seguir comprando
        </Link>
      </header>

      <QueryFeedback pending={isPending} error={error} retry={refetch} />

      {orders &&
        (orders.length === 0 ? (
          <div className="rounded-[2px] border border-border p-8 text-center space-y-4">
            <p>Aún no tienes pedidos</p>
            <Link to="/" className="btn-primary">
              Explorar catálogo
            </Link>
          </div>
        ) : (
          <ul aria-label="Lista de mis pedidos" className="space-y-4">
            {orders.map((order) => (
              <li
                key={order.order_number}
                className="panel flex flex-col justify-between gap-4 sm:flex-row sm:items-center"
              >
                <div className="space-y-1">
                  <div className="flex flex-wrap items-center gap-3">
                    <h2 className="text-lg font-bold">{order.order_number}</h2>
                    <span className="inline-block rounded-[2px] border border-border-strong bg-surface-alt px-2.5 py-0.5 text-xs font-bold">
                      {order.status_label}
                    </span>
                  </div>
                  <p className="text-xs text-muted">
                    Fecha: {new Date(order.created_at).toLocaleString("es-CO")}
                  </p>
                  <p className="text-sm font-semibold">Total: {formatCOP(Number(order.total))}</p>
                </div>

                <Link
                  to={`/pedidos/${order.order_number}`}
                  className="btn-secondary"
                  aria-label={`Ver detalle de ${order.order_number}`}
                >
                  Ver detalle
                </Link>
              </li>
            ))}
          </ul>
        ))}
    </section>
  );
}
