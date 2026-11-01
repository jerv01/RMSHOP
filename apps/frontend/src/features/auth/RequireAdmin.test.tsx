import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { RequireAdmin } from "./RequireAdmin";
import { renderGuarded, type FakeSession } from "./testUtils";

const session = vi.hoisted<FakeSession>(() => ({ isLoaded: true, isSignedIn: false }));
const signOut = vi.hoisted(() => vi.fn());

vi.mock("@clerk/react", () => ({
  useAuth: () => ({ isLoaded: session.isLoaded, isSignedIn: session.isSignedIn }),
  useUser: () => ({
    isLoaded: session.isLoaded,
    user: session.isSignedIn ? { publicMetadata: { role: session.role } } : null,
  }),
  useClerk: () => ({ signOut }),
}));

beforeEach(() => {
  session.isLoaded = true;
  session.isSignedIn = false;
  session.role = undefined;
  signOut.mockReset();
});

describe("RequireAdmin", () => {
  it("redirige a /admin/ingresar si no hay sesión", () => {
    const { router, screen } = renderGuarded(<RequireAdmin />, "/admin/ingresar");

    expect(screen.getByText("Pantalla de ingreso")).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/admin/ingresar");
  });

  it("muestra 'No tienes permisos' con sesión de cliente", async () => {
    session.isSignedIn = true;

    const { screen } = renderGuarded(<RequireAdmin />, "/admin/ingresar");

    expect(screen.getByRole("heading", { name: "No tienes permisos" })).toBeInTheDocument();
    expect(screen.queryByText("Contenido protegido")).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Ir al inicio" })).toHaveAttribute("href", "/");

    await userEvent.click(screen.getByRole("button", { name: "Cerrar sesión" }));
    expect(signOut).toHaveBeenCalledOnce();
  });

  it("muestra el contenido con sesión de administrador", () => {
    session.isSignedIn = true;
    session.role = "admin";

    const { screen } = renderGuarded(<RequireAdmin />, "/admin/ingresar");

    expect(screen.getByText("Contenido protegido")).toBeInTheDocument();
  });

  it("no decide nada mientras Clerk carga", () => {
    session.isLoaded = false;

    const { screen } = renderGuarded(<RequireAdmin />, "/admin/ingresar");

    expect(screen.getByRole("status")).toHaveTextContent("Cargando");
  });
});
