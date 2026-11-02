import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SessionControls } from "./SessionControls";

const signOut = vi.fn();
let session = { isLoaded: true, isSignedIn: false };

vi.mock("@clerk/react", () => ({
  useAuth: () => session,
  useClerk: () => ({ signOut }),
}));

function setup() {
  render(
    <MemoryRouter>
      <SessionControls />
    </MemoryRouter>,
  );
}

describe("SessionControls", () => {
  beforeEach(() => signOut.mockReset());

  it("ofrece ingresar y registrarse sin sesión", () => {
    session = { isLoaded: true, isSignedIn: false };
    setup();

    expect(screen.getByRole("link", { name: "Ingresar" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Registrarse" })).toBeInTheDocument();
  });

  it("cierra la sesión con el botón", async () => {
    session = { isLoaded: true, isSignedIn: true };
    setup();

    await userEvent.click(screen.getByRole("button", { name: "Cerrar sesión" }));

    expect(signOut).toHaveBeenCalledOnce();
  });

  it("no muestra nada mientras Clerk carga", () => {
    session = { isLoaded: false, isSignedIn: false };
    setup();

    expect(screen.queryByRole("button")).not.toBeInTheDocument();
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
  });
});
