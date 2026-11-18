import { useAuth } from "@clerk/react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError } from "@/shared/api/client";
import { useApi } from "@/shared/api/useApi";
import type { AddCartItemInput, Cart } from "./types";

export const cartKey = (userId: string | null | undefined) => ["cart", userId] as const;

export function useCart() {
  const { isLoaded, isSignedIn, userId } = useAuth();
  const api = useApi();

  return useQuery({
    queryKey: cartKey(userId),
    queryFn: ({ signal }) => api<Cart>("/cart", { signal }),
    enabled: isLoaded && Boolean(isSignedIn) && Boolean(userId),
    refetchOnWindowFocus: true,
  });
}

function useCartMutation<T>(request: (input: T) => Promise<Cart>) {
  const { isLoaded, isSignedIn, userId } = useAuth();
  const client = useQueryClient();

  return useMutation({
    mutationFn: (input: T) => {
      if (!isLoaded || !isSignedIn || !userId) {
        throw new ApiError(
          401,
          "not_authenticated",
          "Debes iniciar sesión para modificar el carrito.",
        );
      }
      return request(input);
    },
    // Evita que una consulta anterior sobrescriba la respuesta de una modificación.
    onMutate: async () => {
      const queryKey = cartKey(userId);
      await client.cancelQueries({ queryKey });
      return queryKey;
    },
    onSuccess: (cart, _input, queryKey) => {
      client.setQueryData(queryKey, cart);
      // Confirma el estado persistido sin retrasar la respuesta de la operación.
      void client.invalidateQueries({ queryKey });
      void client.invalidateQueries({ queryKey: ["catalog"] });
    },
    onError: (error) => {
      if (error instanceof ApiError && error.code === "out_of_stock") {
        void client.invalidateQueries({ queryKey: ["catalog"] });
      }
    },
  });
}

export function useAddCartItem() {
  const api = useApi();
  return useCartMutation((input: AddCartItemInput) =>
    api<Cart>("/cart/items", { method: "POST", json: input }),
  );
}

export function useRemoveCartItem() {
  const api = useApi();
  return useCartMutation((itemId: number) =>
    api<Cart>(`/cart/items/${itemId}`, { method: "DELETE" }),
  );
}

export function useReReserveCartItem() {
  const api = useApi();
  return useCartMutation((itemId: number) =>
    api<Cart>(`/cart/items/${itemId}/re-reserve`, { method: "POST" }),
  );
}

export function useUpdateCartItem() {
  const api = useApi();
  return useCartMutation(({ itemId, quantity }: { itemId: number; quantity: number }) => {
    if (!Number.isInteger(quantity) || quantity < 1) {
      throw new ApiError(
        400,
        "validation_error",
        "La cantidad debe ser un entero mayor o igual a 1.",
      );
    }
    return api<Cart>(`/cart/items/${itemId}`, { method: "PATCH", json: { quantity } });
  });
}
