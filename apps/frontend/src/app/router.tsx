import { createBrowserRouter, Navigate } from "react-router";
import { AdminSignInPage } from "@/features/auth/AdminSignInPage";
import { AdminSignUpPage } from "@/features/auth/AdminSignUpPage";
import { RequireAdmin } from "@/features/auth/RequireAdmin";
import { SignInPage } from "@/features/auth/SignInPage";
import { SignUpPage } from "@/features/auth/SignUpPage";
import { DataPolicyPage } from "@/features/legal/DataPolicyPage";
import { AdminLayout } from "./layouts/AdminLayout";
import { StoreLayout } from "./layouts/StoreLayout";
import { HomePage } from "./pages/HomePage";
import { NotFoundPage } from "./pages/NotFoundPage";

export const router = createBrowserRouter([
  {
    element: <StoreLayout />,
    children: [
      { path: "/", element: <HomePage /> },
      { path: "/ingresar/*", element: <SignInPage /> },
      { path: "/login/*", element: <Navigate to="/ingresar" replace /> },
      { path: "/registro/*", element: <SignUpPage /> },
      { path: "/datos-personales", element: <DataPolicyPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
  {
    element: <AdminLayout />,
    children: [
      { path: "/admin/ingresar/*", element: <AdminSignInPage /> },
      { path: "/admin/registro/*", element: <AdminSignUpPage /> },
      {
        // El panel se carga bajo demanda: los clientes no descargan su código.
        element: <RequireAdmin />,
        children: [
          { path: "/admin", element: <Navigate to="/admin/productos" replace /> },
          {
            path: "/admin/productos",
            lazy: async () => ({
              Component: (await import("@/features/admin/products/ProductsPage")).ProductsPage,
            }),
          },
          {
            path: "/admin/inventario",
            lazy: async () => ({
              Component: (await import("@/features/admin/inventory/InventoryPage")).InventoryPage,
            }),
          },
          {
            path: "/admin/administradores",
            lazy: async () => ({
              Component: (await import("@/features/admin/administrators/AdministratorsPage"))
                .AdministratorsPage,
            }),
          },
          {
            path: "/admin/pedidos",
            lazy: async () => ({
              Component: (await import("@/features/admin/orders/OrdersPage")).OrdersPage,
            }),
          },
        ],
      },
    ],
  },
]);
