import { createBrowserRouter } from "react-router";
import { StoreLayout } from "./layouts/StoreLayout";
import { HomePage } from "./pages/HomePage";
import { NotFoundPage } from "./pages/NotFoundPage";

export const router = createBrowserRouter([
  {
    element: <StoreLayout />,
    children: [
      { path: "/", element: <HomePage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);
