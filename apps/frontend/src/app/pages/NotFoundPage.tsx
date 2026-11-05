import { Link } from "react-router";

export function NotFoundPage() {
  return (
    <section className="mx-auto max-w-lg rounded-[2px] border border-border bg-surface-alt p-6 shadow-(--shadow-soft)">
      <span className="text-xs font-semibold uppercase tracking-wider text-muted">Error 404</span>
      <h1 className="mt-1 text-2xl font-bold text-foreground">Página no encontrada</h1>
      <p className="mt-2 text-sm text-muted">La dirección que buscas no existe.</p>
      <Link
        to="/"
        className="mt-5 inline-flex min-h-11 items-center justify-center rounded-[2px] bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition-colors hover:bg-foreground/90"
      >
        Volver al inicio
      </Link>
    </section>
  );
}
