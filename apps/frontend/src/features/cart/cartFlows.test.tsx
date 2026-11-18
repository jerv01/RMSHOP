import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { StoreLayout } from "@/app/layouts/StoreLayout";
import { ProductDetailPage } from "@/features/catalog/ProductDetailPage";
import type { CatalogProduct } from "@/features/catalog/types";
import { cartKey } from "./api";
import type { Cart } from "./types";

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

const product: CatalogProduct = {
  id: 1,
  name: "Camiseta RM",
  slug: "camiseta-rm",
  description: "Camiseta de algodón",
  price: "75000",
  previous_price: null,
  material: "Algodón",
  category: { id: 1, name: "Camisetas", slug: "camisetas" },
  status: "published",
  created_at: "2026-11-01T00:00:00Z",
  updated_at: "2026-11-01T00:00:00Z",
  variants: [
    {
      id: 101,
      product_id: 1,
      color: "Negro",
      size: "M",
      stock_quantity: 5,
      created_at: "",
      updated_at: "",
    },
    {
      id: 102,
      product_id: 1,
      color: "Blanco",
      size: "M",
      stock_quantity: 5,
      created_at: "",
      updated_at: "",
    },
    {
      id: 103,
      product_id: 1,
      color: "Blanco",
      size: "L",
      stock_quantity: 5,
      created_at: "",
      updated_at: "",
    },
  ],
};

const emptyCart: Cart = { id: 1, total_items: 0, total_price: "0", items: [] };

function cartWithItem(variantId = 101, quantity = 1): Cart {
  const variant = product.variants!.find((item) => item.id === variantId)!;
  return {
    id: 1,
    total_items: quantity,
    total_price: String(quantity * 75000),
    items: [
      {
        id: 10,
        variant_id: variantId,
        product_id: product.id,
        product_name: product.name,
        product_slug: product.slug,
        color: variant.color,
        size: variant.size,
        quantity,
        unit_price: "75000",
        subtotal: String(quantity * 75000),
        reservation_expires_at: "2026-11-18T01:15:00Z",
        is_reservation_active: true,
        time_remaining_seconds: 900,
        reservation_status: "active",
        reservation_message: null,
      },
    ],
  };
}

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const fetchMock = vi.fn();
let savedCart: Cart;
let currentProduct: CatalogProduct;
let postResponse: (input: { variant_id: number; quantity: number }) => Response | Promise<Response>;

function renderStore(client = new QueryClient({ defaultOptions: { queries: { retry: false } } })) {
  const view = () => (
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={["/producto/camiseta-rm"]}>
        <Routes>
          <Route element={<StoreLayout />}>
            <Route path="/producto/:slug" element={<ProductDetailPage />} />
            <Route path="/ingresar" element={<h1>Iniciar sesión</h1>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
  return { ...render(view()), client, view };
}

function callsTo(path: string, method = "GET") {
  return fetchMock.mock.calls.filter(
    ([url, init]) =>
      new URL(url).pathname === `/api/v1${path}` && (init?.method ?? "GET") === method,
  );
}

beforeEach(() => {
  Object.assign(session, { isLoaded: true, isSignedIn: true, userId: "customer-a" });
  session.getToken.mockClear();
  savedCart = emptyCart;
  currentProduct = product;
  postResponse = ({ variant_id }) => {
    savedCart = cartWithItem(variant_id);
    return json(savedCart);
  };
  fetchMock.mockReset();
  fetchMock.mockImplementation(async (url: string, init?: RequestInit) => {
    const path = new URL(url).pathname;
    if (path === "/api/v1/products/camiseta-rm") return json(currentProduct);
    if (path === "/api/v1/cart" && !init?.method) return json(savedCart);
    if (path === "/api/v1/cart/items" && init?.method === "POST") {
      return postResponse(JSON.parse(init.body as string));
    }
    throw new Error(`Solicitud inesperada: ${init?.method ?? "GET"} ${path}`);
  });
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => vi.unstubAllGlobals());

describe("HU-13: agregar variantes al carrito", () => {
  it("envía la combinación exacta con cantidad 1 y token, muestra éxito y confirma el ítem mediante GET", async () => {
    const { client } = renderStore();
    await screen.findByRole("heading", { name: product.name });
    await userEvent.click(screen.getByRole("button", { name: "Blanco" }));
    await userEvent.click(screen.getByRole("button", { name: "L" }));
    await userEvent.click(screen.getByRole("button", { name: "Agregar al carrito" }));

    expect(await screen.findByText("Producto agregado al carrito")).toBeInTheDocument();
    expect(screen.getByLabelText("Artículos en el carrito")).toHaveTextContent("Carrito: 1");
    const posts = callsTo("/cart/items", "POST");
    expect(posts).toHaveLength(1);
    expect(JSON.parse(posts[0][1].body)).toEqual({ variant_id: 103, quantity: 1 });
    expect(new Headers(posts[0][1].headers).get("Authorization")).toBe("Bearer customer-token");
    await waitFor(() => expect(callsTo("/cart")).toHaveLength(2));
    await waitFor(() => expect(client.isFetching({ queryKey: cartKey("customer-a") })).toBe(0));
    expect(client.getQueryData<Cart>(cartKey("customer-a"))?.items).toEqual([
      expect.objectContaining({
        variant_id: 103,
        product_name: product.name,
        color: "Blanco",
        size: "L",
        quantity: 1,
      }),
    ]);
  });

  it("usa total_items del servidor y conserva su acumulación al agregar otra vez la misma variante", async () => {
    savedCart = cartWithItem(101, 3);
    const { client } = renderStore();
    await waitFor(() =>
      expect(screen.getByLabelText("Artículos en el carrito")).toHaveTextContent("Carrito: 3"),
    );
    postResponse = () => {
      savedCart = cartWithItem(101, 4);
      return json(savedCart);
    };
    await userEvent.click(await screen.findByRole("button", { name: "Agregar al carrito" }));
    await waitFor(() =>
      expect(screen.getByLabelText("Artículos en el carrito")).toHaveTextContent("Carrito: 4"),
    );
    postResponse = () => {
      savedCart = cartWithItem(101, 5);
      return json(savedCart);
    };
    await userEvent.click(screen.getByRole("button", { name: "Agregar al carrito" }));
    await waitFor(() =>
      expect(screen.getByLabelText("Artículos en el carrito")).toHaveTextContent("Carrito: 5"),
    );
    expect(callsTo("/cart/items", "POST").map(([, init]) => JSON.parse(init.body))).toEqual([
      { variant_id: 101, quantity: 1 },
      { variant_id: 101, quantity: 1 },
    ]);
    expect(client.getQueryData<Cart>(cartKey("customer-a"))?.items).toHaveLength(1);
  });

  it("redirige al visitante a /ingresar sin consultar ni modificar el carrito", async () => {
    Object.assign(session, { isSignedIn: false, userId: null });
    renderStore();
    await userEvent.click(await screen.findByRole("button", { name: "Agregar al carrito" }));
    expect(await screen.findByRole("heading", { name: "Iniciar sesión" })).toBeInTheDocument();
    expect(callsTo("/cart/items", "POST")).toHaveLength(0);
    expect(callsTo("/cart")).toHaveLength(0);
    expect(session.getToken).not.toHaveBeenCalled();
  });

  it("espera a que Clerk cargue antes de permitir agregar", async () => {
    Object.assign(session, { isLoaded: false, isSignedIn: false, userId: null });
    renderStore();
    const button = await screen.findByRole("button", { name: "Agregar al carrito" });
    expect(button).toBeDisabled();
    await userEvent.click(button);
    expect(callsTo("/cart/items", "POST")).toHaveLength(0);
    expect(callsTo("/cart")).toHaveLength(0);
  });

  it("mantiene deshabilitado el botón para una variante agotada o una combinación inexistente", async () => {
    currentProduct = {
      ...product,
      variants: product.variants!.map((v) => ({ ...v, stock_quantity: 0 })),
    };
    renderStore();
    const button = await screen.findByRole("button", { name: "Agotado" });
    expect(button).toBeDisabled();
    await userEvent.click(button);
    await userEvent.click(screen.getByRole("button", { name: /L/ }));
    expect(button).toBeDisabled();
    expect(callsTo("/cart/items", "POST")).toHaveLength(0);
  });

  it("maneja out_of_stock sin éxito ni incremento del contador y vuelve a consultar el catálogo", async () => {
    savedCart = cartWithItem(101, 2);
    renderStore();
    await waitFor(() =>
      expect(screen.getByLabelText("Artículos en el carrito")).toHaveTextContent("Carrito: 2"),
    );
    postResponse = () => {
      currentProduct = {
        ...product,
        variants: product.variants!.map((v) => ({ ...v, stock_quantity: 0 })),
      };
      return json({ code: "out_of_stock", message: "Stock insuficiente.", fields: {} }, 400);
    };
    await userEvent.click(await screen.findByRole("button", { name: "Agregar al carrito" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Ya no hay disponibilidad");
    expect(screen.queryByText("Producto agregado al carrito")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Artículos en el carrito")).toHaveTextContent("Carrito: 2");
    await waitFor(() => expect(callsTo("/products/camiseta-rm")).toHaveLength(2));
    expect(await screen.findByRole("button", { name: "Agotado" })).toBeDisabled();
  });

  it("retira la confirmación anterior si un segundo intento falla", async () => {
    renderStore();
    await userEvent.click(await screen.findByRole("button", { name: "Agregar al carrito" }));
    await screen.findByText("Producto agregado al carrito");
    postResponse = () => json({ code: "out_of_stock", message: "Sin stock.", fields: {} }, 400);
    await userEvent.click(screen.getByRole("button", { name: "Agregar al carrito" }));
    await screen.findByRole("alert");
    expect(screen.queryByText("Producto agregado al carrito")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Artículos en el carrito")).toHaveTextContent("Carrito: 1");
  });

  it("bloquea nuevos clics mientras agrega y muestra errores de conexión sin éxito", async () => {
    let rejectPost!: (error: Error) => void;
    postResponse = () =>
      new Promise((_resolve, reject) => {
        rejectPost = reject;
      });
    renderStore();
    await userEvent.click(await screen.findByRole("button", { name: "Agregar al carrito" }));
    const button = await screen.findByRole("button", { name: "Agregando…" });
    expect(button).toBeDisabled();
    await userEvent.click(button);
    expect(callsTo("/cart/items", "POST")).toHaveLength(1);
    rejectPost(new TypeError("Failed to fetch"));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "No pudimos conectar con el servidor",
    );
    expect(screen.queryByText("Producto agregado al carrito")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Artículos en el carrito")).toHaveTextContent("Carrito: 0");
  });

  it("recupera el carrito desde GET al recargar con una caché nueva", async () => {
    const first = renderStore();
    await userEvent.click(await screen.findByRole("button", { name: "Agregar al carrito" }));
    await screen.findByText("Producto agregado al carrito");
    first.unmount();
    const { client } = renderStore();
    await waitFor(() =>
      expect(screen.getByLabelText("Artículos en el carrito")).toHaveTextContent("Carrito: 1"),
    );
    expect(client.getQueryData<Cart>(cartKey("customer-a"))?.items[0].variant_id).toBe(101);
    expect(callsTo("/cart/items", "POST")).toHaveLength(1);
  });

  it("no muestra el contador de otro usuario al cambiar de sesión o salir", async () => {
    savedCart = cartWithItem(101, 3);
    const { rerender, view } = renderStore();
    await waitFor(() =>
      expect(screen.getByLabelText("Artículos en el carrito")).toHaveTextContent("Carrito: 3"),
    );
    savedCart = emptyCart;
    session.userId = "customer-b";
    rerender(view());
    await waitFor(() =>
      expect(screen.getByLabelText("Artículos en el carrito")).toHaveTextContent("Carrito: 0"),
    );
    Object.assign(session, { isSignedIn: false, userId: null });
    rerender(view());
    expect(screen.getByLabelText("Artículos en el carrito")).toHaveTextContent("Carrito: 0");
  });
});
