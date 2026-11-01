import { useAuth } from "@clerk/react";
import { Navigate, Outlet, useLocation } from "react-router";

/**
 * Exige una sesión de Clerk; sin ella redirige a `/ingresar`.
 *
 * Esta protección es solo de experiencia de uso: la autorización real la aplica el backend
 * en cada petición.
 */
export function RequireAuth() {
  const { isLoaded, isSignedIn } = useAuth();
  const location = useLocation();

  if (!isLoaded) return <p role="status">Cargando…</p>;
  if (!isSignedIn) return <Navigate to="/ingresar" replace state={{ from: location }} />;
  return <Outlet />;
}
