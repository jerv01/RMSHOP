import { render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider, type RouteObject } from "react-router";

/** Estado de sesión que controlan las pruebas; `vi.mock("@clerk/react")` lo lee. */
export interface FakeSession {
  isLoaded: boolean;
  isSignedIn: boolean;
  role?: string;
}

/** Monta `guard` como ruta de protección de `/protegida` y devuelve lo que ve el usuario. */
export function renderGuarded(guard: RouteObject["element"], signInPath: string) {
  const router = createMemoryRouter(
    [
      { element: guard, children: [{ path: "/protegida", element: <p>Contenido protegido</p> }] },
      { path: signInPath, element: <p>Pantalla de ingreso</p> },
      { path: "/", element: <p>Inicio</p> },
    ],
    { initialEntries: ["/protegida"] },
  );
  render(<RouterProvider router={router} />);
  return { router, screen };
}
