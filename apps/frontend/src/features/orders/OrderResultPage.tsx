import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router";
import { useApi } from "@/shared/api/useApi";
import { QueryFeedback } from "@/shared/ui/Feedback";

type SyncResult = {
  order: { order_number: string; status_label: string; total: string };
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
          <p className="text-xl font-semibold">Estado: {data.order.status_label}</p>
          {data.payment && (
            <p className="text-sm text-muted">
              Pago: {data.payment.status_label} ({data.payment.status_detail})
            </p>
          )}
          <button type="button" className="btn-secondary" onClick={() => refetch()}>
            Actualizar estado
          </button>
        </>
      )}
    </section>
  );
}
