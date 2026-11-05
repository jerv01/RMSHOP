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

  if (isPending) {
    return (
      <p
        role="status"
        className="rounded-[2px] border border-border bg-surface-alt p-4 text-sm text-muted"
      >
        Cargando administradores…
      </p>
    );
  }

  if (isError) {
    return (
      <p
        role="alert"
        className="rounded-[2px] border border-accent-sale bg-background p-4 text-sm font-medium text-accent-sale"
      >
        No pudimos cargar los administradores. Intenta de nuevo.
      </p>
    );
  }

  return (
    <>
      <div className="mb-3 flex items-center justify-between">
        <span className="inline-flex items-center rounded-[2px] border border-border bg-surface px-2.5 py-1 text-xs font-semibold text-foreground">
          {data.length === 1 ? "1 administrador activo" : `${data.length} administradores activos`}
        </span>
      </div>

      <div className="overflow-x-auto rounded-[2px] border border-border bg-background shadow-(--shadow-soft)">
        <table className="w-full border-collapse text-left text-sm">
          <caption className="sr-only">Administradores de la tienda</caption>
          <thead>
            <tr className="border-b border-border bg-surface text-xs font-semibold uppercase tracking-wider text-foreground">
              <th scope="col" className="px-4 py-3">
                Nombre
              </th>
              <th scope="col" className="px-4 py-3">
                Correo
              </th>
              <th scope="col" className="px-4 py-3 text-right">
                <span className="sr-only">Acciones</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {data.map((admin) => (
              <tr
                key={admin.clerk_user_id}
                className="border-b border-border bg-background transition-colors last:border-b-0 even:bg-surface-alt hover:bg-surface"
              >
                <td className="px-4 py-3 font-medium text-foreground">
                  {fullName(admin)}
                  {admin.is_me && (
                    <span className="ml-2 inline-flex items-center rounded-[2px] border border-accent-success bg-background px-2 py-0.5 text-xs font-semibold text-accent-success">
                      Tú
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-muted">{admin.email}</td>
                <td className="px-4 py-3 text-right">
                  <button
                    type="button"
                    // El backend es quien impone la regla; esto solo evita el intento.
                    disabled={admin.is_me}
                    aria-label={`Eliminar a ${fullName(admin)}`}
                    onClick={(event) => {
                      opener.current = event.currentTarget;
                      setTarget(admin);
                    }}
                    className="inline-flex min-h-11 min-w-11 items-center justify-center rounded-[2px] border border-accent-sale bg-background px-3.5 py-2 text-xs font-semibold uppercase tracking-wider text-accent-sale transition-colors hover:bg-accent-sale hover:text-primary-foreground disabled:cursor-not-allowed disabled:border-border disabled:bg-surface-alt disabled:text-muted"
                  >
                    Eliminar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <AlertDialog.Root open={target !== null} onOpenChange={(open) => !open && close()}>
        <AlertDialog.Portal>
          <AlertDialog.Overlay className="fixed inset-0 bg-foreground/50" />
          <AlertDialog.Content
            onCloseAutoFocus={(event) => {
              event.preventDefault();
              opener.current?.focus();
            }}
            className="fixed top-1/2 left-1/2 w-[90vw] max-w-md -translate-x-1/2 -translate-y-1/2 rounded-[2px] border border-border-strong bg-background p-6 shadow-(--shadow-soft)"
          >
            <AlertDialog.Title className="text-lg font-bold text-foreground">
              Eliminar administrador
            </AlertDialog.Title>
            <AlertDialog.Description className="mt-2 text-sm text-muted">
              {target && `${fullName(target)} (${target.email}) perderá el acceso al panel. `}
              Esta acción no se puede deshacer.
            </AlertDialog.Description>
            <p role="alert" className="mt-2 min-h-5 text-sm font-medium text-accent-sale">
              {removeError}
            </p>
            <div className="mt-4 flex justify-end gap-3">
              <AlertDialog.Cancel className="inline-flex min-h-11 items-center justify-center rounded-[2px] border border-border-strong bg-background px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-surface-alt">
                Cancelar
              </AlertDialog.Cancel>
              <AlertDialog.Action
                onClick={(event) => {
                  // Radix cierra el diálogo al accionar; aquí se cierra solo si la baja funciona.
                  event.preventDefault();
                  void confirm();
                }}
                disabled={remove.isPending}
                className="inline-flex min-h-11 items-center justify-center rounded-[2px] bg-accent-sale px-4 py-2 text-sm font-semibold text-primary-foreground transition-opacity disabled:opacity-60"
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
