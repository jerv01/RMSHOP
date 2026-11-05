import { useAuth } from "@clerk/react";
import { Link, NavLink, Outlet } from "react-router";
import { SessionControls } from "@/features/auth/SessionControls";
import { ProductSessionProvider } from "@/features/admin/products/ProductSession";

export function AdminLayout() {
  const { userId, isSignedIn } = useAuth();
  return (
    <ProductSessionProvider key={userId ?? "anonymous"}>
      <div className="admin-shell min-h-screen">
        <header className="border-b border-border bg-white">
          <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-5 py-5">
            <Link to="/admin/productos" className="text-xl font-semibold tracking-tight">
              RM <span className="font-normal">Shop</span>
              <span className="ml-3 text-xs font-normal uppercase tracking-widest muted">
                Administración
              </span>
            </Link>
            <div className="flex items-center gap-5">
              <Link className="text-sm text-link" to="/">
                Ver tienda
              </Link>
              {isSignedIn && <SessionControls />}
            </div>
          </div>
          {isSignedIn && (
            <nav aria-label="Administración" className="mx-auto flex max-w-6xl gap-6 px-5">
              <NavLink
                className={({ isActive }) => `admin-nav ${isActive ? "active" : ""}`}
                to="/admin/productos"
              >
                Productos
              </NavLink>
              <NavLink
                className={({ isActive }) => `admin-nav ${isActive ? "active" : ""}`}
                to="/admin/inventario"
              >
                Inventario
              </NavLink>
            </nav>
          )}
        </header>
        <main className="mx-auto max-w-6xl px-5 py-8 sm:py-12">
          <Outlet />
        </main>
      </div>
    </ProductSessionProvider>
  );
}
