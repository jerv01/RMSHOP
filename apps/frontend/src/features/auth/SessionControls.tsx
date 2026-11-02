import { useAuth, useClerk } from "@clerk/react";
import { Link } from "react-router";

/** Acceso a la sesión en el encabezado: "Ingresar" y "Registrarse", o "Cerrar sesión". */
export function SessionControls() {
  const { isLoaded, isSignedIn } = useAuth();
  const { signOut } = useClerk();

  if (!isLoaded) return null;

  if (!isSignedIn) {
    return (
      <nav className="flex gap-4 text-sm">
        <Link to="/ingresar">Ingresar</Link>
        <Link to="/registro">Registrarse</Link>
      </nav>
    );
  }

  return (
    <button type="button" className="text-sm underline" onClick={() => void signOut()}>
      Cerrar sesión
    </button>
  );
}
