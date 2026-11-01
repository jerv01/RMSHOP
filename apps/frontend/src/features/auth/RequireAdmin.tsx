import { useAuth, useUser } from "@clerk/react";
import { Navigate, Outlet } from "react-router";
import { NoPermissionPage } from "./NoPermissionPage";

/**
 * Exige una sesión con rol `admin` (`publicMetadata.role` del usuario de Clerk). Sin sesión
 * redirige a `/admin/ingresar`; con sesión sin el rol, muestra "No tienes permisos".
 *
 * Esta protección es solo de experiencia de uso: la autorización real la aplica el backend
 * (`IsRMAdmin`) leyendo el rol del token en cada petición.
 */
export function RequireAdmin() {
  const { isLoaded: authLoaded, isSignedIn } = useAuth();
  const { isLoaded: userLoaded, user } = useUser();

  if (!authLoaded || !userLoaded) return <p role="status">Cargando…</p>;
  if (!isSignedIn) return <Navigate to="/admin/ingresar" replace />;
  if (user?.publicMetadata.role !== "admin") return <NoPermissionPage />;
  return <Outlet />;
}
