import { useUser } from "@clerk/react";
import { Link, NavLink, Outlet } from "react-router";
import { SessionControls } from "@/features/auth/SessionControls";
import { BrandLogo } from "@/shared/ui/BrandLogo";

const links = [
  { to: "/admin/productos", label: "Productos" },
  { to: "/admin/inventario", label: "Inventario" },
  { to: "/admin/pedidos", label: "Pedidos" },
  { to: "/admin/administradores", label: "Administradores" },
];

export function AdminLayout() {
  const { user } = useUser();
  const isAdmin = user?.publicMetadata.role === "admin";

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border bg-background">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-4 py-3 sm:px-6">
          <div className="flex flex-wrap items-center gap-6">
            <Link
              to={isAdmin ? "/admin/productos" : "/admin/ingresar"}
              className="inline-flex min-h-11 items-center rounded-[2px]"
            >
              <BrandLogo subtitle="Panel de administración" />
            </Link>
            {isAdmin && (
              <nav aria-label="Panel de administración">
                <ul className="flex flex-wrap items-center gap-2 text-sm">
                  {links.map((link) => (
                    <li key={link.to}>
                      <NavLink
                        to={link.to}
                        className={({ isActive }) =>
                          `inline-flex min-h-11 items-center rounded-[2px] border px-3.5 py-2 font-medium transition-colors ${
                            isActive
                              ? "border-primary bg-primary text-primary-foreground"
                              : "border-transparent text-foreground hover:bg-surface-alt"
                          }`
                        }
                      >
                        {link.label}
                      </NavLink>
                    </li>
                  ))}
                </ul>
              </nav>
            )}
          </div>
          {isAdmin && <SessionControls />}
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6">
        <Outlet />
      </main>
    </div>
  );
}
