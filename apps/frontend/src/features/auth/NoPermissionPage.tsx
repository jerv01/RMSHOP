import { useClerk } from "@clerk/react";
import { Link } from "react-router";

export function NoPermissionPage() {
  const { signOut } = useClerk();

  return (
    <>
      <h1 className="text-2xl font-bold">No tienes permisos</h1>
      <p className="mt-2">Tu cuenta no puede acceder al panel de administración.</p>
      <div className="mt-4 flex items-center gap-4">
        <Link to="/" className="underline">
          Ir al inicio
        </Link>
        <button type="button" onClick={() => void signOut()} className="rounded border px-3 py-1">
          Cerrar sesión
        </button>
      </div>
    </>
  );
}
