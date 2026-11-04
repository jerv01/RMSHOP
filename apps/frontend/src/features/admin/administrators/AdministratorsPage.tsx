import { AdministratorsTable } from "./AdministratorsTable";
import { InviteForm } from "./InviteForm";

export function AdministratorsPage() {
  return (
    <>
      <h1 className="text-2xl font-bold">Administradores</h1>
      <p className="mt-2 text-gray-800">
        Todos los administradores tienen los mismos permisos. Quien reciba la invitación crea su
        cuenta con el enlace del correo.
      </p>
      <section aria-labelledby="add-admin" className="mt-6">
        <h2 id="add-admin" className="mb-2 text-lg font-semibold">
          Agregar administrador
        </h2>
        <InviteForm />
      </section>
      <section aria-labelledby="admin-list" className="mt-6">
        <h2 id="admin-list" className="mb-2 text-lg font-semibold">
          Cuentas con acceso
        </h2>
        <AdministratorsTable />
      </section>
    </>
  );
}
