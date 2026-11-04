import { useUser } from "@clerk/react";
import { NavLink, Outlet } from "react-router";

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
    <div className="min-h-screen">
      <header className="flex flex-wrap items-center gap-6 border-b border-gray-200 p-4">
        <span className="text-lg font-semibold">RM Shop · Panel de administración</span>
        {isAdmin && (
          <nav aria-label="Panel de administración">
            <ul className="flex gap-4 text-sm">
              {links.map((link) => (
                <li key={link.to}>
                  <NavLink
                    to={link.to}
                    className={({ isActive }) => (isActive ? "font-semibold underline" : "")}
                  >
                    {link.label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </nav>
        )}
      </header>
      <main className="p-4">
        <Outlet />
      </main>
    </div>
  );
}
