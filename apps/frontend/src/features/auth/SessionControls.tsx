import { useAuth, useClerk } from "@clerk/react";
import { Link } from "react-router";

/** Acceso a la sesión en el encabezado: "Ingresar" y "Registrarse", o "Cerrar sesión". */
export function SessionControls() {
  const { isLoaded, isSignedIn } = useAuth();
  const { signOut } = useClerk();

  if (!isLoaded) return null;

  if (!isSignedIn) {
    return (
      <nav aria-label="Acceso de cuenta" className="flex flex-wrap items-center gap-2 text-sm">
        <Link
          to="/ingresar"
          className="inline-flex min-h-11 items-center justify-center rounded-[2px] border border-border-strong bg-background px-4 py-2 font-medium text-foreground transition-colors hover:bg-surface-alt"
        >
          Ingresar
        </Link>
        <Link
          to="/registro"
          className="inline-flex min-h-11 items-center justify-center rounded-[2px] border border-primary bg-primary px-4 py-2 font-semibold text-primary-foreground transition-colors hover:bg-foreground/90"
        >
          Registrarse
        </Link>
      </nav>
    );
  }

  return (
    <button
      type="button"
      onClick={() => void signOut()}
      className="inline-flex min-h-11 items-center justify-center rounded-[2px] border border-border-strong bg-background px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-surface-alt"
    >
      Cerrar sesión
    </button>
  );
}
