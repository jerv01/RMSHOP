import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { CartCounter } from "./CartCounter";
import { CartPage } from "./CartPage";
import { ReservationCountdown } from "./ReservationCountdown";
import type { Cart, CartItem } from "./types";

vi.mock("@clerk/react", () => ({
  useAuth: () => ({
    isLoaded: true,
    isSignedIn: true,
    userId: "customer-a",
    getToken: async () => "customer-token",
  }),
}));

const start = Date.parse("2026-11-18T12:00:00Z");
let expiresAt: number;
let quantity: number;
let removed: boolean;
let failGet: boolean;
const fetchMock = vi.fn();
let reserveResponse: () => Response | Promise<Response>;

function item(): CartItem {
  const remaining = Math.max(0, Math.ceil((expiresAt - Date.now()) / 1000));
  return {
    id: 10,
    variant_id: 101,
    product_id: 1,
    product_name: "Camiseta RM",
    product_slug: "camiseta-rm",
    color: "Negro",
    size: "M",
    quantity,
    unit_price: "10000",
    subtotal: String(10000 * quantity),
    reservation_expires_at: new Date(expiresAt).toISOString(),
    time_remaining_seconds: remaining,
    reservation_status: remaining > 0 ? "active" : "expired",
    is_reservation_active: remaining > 0,
    reservation_message: remaining > 0 ? null : "Tu reserva expiró",
  };
}
function cart(): Cart {
  return {
    id: 1,
    items: removed ? [] : [item()],
    total_items: removed ? 0 : quantity,
    total_price: removed ? "0" : String(quantity * 10000),
  };
}
function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}
function calls(path: string, method = "GET") {
  return fetchMock.mock.calls.filter(
    ([url, init]) =>
      new URL(url).pathname === `/api/v1${path}` && (init?.method ?? "GET") === method,
  );
}
async function advance(ms: number) {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(ms);
  });
}
async function click(name: string) {
  await act(async () => {
    fireEvent.click(screen.getByRole("button", { name }));
    await vi.advanceTimersByTimeAsync(20);
  });
}
async function mount(client = new QueryClient({ defaultOptions: { queries: { retry: false } } })) {
  const view = render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <CartCounter />
        <CartPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
  await advance(20);
  return { ...view, client };
}
function time() {
  return screen.getByLabelText("Tiempo restante de reserva");
}

beforeEach(() => {
  vi.useFakeTimers();
  vi.setSystemTime(start);
  expiresAt = start + 900_000;
  quantity = 1;
  removed = false;
  failGet = false;
  reserveResponse = () => {
    expiresAt = Date.now() + 900_000;
    return json(cart());
  };
  fetchMock.mockReset();
  fetchMock.mockImplementation(async (url: string, init?: RequestInit) => {
    const path = new URL(url).pathname;
    if (path === "/api/v1/cart") {
      if (failGet) throw new TypeError("Failed to fetch");
      return json(cart());
    }
    if (path === "/api/v1/cart/items/10/re-reserve" && init?.method === "POST")
      return reserveResponse();
    if (path === "/api/v1/cart/items/10" && init?.method === "PATCH") {
      quantity = JSON.parse(init.body as string).quantity;
      expiresAt = Date.now() + 900_000;
      return json(cart());
    }
    if (path === "/api/v1/cart/items/10" && init?.method === "DELETE") {
      removed = true;
      return json(cart());
    }
    throw new Error(`Solicitud inesperada: ${path}`);
  });
  vi.stubGlobal("fetch", fetchMock);
});
afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe("HU-17 y HU-18: reservas del carrito", () => {
  it("comienza en 15:00 y disminuye cada segundo sin consultar cada segundo", async () => {
    await mount();
    expect(time()).toHaveTextContent("15:00");
    await advance(1000);
    expect(time()).toHaveTextContent("14:59");
    await advance(1000);
    expect(time()).toHaveTextContent("14:58");
    expect(calls("/cart")).toHaveLength(1);
  });

  it("al recargar consulta el tiempo real sin volver a 15:00", async () => {
    const first = await mount();
    await advance(120_000);
    expect(time()).toHaveTextContent("13:00");
    first.unmount();
    await mount();
    expect(time()).toHaveTextContent("13:00");
    expect(calls("/cart")).toHaveLength(2);
    expect(calls("/cart/items/10/re-reserve", "POST")).toHaveLength(0);
  });

  it("no reinicia el tiempo al entrar con datos que ya estaban en caché", async () => {
    const first = await mount();
    const { client } = first;
    first.unmount();
    await advance(60_000);
    client.setDefaultOptions({ queries: { staleTime: Infinity, retry: false } });
    await mount(client);
    expect(time()).toHaveTextContent("14:00");
    expect(calls("/cart")).toHaveLength(1);
  });

  it("refleja la renovación del backend al modificar cantidades", async () => {
    await mount();
    await advance(120_000);
    await click("Aumentar cantidad");
    expect(time()).toHaveTextContent("15:00");
    expect(screen.getByLabelText("Cantidad")).toHaveTextContent("2");
    expect(calls("/cart/items/10", "PATCH")).toHaveLength(1);
  });

  it("vence en 00:00, informa, refresca una sola vez y mantiene el artículo", async () => {
    expiresAt = start + 2000;
    const { client } = await mount();
    client.setQueryData(["catalog", "products"], []);
    await advance(2000);
    expect(time()).toHaveTextContent("00:00");
    expect(screen.getByText("Tu reserva expiró", { exact: true })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Camiseta RM" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Volver a reservar" })).toBeEnabled();
    expect(calls("/cart")).toHaveLength(2);
    expect(client.getQueryState(["catalog", "products"])?.isInvalidated).toBe(true);
    await advance(5000);
    expect(calls("/cart")).toHaveLength(2);
  });

  it("vuelve a reservar con token y usa el nuevo vencimiento del backend", async () => {
    expiresAt = start - 1000;
    await mount();
    await click("Volver a reservar");
    expect(time()).toHaveTextContent("15:00");
    expect(screen.queryByText("Tu reserva expiró")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Volver a reservar" })).not.toBeInTheDocument();
    const posts = calls("/cart/items/10/re-reserve", "POST");
    expect(posts).toHaveLength(1);
    expect(new Headers(posts[0][1].headers).get("Authorization")).toBe("Bearer customer-token");
    await advance(1000);
    expect(time()).toHaveTextContent("14:59");
  });

  it("rechaza out_of_stock sin activar un contador ni confirmar la reserva", async () => {
    expiresAt = start - 1000;
    await mount();
    reserveResponse = () => json({ code: "out_of_stock", message: "Sin stock.", fields: {} }, 400);
    await click("Volver a reservar");
    expect(screen.getByRole("alert")).toHaveTextContent("Ya no hay unidades disponibles");
    expect(time()).toHaveTextContent("00:00");
    expect(screen.getByText("Tu reserva expiró")).toBeInTheDocument();
    expect(screen.getByLabelText("Artículos en el carrito")).toHaveTextContent("Carrito: 1");
  });

  it("permite eliminar un artículo con reserva vencida", async () => {
    expiresAt = start - 1000;
    await mount();
    await click("Eliminar");
    expect(screen.getByText("Tu carrito está vacío")).toBeInTheDocument();
    expect(calls("/cart/items/10", "DELETE")).toHaveLength(1);
  });

  it("conserva el artículo vencido si falla la red y permite intentar nuevamente", async () => {
    expiresAt = start - 1000;
    await mount();
    reserveResponse = () => Promise.reject(new TypeError("Failed to fetch"));
    await click("Volver a reservar");
    expect(screen.getByRole("alert")).toHaveTextContent("No pudimos conectar con el servidor");
    expect(time()).toHaveTextContent("00:00");
    reserveResponse = () => {
      expiresAt = Date.now() + 900_000;
      return json(cart());
    };
    await click("Volver a reservar");
    expect(time()).toHaveTextContent("15:00");
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("evita re-reservas duplicadas y modificaciones mientras la petición está pendiente", async () => {
    expiresAt = start - 1000;
    await mount();
    let resolve!: (response: Response) => void;
    reserveResponse = () =>
      new Promise((done) => {
        resolve = done;
      });
    await click("Volver a reservar");
    expect(screen.getByRole("button", { name: "Volver a reservar" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Eliminar" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Aumentar cantidad" })).toBeDisabled();
    await click("Volver a reservar");
    expect(calls("/cart/items/10/re-reserve", "POST")).toHaveLength(1);
    expiresAt = Date.now() + 900_000;
    resolve(json(cart()));
    await advance(20);
    expect(time()).toHaveTextContent("15:00");
  });

  it("si falla el refresco al vencer, mantiene 00:00 y permite reintentar GET", async () => {
    expiresAt = start + 1000;
    await mount();
    failGet = true;
    await advance(1000);
    await advance(20);
    expect(time()).toHaveTextContent("00:00");
    expect(screen.getByText("Tu reserva expiró")).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("No pudimos conectar con el servidor");
    failGet = false;
    await click("Reintentar");
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(time()).toHaveTextContent("00:00");
  });

  it("usa los segundos del servidor aunque el reloj del cliente tenga otra hora", () => {
    const serverItem = item();
    vi.setSystemTime(start + 3600_000);
    render(
      <ReservationCountdown
        item={serverItem}
        updatedAt={Date.now()}
        busy={false}
        onExpire={vi.fn()}
        onReReserve={vi.fn()}
      />,
    );
    expect(time()).toHaveTextContent("15:00");
  });

  it("usa expires_at si no hay segundos y respeta el estado vencido del backend", async () => {
    const serverItem = { ...item(), time_remaining_seconds: null };
    const view = render(
      <ReservationCountdown
        item={serverItem}
        updatedAt={Date.now()}
        busy={false}
        onExpire={vi.fn()}
        onReReserve={vi.fn()}
      />,
    );
    expect(time()).toHaveTextContent("15:00");
    await advance(1000);
    expect(time()).toHaveTextContent("14:59");
    view.rerender(
      <ReservationCountdown
        item={{ ...serverItem, reservation_status: "expired", is_reservation_active: false }}
        updatedAt={Date.now()}
        busy={false}
        onExpire={vi.fn()}
        onReReserve={vi.fn()}
      />,
    );
    expect(time()).toHaveTextContent("00:00");
  });
});
