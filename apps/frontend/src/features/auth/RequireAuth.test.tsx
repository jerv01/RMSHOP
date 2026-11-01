import { beforeEach, describe, expect, it, vi } from "vitest";
import { RequireAuth } from "./RequireAuth";
import { renderGuarded, type FakeSession } from "./testUtils";

const session = vi.hoisted<FakeSession>(() => ({ isLoaded: true, isSignedIn: false }));

vi.mock("@clerk/react", () => ({
  useAuth: () => ({ isLoaded: session.isLoaded, isSignedIn: session.isSignedIn }),
}));

beforeEach(() => {
  session.isLoaded = true;
  session.isSignedIn = false;
});

describe("RequireAuth", () => {
  it("redirige a /ingresar si no hay sesión", () => {
    const { router, screen } = renderGuarded(<RequireAuth />, "/ingresar");

    expect(screen.getByText("Pantalla de ingreso")).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/ingresar");
  });

  it("muestra el contenido con sesión de cliente", () => {
    session.isSignedIn = true;

    const { screen } = renderGuarded(<RequireAuth />, "/ingresar");

    expect(screen.getByText("Contenido protegido")).toBeInTheDocument();
  });

  it("no redirige mientras Clerk carga", () => {
    session.isLoaded = false;

    const { router, screen } = renderGuarded(<RequireAuth />, "/ingresar");

    expect(screen.getByRole("status")).toHaveTextContent("Cargando");
    expect(router.state.location.pathname).toBe("/protegida");
  });
});
