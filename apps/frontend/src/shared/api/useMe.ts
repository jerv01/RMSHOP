import { useAuth } from "@clerk/react";
import { useQuery } from "@tanstack/react-query";
import { useApi } from "./useApi";

export interface Me {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: string | null;
}

/** Perfil de la sesión actual (`GET /me`). Solo consulta cuando hay sesión. */
export function useMe() {
  const { isLoaded, isSignedIn } = useAuth();
  const api = useApi();

  return useQuery({
    queryKey: ["me"],
    queryFn: () => api<Me>("/me"),
    enabled: isLoaded && Boolean(isSignedIn),
  });
}
