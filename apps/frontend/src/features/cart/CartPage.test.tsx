import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, renderHook, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { StoreLayout } from "@/app/layouts/StoreLayout";
import { RequireAuth } from "@/features/auth/RequireAuth";
import { CartPage } from "./CartPage";
import { useUpdateCartItem } from "./api";
import type { Cart, CartItem } from "./types";

const session = vi.hoisted(() => ({
  isLoaded: true,
  isSignedIn: true,
  userId: "customer-a" as string | null,
  getToken: vi.fn(async () => "customer-token"),
}));
vi.mock("@clerk/react", () => ({
  useAuth: () => session,
  useClerk: () => ({ signOut: vi.fn() }),
}));

const first: CartItem = {
  id: 10,
  variant_id: 101,
  product_id: 1,
  product_name: "Camiseta RM",
  product_slug: "camiseta-rm",
  color: "Negro",
  size: "M",
  quantity: 1,
  unit_price: "10000",
  subtotal: "10000",
  reservation_expires_at: null,
  is_reservation_active: false,
  time_remaining_seconds: 0,
  reservation_status: "expired",
  reservation_message: "Tu reserva expiró",
};
const second: CartItem = {
  ...first,
  id: 20,
  variant_id: 201,
  product_id: 2,
  product_name: "Buzo RM",
  product_slug: "buzo-rm",
  color: "Gris",
  size: "L",
  unit_price: "20000",
  subtotal: "20000",
};
const initialCart: Cart = { id: 1, total_items: 2, total_price: "30000", items: [first, second] };
const emptyCart: Cart = { id: 1, total_items: 0, total_price: "0", items: [] };
const fetchMock = vi.fn();
let savedCart: Cart;
let getResponse: () => Response | Promise<Response>;
let mutationResponse: () => Response | Promise<Response>;

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}
function respondWithCart(cart: Cart) {
  mutationResponse = () => {
    savedCart = cart;
    return json(cart);
  };
}
function calls(method: string) {
  return fetchMock.mock.calls.filter(([, init]) => (init?.method ?? "GET") === method);
}
function row(name = "Camiseta RM, Negro, M") {
  return within(screen.getByRole("listitem", { name }));
}
function count() {
  return screen.getByLabelText("Artículos en el carrito");
}
function total() {
  return screen.getByLabelText("Total del carrito");
}
function mount(initialEntry = "/carrito") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[initialEntry]}>
        <Routes>
          <Route element={<StoreLayout />}>
            <Route element={<RequireAuth />}>
              <Route path="/carrito" element={<CartPage />} />
            </Route>
            <Route path="/" element={<p>Catálogo</p>} />
            <Route path="/ingresar" element={<h1>Iniciar sesión</h1>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  Object.assign(session, { isLoaded: true, isSignedIn: true, userId: "customer-a" });
  savedCart = initialCart;
  getResponse = () => json(savedCart);
  mutationResponse = () => json(savedCart);
  fetchMock.mockReset();
  fetchMock.mockImplementation(async (url: string, init?: RequestInit) => {
    const path = new URL(url).pathname;
    if (path === "/api/v1/cart" && !init?.method) return getResponse();
    if (
      /^\/api\/v1\/cart\/items\/\d+$/.test(path) &&
      ["PATCH", "DELETE"].includes(init?.method ?? "")
    )
      return mutationResponse();
    throw new Error(`Solicitud inesperada: ${path}`);
  });
  vi.stubGlobal("fetch", fetchMock);
});
afterEach(() => vi.unstubAllGlobals());

describe("HU-14 y HU-15: página del carrito", () => {
  it("consulta con token y muestra nombre, variante, cantidad, precio, subtotales y total", async () => {
    mount();
    await screen.findByRole("list", { name: "Artículos del carrito" });
    expect(row().getByText("Color: Negro · Talla: M")).toBeInTheDocument();
    expect(row().getByLabelText("Cantidad")).toHaveTextContent("1");
    expect(row().getByText(/Precio unitario:.*10\.000/)).toBeInTheDocument();
    expect(row().getByText(/Subtotal:.*10\.000/)).toBeInTheDocument();
    expect(total()).toHaveTextContent(/30\.000/);
    expect(count()).toHaveTextContent("Carrito: 2");
    expect(new Headers(calls("GET")[0][1].headers).get("Authorization")).toBe(
      "Bearer customer-token",
    );
  });

  it("permite abrir /carrito desde el contador del encabezado", async () => {
    mount("/");
    await userEvent.click(screen.getByRole("link", { name: "Ver carrito" }));
    expect(await screen.findByRole("heading", { name: "Tu carrito" })).toBeInTheDocument();
    expect(await screen.findByRole("list", { name: "Artículos del carrito" })).toBeInTheDocument();
  });

  it("redirige visitantes sin solicitar el carrito", async () => {
    Object.assign(session, { isSignedIn: false, userId: null });
    mount();
    expect(await screen.findByRole("heading", { name: "Iniciar sesión" })).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("elimina un artículo con reserva vencida, conserva el otro y actualiza importes y contador", async () => {
    mount();
    await screen.findByRole("list", { name: "Artículos del carrito" });
    respondWithCart({ id: 1, total_items: 1, total_price: "20000", items: [second] });
    await userEvent.click(row().getByRole("button", { name: "Eliminar" }));
    await waitFor(() =>
      expect(screen.queryByRole("heading", { name: first.product_name })).not.toBeInTheDocument(),
    );
    expect(calls("DELETE")).toHaveLength(1);
    expect(calls("DELETE")[0][0]).toMatch(/\/api\/v1\/cart\/items\/10$/);
    expect(row("Buzo RM, Gris, L").getByLabelText("Cantidad")).toHaveTextContent("1");
    expect(row("Buzo RM, Gris, L").getByText(/Subtotal:.*20\.000/)).toBeInTheDocument();
    expect(total()).toHaveTextContent(/20\.000/);
    expect(count()).toHaveTextContent("Carrito: 1");
  });

  it("elimina el último artículo y muestra exactamente el estado vacío", async () => {
    savedCart = { id: 1, total_items: 1, total_price: "10000", items: [first] };
    mount();
    await screen.findByRole("list", { name: "Artículos del carrito" });
    respondWithCart(emptyCart);
    await userEvent.click(row().getByRole("button", { name: "Eliminar" }));
    expect(await screen.findByText("Tu carrito está vacío", { exact: true })).toBeInTheDocument();
    expect(count()).toHaveTextContent("Carrito: 0");
    expect(screen.queryByRole("list")).not.toBeInTheDocument();
  });

  it("aumenta y disminuye con cantidades absolutas y usa los importes del servidor", async () => {
    mount();
    await screen.findByRole("list", { name: "Artículos del carrito" });
    respondWithCart({
      ...initialCart,
      total_items: 3,
      total_price: "40000",
      items: [{ ...first, quantity: 2, subtotal: "20000" }, second],
    });
    await userEvent.click(row().getByRole("button", { name: "Aumentar cantidad" }));
    await waitFor(() => expect(row().getByLabelText("Cantidad")).toHaveTextContent("2"));
    expect(JSON.parse(calls("PATCH")[0][1].body)).toEqual({ quantity: 2 });
    expect(calls("PATCH")[0][0]).toMatch(/\/cart\/items\/10$/);
    expect(row().getByText(/Subtotal:.*20\.000/)).toBeInTheDocument();
    expect(total()).toHaveTextContent(/40\.000/);
    expect(count()).toHaveTextContent("Carrito: 3");
    respondWithCart(initialCart);
    await userEvent.click(row().getByRole("button", { name: "Disminuir cantidad" }));
    await waitFor(() => expect(row().getByLabelText("Cantidad")).toHaveTextContent("1"));
    expect(JSON.parse(calls("PATCH")[1][1].body)).toEqual({ quantity: 1 });
    expect(total()).toHaveTextContent(/30\.000/);
    expect(count()).toHaveTextContent("Carrito: 2");
  });

  it("conserva cantidad, subtotal y total cuando supera el stock y muestra el máximo del backend", async () => {
    mount();
    await screen.findByRole("list", { name: "Artículos del carrito" });
    mutationResponse = () =>
      json(
        {
          code: "out_of_stock",
          message: "No hay disponibilidad suficiente.",
          fields: { max_available: 1 },
        },
        400,
      );
    await userEvent.click(row().getByRole("button", { name: "Aumentar cantidad" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("No hay disponibilidad suficiente.");
    expect(screen.getByText("Máximo disponible: 1")).toBeInTheDocument();
    expect(row().getByLabelText("Cantidad")).toHaveTextContent("1");
    expect(row().getByText(/Subtotal:.*10\.000/)).toBeInTheDocument();
    expect(total()).toHaveTextContent(/30\.000/);
    expect(count()).toHaveTextContent("Carrito: 2");
  });

  it("deshabilita disminuir en 1 y no envía cantidades cero o negativas", async () => {
    mount();
    await screen.findByRole("list", { name: "Artículos del carrito" });
    const decrease = row().getByRole("button", { name: "Disminuir cantidad" });
    expect(decrease).toBeDisabled();
    await userEvent.click(decrease);
    await userEvent.click(decrease);
    expect(calls("PATCH")).toHaveLength(0);
    expect(row().getByLabelText("Cantidad")).toHaveTextContent("1");
  });

  it.each(["PATCH", "DELETE"])(
    "conserva los artículos y cantidades si falla %s por conexión",
    async (method) => {
      mount();
      await screen.findByRole("list", { name: "Artículos del carrito" });
      mutationResponse = () => Promise.reject(new TypeError("Failed to fetch"));
      await userEvent.click(
        row().getByRole("button", { name: method === "PATCH" ? "Aumentar cantidad" : "Eliminar" }),
      );
      expect(await screen.findByRole("alert")).toHaveTextContent(
        "No pudimos conectar con el servidor",
      );
      expect(screen.getAllByRole("listitem")).toHaveLength(2);
      expect(row().getByLabelText("Cantidad")).toHaveTextContent("1");
      expect(total()).toHaveTextContent(/30\.000/);
      expect(count()).toHaveTextContent("Carrito: 2");
    },
  );

  it.each(["PATCH", "DELETE"])(
    "evita peticiones duplicadas y otras modificaciones mientras está pendiente %s",
    async (method) => {
      mount();
      await screen.findByRole("list", { name: "Artículos del carrito" });
      let resolve!: (response: Response) => void;
      mutationResponse = () =>
        new Promise((done) => {
          resolve = done;
        });
      await userEvent.click(
        row().getByRole("button", { name: method === "PATCH" ? "Aumentar cantidad" : "Eliminar" }),
      );
      await screen.findByText("Actualizando carrito…");
      for (const button of within(
        screen.getByRole("list", { name: "Artículos del carrito" }),
      ).getAllByRole("button"))
        expect(button).toBeDisabled();
      await userEvent.click(row().getByRole("button", { name: "Aumentar cantidad" }));
      await userEvent.click(row("Buzo RM, Gris, L").getByRole("button", { name: "Eliminar" }));
      expect(calls("PATCH").length + calls("DELETE").length).toBe(1);
      resolve(json(savedCart));
      await waitFor(() =>
        expect(screen.queryByText("Actualizando carrito…")).not.toBeInTheDocument(),
      );
    },
  );

  it("recupera desde GET el carrito modificado al recargar con una caché nueva", async () => {
    const view = mount();
    await screen.findByRole("list", { name: "Artículos del carrito" });
    respondWithCart({ id: 1, total_items: 1, total_price: "20000", items: [second] });
    await userEvent.click(row().getByRole("button", { name: "Eliminar" }));
    await waitFor(() => expect(screen.getAllByRole("listitem")).toHaveLength(1));
    view.unmount();
    mount();
    expect(await screen.findByRole("heading", { name: "Buzo RM" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Camiseta RM" })).not.toBeInTheDocument();
    expect(total()).toHaveTextContent(/20\.000/);
    expect(count()).toHaveTextContent("Carrito: 1");
    expect(calls("DELETE")).toHaveLength(1);
  });

  it("muestra carga, error de consulta y permite reintentar sin confundirlos con un carrito vacío", async () => {
    let resolve!: (response: Response) => void;
    getResponse = () =>
      new Promise((done) => {
        resolve = done;
      });
    mount();
    expect(screen.getByText("Cargando…")).toBeInTheDocument();
    expect(screen.queryByText("Tu carrito está vacío")).not.toBeInTheDocument();
    await waitFor(() => expect(calls("GET")).toHaveLength(1));
    resolve(
      json({ code: "server_error", message: "No se pudo consultar el carrito.", fields: {} }, 500),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent("No se pudo consultar el carrito.");
    expect(screen.queryByText("Tu carrito está vacío")).not.toBeInTheDocument();
    getResponse = () => json(savedCart);
    await userEvent.click(screen.getByRole("button", { name: "Reintentar" }));
    expect(await screen.findByRole("list", { name: "Artículos del carrito" })).toBeInTheDocument();
  });

  it.each([0, -1])(
    "rechaza cantidad inválida %s también en el hook sin enviar PATCH",
    async (quantity) => {
      const client = new QueryClient();
      const { result } = renderHook(() => useUpdateCartItem(), {
        wrapper: ({ children }) => (
          <QueryClientProvider client={client}>{children}</QueryClientProvider>
        ),
      });
      await act(async () => {
        await expect(
          result.current.mutateAsync({ itemId: first.id, quantity }),
        ).rejects.toMatchObject({ code: "validation_error" });
      });
      expect(fetchMock).not.toHaveBeenCalled();
    },
  );
});
