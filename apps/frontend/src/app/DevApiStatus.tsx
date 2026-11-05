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
  const { isSignedIn } = useAuth();
  const health = useQuery({ queryKey: ["health"], queryFn: () => apiFetch<Health>("/health") });
  const me = useMe();

  return (
    <section
      aria-label="Estado de la API"
      className="mt-6 rounded-[2px] border border-border bg-surface-alt p-5 text-sm shadow-(--shadow-soft)"
    >
      <h2 className="font-semibold text-foreground">Estado de la API (solo desarrollo)</h2>
      {health.isPending && <p className="mt-1 text-muted">Consultando…</p>}
      {health.isError && (
        <p role="alert" className="mt-1 font-medium text-accent-sale">
          Error: {health.error.message}
        </p>
      )}
      {health.data && (
        <p className="mt-1 font-medium text-accent-success">
          API: {health.data.status} · Base de datos: {health.data.database}
        </p>
      )}

      <h3 className="mt-4 font-semibold text-foreground">GET /me</h3>
      {!isSignedIn && (
        <p className="mt-1 text-muted">
          Sin sesión.{" "}
          <Link to="/ingresar" className="font-semibold text-foreground underline">
            Inicia sesión
          </Link>{" "}
          para probarlo.
        </p>
      )}
      {isSignedIn && me.isPending && <p className="mt-1 text-muted">Consultando…</p>}
      {me.isError && (
        <p role="alert" className="mt-1 font-medium text-accent-sale">
          Error: {me.error.message}
        </p>
      )}
      {me.data && (
        <pre className="mt-2 overflow-x-auto rounded-[2px] border border-border bg-background p-3 font-mono text-xs text-foreground">
          {JSON.stringify(me.data, null, 2)}
        </pre>
      )}
    </section>
  );
}
