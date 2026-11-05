import { useClerk } from "@clerk/react";
import { Link } from "react-router";

export function NoPermissionPage() {
  const { signOut } = useClerk();

  return (
    <section className="mx-auto max-w-lg rounded-[2px] border border-border bg-surface-alt p-6 shadow-(--shadow-soft)">
      <span className="inline-block rounded-[2px] border border-accent-sale bg-background px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider text-accent-sale">
        Acceso restringido
      </span>
      <h1 className="mt-3 text-2xl font-bold text-foreground">No tienes permisos</h1>
      <p className="mt-2 text-sm text-muted">
        Tu cuenta no puede acceder al panel de administración. Si eres administrador, cierra sesión
        e ingresa con tu cuenta administrativa.
      </p>
      <div className="mt-6 flex flex-wrap items-center gap-3">
        <Link
          to="/"
          className="inline-flex min-h-11 items-center justify-center rounded-[2px] bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition-colors hover:bg-foreground/90"
        >
          Ir al inicio
        </Link>
        <button
          type="button"
          onClick={() => void signOut()}
          className="inline-flex min-h-11 items-center justify-center rounded-[2px] border border-border-strong bg-background px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-surface"
        >
          Cerrar sesión
        </button>
      </div>
    </section>
  );
}
