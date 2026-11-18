import { useAuth } from "@clerk/react";
import { Link } from "react-router";
import { useCart } from "./api";

export function CartCounter() {
  const { isLoaded, isSignedIn } = useAuth();
  const { data, isPending, isError } = useCart();
  const count = !isLoaded ? "…" : !isSignedIn ? 0 : (data?.total_items ?? (isPending ? "…" : "—"));

  return (
    <Link to="/carrito" aria-label="Ver carrito">
      <span
        role="status"
        aria-label="Artículos en el carrito"
        title={isSignedIn && isError ? "No se pudo actualizar el carrito." : undefined}
        className="inline-flex min-h-11 items-center rounded-[2px] border border-border px-3.5 py-2 text-sm font-semibold"
      >
        Carrito: {count}
      </span>
    </Link>
  );
}
