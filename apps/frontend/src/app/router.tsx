import { createBrowserRouter } from "react-router";
import { AdminSignInPage } from "@/features/auth/AdminSignInPage";
import { RequireAdmin } from "@/features/auth/RequireAdmin";
import { SignInPage } from "@/features/auth/SignInPage";
import { SignUpPage } from "@/features/auth/SignUpPage";
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
      { path: "/registro/*", element: <SignUpPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
  {
    element: <AdminLayout />,
    children: [
      { path: "/admin/ingresar/*", element: <AdminSignInPage /> },
      {
        // El panel se carga bajo demanda: los clientes no descargan su código.
        element: <RequireAdmin />,
        children: [
          {
            path: "/admin/productos/nuevo",
            lazy: async () => ({
              Component: (await import("@/features/admin/products/ProductCreatePage"))
                .ProductCreatePage,
            }),
          },
          {
            path: "/admin/productos/:id",
            lazy: async () => ({
              Component: (await import("@/features/admin/products/ProductEditPage"))
                .ProductEditPage,
            }),
          },
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
