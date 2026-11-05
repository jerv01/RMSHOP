import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useApi } from "@/shared/api/useApi";

export interface Administrator {
  clerk_user_id: string;
  email: string;
  first_name: string;
  last_name: string;
  is_me: boolean;
}

export const administratorsKey = ["administrators"] as const;

export function useAdministrators() {
  const api = useApi();
  return useQuery({
    queryKey: administratorsKey,
    queryFn: () => api<Administrator[]>("/admin/administrators"),
  });
}

/** Registrar = invitar: el correo recibe un enlace para crear su cuenta de administrador. */
export function useInviteAdministrator() {
  const api = useApi();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (email: string) =>
      api<{ status: "invited"; email: string }>("/admin/administrators", {
        method: "POST",
        json: { email },
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: administratorsKey }),
  });
}

export function useRemoveAdministrator() {
  const api = useApi();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (clerkUserId: string) =>
      api<void>(`/admin/administrators/${encodeURIComponent(clerkUserId)}`, {
        method: "DELETE",
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: administratorsKey }),
  });
}
