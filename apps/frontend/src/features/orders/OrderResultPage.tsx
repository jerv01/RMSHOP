import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router";
import { useApi } from "@/shared/api/useApi";
import { QueryFeedback } from "@/shared/ui/Feedback";

type SyncResult = {
  order: {
    order_number: string;
    status: string;
    status_label: string;
    total: string;
    status_history: { to_status_label: string; note: string; created_at: string }[];
  };
  payment: { status_label: string; status_detail: string } | null;
};

/** Vuelta del banco (PSE): consulta el pago en MercadoPago y muestra el estado del pedido. */
export function OrderResultPage() {
  const { numero = "" } = useParams();
  const api = useApi();
  const { data, isPending, error, refetch } = useQuery({
    queryKey: ["order-payment", numero],
    queryFn: () => api<SyncResult>(`/orders/${numero}/payments/sync`, { method: "POST" }),
  });

  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-bold">Pedido {numero}</h1>
      <QueryFeedback pending={isPending} error={error} retry={refetch} />
      {data && (
        <>
          {data.order.status === "payment_approved" && (
            <p role="status" className="notice notice-success">
              ¡Pago aprobado! Tu compra fue exitosa.
            </p>
          )}
          {data.order.status === "cancelled" && (
            <p role="alert" className="notice notice-error">
              Tu pago fue rechazado o venció y el pedido se canceló. Puedes hacer una{" "}
              <Link to="/" className="underline">
                nueva compra
              </Link>
              .
            </p>
          )}
          <p className="text-xl font-semibold">Estado: {data.order.status_label}</p>
          {data.payment && (
            <p className="text-sm text-muted">
              Pago: {data.payment.status_label} ({data.payment.status_detail})
            </p>
          )}
          <ol aria-label="Historial del pedido" className="space-y-1 text-sm">
            {data.order.status_history.map((h) => (
              <li key={h.created_at + h.to_status_label}>
                {new Date(h.created_at).toLocaleString("es-CO")}: {h.to_status_label}
                {h.note && ` — ${h.note}`}
              </li>
            ))}
          </ol>
          <button type="button" className="btn-secondary" onClick={() => refetch()}>
            Actualizar estado
          </button>
        </>
      )}
    </section>
  );
}
