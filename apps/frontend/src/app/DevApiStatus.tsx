import { useAuth } from "@clerk/react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router";
import { apiFetch } from "@/shared/api/client";
import { useMe } from "@/shared/api/useMe";

interface Health {
  status: string;
  database: string;
}

/** Solo desarrollo: muestra si la API responde y, con sesión, el resultado de `GET /me`. */
export function DevApiStatus() {
  const { isSignedIn, getToken } = useAuth();
  const health = useQuery({ queryKey: ["health"], queryFn: () => apiFetch<Health>("/health") });
  const me = useMe();

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

      <h3 className="mt-3 font-semibold">GET /me</h3>
      {!isSignedIn && (
        <p>
          Sin sesión.{" "}
          <Link to="/ingresar" className="underline">
            Inicia sesión
          </Link>{" "}
          para probarlo.
        </p>
      )}
      {isSignedIn && me.isPending && <p>Consultando…</p>}
      {me.isError && <p role="alert">Error: {me.error.message}</p>}
      {me.data && <pre className="overflow-x-auto">{JSON.stringify(me.data, null, 2)}</pre>}
      {isSignedIn && (
        <button
          type="button"
          onClick={async () => {
            const token = await getToken();
            if (token) {
              await navigator.clipboard.writeText(token);
              alert("Token copiado al portapapeles. Pégalo en el botón 'Authorize' de Swagger.");
            }
          }}
          className="mt-2 rounded bg-black px-3 py-1.5 text-xs text-white hover:bg-gray-800"
        >
          Copiar token para Swagger UI
        </button>
      )}
    </section>
  );
}
