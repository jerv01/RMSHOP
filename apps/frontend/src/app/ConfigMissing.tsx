import { BrandLogo } from "@/shared/ui/BrandLogo";

/** Se muestra en lugar de la app cuando falta la clave publicable de Clerk. */
export function ConfigMissing() {
  return (
    <main className="mx-auto max-w-xl p-8">
      <div className="rounded-[2px] border border-border-strong bg-surface-alt p-6 shadow-(--shadow-soft)">
        <BrandLogo size="md" />
        <h1 className="mt-4 text-2xl font-bold text-foreground">Falta configurar Clerk</h1>
        <p className="mt-4 text-sm text-foreground">
          La aplicación necesita la variable{" "}
          <code className="rounded-[2px] bg-surface px-1.5 py-0.5 font-mono">
            VITE_CLERK_PUBLISHABLE_KEY
          </code>{" "}
          en{" "}
          <code className="rounded-[2px] bg-surface px-1.5 py-0.5 font-mono">
            apps/frontend/.env
          </code>
          .
        </p>
        <p className="mt-2 text-sm text-muted">
          Copia la clave publicable desde el panel de Clerk, guarda el archivo y recrea el servicio
          con{" "}
          <code className="rounded-[2px] bg-surface px-1.5 py-0.5 font-mono text-foreground">
            docker compose up -d
          </code>
          .
        </p>
        <p className="mt-2 text-sm text-muted">
          Los pasos completos están en{" "}
          <code className="rounded-[2px] bg-surface px-1.5 py-0.5 font-mono text-foreground">
            docs/clerk-setup.md
          </code>
          .
        </p>
      </div>
    </main>
  );
}
