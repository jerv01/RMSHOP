import { useAuth } from "@clerk/react";
import { useCallback } from "react";
import { apiFetch, type RequestOptions } from "./client";

/** Cliente de la API que agrega el token de sesión de Clerk a cada petición. */
export function useApi() {
  const { getToken } = useAuth();

  return useCallback(
    <T>(path: string, options: Omit<RequestOptions, "getToken"> = {}) =>
      apiFetch<T>(path, { ...options, getToken: () => getToken() }),
    [getToken],
  );
}
