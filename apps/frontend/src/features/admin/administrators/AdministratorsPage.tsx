import { AdministratorsTable } from "./AdministratorsTable";
import { InviteForm } from "./InviteForm";

export function AdministratorsPage() {
  return (
    <div className="space-y-8">
      <header className="border-b border-border pb-4">
        <span className="text-xs font-semibold uppercase tracking-wider text-muted">
          Seguridad y accesos · HU-12
        </span>
        <h1 className="mt-1 text-2xl font-bold tracking-tight text-foreground">Administradores</h1>
        <p className="mt-2 max-w-2xl text-sm text-muted">
          Todos los administradores tienen los mismos permisos. Quien reciba la invitación crea su
          cuenta con el enlace del correo.
        </p>
      </header>

      <section
        aria-labelledby="add-admin"
        className="rounded-[2px] border border-border bg-surface-alt p-5 shadow-(--shadow-soft)"
      >
        <h2 id="add-admin" className="mb-3 text-lg font-semibold text-foreground">
          Agregar administrador
        </h2>
        <InviteForm />
      </section>

      <section aria-labelledby="admin-list">
        <h2 id="admin-list" className="mb-3 text-lg font-semibold text-foreground">
          Cuentas con acceso
        </h2>
        <AdministratorsTable />
      </section>
    </div>
  );
}
