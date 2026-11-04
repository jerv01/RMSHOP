import { AlertDialog } from "radix-ui";
import { useRef, useState } from "react";
import { ApiError } from "@/shared/api/client";
import { useAdministrators, useRemoveAdministrator, type Administrator } from "./api";

function fullName(admin: Administrator) {
  return `${admin.first_name} ${admin.last_name}`.trim() || admin.email;
}

export function AdministratorsTable() {
  const { data, isPending, isError } = useAdministrators();
  const remove = useRemoveAdministrator();
  const [target, setTarget] = useState<Administrator | null>(null);
  const [removeError, setRemoveError] = useState<string | null>(null);
  // El diálogo es controlado (sin Trigger): al cerrarse, el foco vuelve al botón que lo abrió.
  const opener = useRef<HTMLButtonElement | null>(null);

  function close() {
    setTarget(null);
    setRemoveError(null);
    remove.reset();
  }

  async function confirm() {
    if (!target) return;
    try {
      await remove.mutateAsync(target.clerk_user_id);
      close();
    } catch (error) {
      setRemoveError(
        error instanceof ApiError
          ? error.message
          : "Ocurrió un error inesperado. Intenta de nuevo.",
      );
    }
  }

  if (isPending) return <p role="status">Cargando administradores…</p>;
  if (isError) return <p role="alert">No pudimos cargar los administradores. Intenta de nuevo.</p>;

  return (
    <>
      <table className="w-full max-w-3xl border-collapse text-left">
        <caption className="sr-only">Administradores de la tienda</caption>
        <thead>
          <tr className="border-b border-gray-300">
            <th scope="col" className="py-2 pr-4">
              Nombre
            </th>
            <th scope="col" className="py-2 pr-4">
              Correo
            </th>
            <th scope="col" className="py-2">
              <span className="sr-only">Acciones</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {data.map((admin) => (
            <tr key={admin.clerk_user_id} className="border-b border-gray-200">
              <td className="py-2 pr-4">
                {fullName(admin)}
                {admin.is_me && (
                  <span className="ml-2 rounded bg-gray-200 px-2 py-0.5 text-sm text-gray-900">
                    Tú
                  </span>
                )}
              </td>
              <td className="py-2 pr-4">{admin.email}</td>
              <td className="py-2 text-right">
                <button
                  type="button"
                  // El backend es quien impone la regla; esto solo evita el intento.
                  disabled={admin.is_me}
                  aria-label={`Eliminar a ${fullName(admin)}`}
                  onClick={(event) => {
                    opener.current = event.currentTarget;
                    setTarget(admin);
                  }}
                  className="rounded border border-red-700 px-3 py-1 text-red-700 disabled:border-gray-400 disabled:text-gray-600"
                >
                  Eliminar
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <AlertDialog.Root open={target !== null} onOpenChange={(open) => !open && close()}>
        <AlertDialog.Portal>
          <AlertDialog.Overlay className="fixed inset-0 bg-black/50" />
          <AlertDialog.Content
            onCloseAutoFocus={(event) => {
              event.preventDefault();
              opener.current?.focus();
            }}
            className="fixed top-1/2 left-1/2 w-[90vw] max-w-md -translate-x-1/2 -translate-y-1/2 rounded bg-white p-6 shadow-lg"
          >
            <AlertDialog.Title className="text-lg font-semibold">
              Eliminar administrador
            </AlertDialog.Title>
            <AlertDialog.Description className="mt-2 text-gray-800">
              {target && `${fullName(target)} (${target.email}) perderá el acceso al panel. `}
              Esta acción no se puede deshacer.
            </AlertDialog.Description>
            <p role="alert" className="mt-2 min-h-5 text-sm text-red-700">
              {removeError}
            </p>
            <div className="mt-4 flex justify-end gap-2">
              <AlertDialog.Cancel className="rounded border border-gray-600 px-3 py-1">
                Cancelar
              </AlertDialog.Cancel>
              <AlertDialog.Action
                onClick={(event) => {
                  // Radix cierra el diálogo al accionar; aquí se cierra solo si la baja funciona.
                  event.preventDefault();
                  void confirm();
                }}
                disabled={remove.isPending}
                className="rounded bg-red-700 px-3 py-1 text-white disabled:opacity-60"
              >
                {remove.isPending ? "Eliminando…" : "Eliminar"}
              </AlertDialog.Action>
            </div>
          </AlertDialog.Content>
        </AlertDialog.Portal>
      </AlertDialog.Root>
    </>
  );
}
