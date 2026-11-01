import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/shared/api/client";

interface Health {
  status: string;
  database: string;
}

/** Solo desarrollo: muestra si la API y la base de datos responden. */
export function DevApiStatus() {
  const health = useQuery({ queryKey: ["health"], queryFn: () => apiFetch<Health>("/health") });

  return (
    <section
      aria-label="Estado de la API"
      className="mt-6 rounded border border-gray-300 p-4 text-sm"
    >
      <h2 className="font-semibold">Estado de la API (solo desarrollo)</h2>
      {health.isPending && <p>Consultando…</p>}
      {health.isError && <p role="alert">Error: {health.error.message}</p>}
      {health.data && (
        <p>
          API: {health.data.status} · Base de datos: {health.data.database}
        </p>
      )}
    </section>
  );
}
