import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { RequireAdmin } from "@/features/auth/RequireAdmin";
import { AdministratorsPage } from "./AdministratorsPage";

const session = vi.hoisted(() => ({ role: "admin" as string | undefined }));

vi.mock("@clerk/react", () => ({
  useAuth: () => ({ isLoaded: true, isSignedIn: true, getToken: async () => "token-simulado" }),
  useUser: () => ({ isLoaded: true, user: { publicMetadata: { role: session.role } } }),
  useClerk: () => ({ signOut: vi.fn() }),
}));

interface Admin {
  clerk_user_id: string;
  email: string;
  first_name: string;
  last_name: string;
  is_me: boolean;
}

const me: Admin = {
  clerk_user_id: "user_me",
  email: "yo@rmshop.test",
  first_name: "Yo",
  last_name: "Admin",
  is_me: true,
};
const other: Admin = {
  clerk_user_id: "user_other",
  email: "otra@rmshop.test",
  first_name: "Otra",
  last_name: "Admin",
  is_me: false,
};

let admins: Admin[];
let postResponse: () => Response;
const fetchMock = vi.fn();

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

beforeEach(() => {
  session.role = "admin";
  admins = [me, other];
  postResponse = () => json({ status: "invited", email: "nuevo@rmshop.test" }, 201);
  fetchMock.mockReset();
  fetchMock.mockImplementation(async (url: string, init: RequestInit = {}) => {
    const method = init.method ?? "GET";
    if (method === "DELETE") {
      const id = decodeURIComponent(url.split("/").pop() ?? "");
      admins = admins.filter((admin) => admin.clerk_user_id !== id);
      return new Response(null, { status: 204 });
    }
    if (method === "POST") return postResponse();
    return json(admins);
  });
  vi.stubGlobal("fetch", fetchMock);
});

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={["/admin/administradores"]}>
        <Routes>
          <Route element={<RequireAdmin />}>
            <Route path="/admin/administradores" element={<AdministratorsPage />} />
          </Route>
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

const calls = (method: string) =>
  fetchMock.mock.calls.filter(([, init]) => (init?.method ?? "GET") === method);

describe("AdministratorsPage", () => {
  it("lista los administradores y marca la propia cuenta", async () => {
    renderPage();

    const table = await screen.findByRole("table", { name: "Administradores de la tienda" });
    const rows = within(table).getAllByRole("row");
    expect(rows).toHaveLength(3);
    expect(within(rows[1]).getByText("Yo Admin")).toBeInTheDocument();
    expect(within(rows[1]).getByText("Tú")).toBeInTheDocument();
    expect(within(rows[2]).getByText("otra@rmshop.test")).toBeInTheDocument();
    expect(within(rows[2]).queryByText("Tú")).not.toBeInTheDocument();
    expect(screen.getByText("2 administradores activos")).toBeInTheDocument();
    const headers = fetchMock.mock.calls[0][1].headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer token-simulado");
  });

  it("deshabilita eliminar en la propia cuenta", async () => {
    renderPage();

    expect(await screen.findByRole("button", { name: "Eliminar a Yo Admin" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Eliminar a Otra Admin" })).toBeEnabled();
  });

  it("invita a un correo, confirma el envío y recarga la lista", async () => {
    renderPage();
    await screen.findByRole("table");

    await userEvent.type(
      screen.getByLabelText("Correo del nuevo administrador"),
      "nuevo@rmshop.test",
    );
    await userEvent.click(screen.getByRole("button", { name: "Agregar" }));

    expect(await screen.findByText("Invitación enviada a nuevo@rmshop.test")).toBeInTheDocument();
    expect(JSON.parse(calls("POST")[0][1].body)).toEqual({ email: "nuevo@rmshop.test" });
    expect(calls("GET")).toHaveLength(2);
    expect(screen.getByLabelText("Correo del nuevo administrador")).toHaveValue("");
  });

  it("valida el formato del correo sin llamar a la API", async () => {
    renderPage();
    await screen.findByRole("table");

    await userEvent.type(screen.getByLabelText("Correo del nuevo administrador"), "no-es-correo");
    await userEvent.click(screen.getByRole("button", { name: "Agregar" }));

    const input = screen.getByLabelText("Correo del nuevo administrador");
    const error = await screen.findByText("Ingresa un correo válido.");
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(input.getAttribute("aria-describedby")).toContain(error.id);
    expect(error).toHaveAttribute("aria-live", "polite");
    expect(calls("POST")).toHaveLength(0);
  });

  it("muestra el mensaje de la API cuando el correo es de un cliente", async () => {
    postResponse = () =>
      json(
        {
          code: "email_belongs_to_customer",
          message: "Este correo pertenece a una cuenta de cliente.",
          fields: {},
        },
        409,
      );
    renderPage();
    await screen.findByRole("table");

    await userEvent.type(
      screen.getByLabelText("Correo del nuevo administrador"),
      "cliente@example.com",
    );
    await userEvent.click(screen.getByRole("button", { name: "Agregar" }));

    const error = await screen.findByText("Este correo pertenece a una cuenta de cliente.");
    expect(
      screen.getByLabelText("Correo del nuevo administrador").getAttribute("aria-describedby"),
    ).toContain(error.id);
    expect(screen.queryByText(/Invitación enviada/)).not.toBeInTheDocument();
  });

  it("pide confirmación antes de eliminar y recarga la lista", async () => {
    renderPage();

    await userEvent.click(await screen.findByRole("button", { name: "Eliminar a Otra Admin" }));
    const dialog = await screen.findByRole("alertdialog", { name: "Eliminar administrador" });
    expect(dialog).toHaveTextContent("otra@rmshop.test");
    expect(calls("DELETE")).toHaveLength(0);

    await userEvent.click(within(dialog).getByRole("button", { name: "Eliminar" }));

    await vi.waitFor(() => expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument());
    expect(calls("DELETE")[0][0]).toContain("/api/v1/admin/administrators/user_other");
    expect(screen.queryByText("otra@rmshop.test")).not.toBeInTheDocument();
  });

  it("cancelar no elimina nada y se opera con teclado", async () => {
    renderPage();
    const trigger = await screen.findByRole("button", { name: "Eliminar a Otra Admin" });

    trigger.focus();
    await userEvent.keyboard("{Enter}");
    const dialog = await screen.findByRole("alertdialog");
    expect(within(dialog).getByRole("button", { name: "Cancelar" })).toHaveFocus();
    await userEvent.keyboard("{Escape}");

    await vi.waitFor(() => expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument());
    expect(calls("DELETE")).toHaveLength(0);
    expect(trigger).toHaveFocus();
  });

  it("mantiene el diálogo abierto y muestra el error si la baja falla", async () => {
    fetchMock.mockImplementation(async (_url: string, init: RequestInit = {}) =>
      init.method === "DELETE"
        ? json(
            {
              code: "cannot_delete_last_admin",
              message: "No se puede eliminar la última cuenta de administrador.",
              fields: {},
            },
            409,
          )
        : json(admins),
    );
    renderPage();

    await userEvent.click(await screen.findByRole("button", { name: "Eliminar a Otra Admin" }));
    await userEvent.click(
      within(await screen.findByRole("alertdialog")).getByRole("button", { name: "Eliminar" }),
    );

    expect(
      await screen.findByText("No se puede eliminar la última cuenta de administrador."),
    ).toBeInTheDocument();
    expect(screen.getByRole("alertdialog")).toBeInTheDocument();
  });

  it("niega el acceso sin rol de administrador y no llama a la API", () => {
    session.role = undefined;

    renderPage();

    expect(screen.getByRole("heading", { name: "No tienes permisos" })).toBeInTheDocument();
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
