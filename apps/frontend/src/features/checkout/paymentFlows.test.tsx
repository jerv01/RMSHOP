import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { MemoryRouter, Route, Routes } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { StoreLayout } from "@/app/layouts/StoreLayout";
import { RequireAuth } from "@/features/auth/RequireAuth";
import { CartPage } from "@/features/cart/CartPage";
import type { Cart } from "@/features/cart/types";
import { OrderResultPage } from "@/features/orders/OrderResultPage";
import { OrdersListPage } from "@/features/orders/OrdersListPage";
import type { OrderDetail, OrderSummary, PaymentResult } from "@/features/orders/types";
import { CheckoutPage } from "./CheckoutPage";
import { PaymentMethodForm, resetMercadoPagoInitForTests } from "./PaymentMethodForm";

const session = vi.hoisted(() => ({
  isLoaded: true,
  isSignedIn: true,
  userId: "customer-a" as string | null,
  getToken: vi.fn(async () => "customer-token"),
}));

const mpMock = vi.hoisted(() => ({
  publicKey: "APP_USR-public-key-test",
  initMercadoPago: vi.fn(),
}));

vi.mock("@clerk/react", () => ({
  useAuth: () => session,
  useClerk: () => ({ signOut: vi.fn() }),
}));

vi.mock("@/shared/lib/env", () => ({
  env: {
    apiUrl: "http://localhost:8000",
    clerkPublishableKey: "pk_test_123",
    get mercadopagoPublicKey() {
      return mpMock.publicKey;
    },
  },
}));

vi.mock("@mercadopago/sdk-react", () => ({
  initMercadoPago: (...args: unknown[]) => mpMock.initMercadoPago(...args),
  CardPayment: ({
    initialization,
    onSubmit,
  }: {
    initialization: { amount: number };
    onSubmit: (formData: Record<string, unknown>, additionalData?: unknown) => Promise<unknown>;
  }) => {
    const [scheme, setScheme] = useState("debvisa");
    return (
      <div data-testid="mp-card-payment-brick">
        <p>Monto Brick: {initialization.amount}</p>
        <label>
          <span>Franquicia de la tarjeta</span>
          <select
            aria-label="Franquicia de la tarjeta"
            value={scheme}
            onChange={(e) => setScheme(e.target.value)}
          >
            <option value="debvisa">Tarjeta débito Visa</option>
            <option value="debmaster">Tarjeta débito Mastercard</option>
            <option value="credit_visa">Tarjeta de crédito Visa</option>
          </select>
        </label>
        <button
          type="button"
          onClick={() =>
            void onSubmit(
              {
                token: "a".repeat(32),
                payment_method_id: scheme === "credit_visa" ? "visa" : scheme,
                installments: 1,
                transaction_amount: initialization.amount,
                payer: {
                  email: "ana@rmshop.co",
                  first_name: "Ana",
                  last_name: "Pérez",
                  identification: { type: "CC", number: "12345678" },
                },
              },
              {
                paymentTypeId: scheme === "credit_visa" ? "credit_card" : "debit_card",
                cardholderName: "Ana Pérez",
              },
            )
          }
        >
          Pagar con tarjeta débito
        </button>
      </div>
    );
  },
}));

const activeCart: Cart = {
  id: 1,
  total_items: 2,
  total_price: "100000",
  items: [
    {
      id: 10,
      variant_id: 101,
      product_id: 1,
      product_name: "Camiseta Texturizada Negra",
      product_slug: "camiseta-texturizada-negra",
      color: "Negro",
      size: "M",
      quantity: 2,
      unit_price: "50000",
      subtotal: "100000",
      reservation_expires_at: "2026-11-18T18:00:00Z",
      is_reservation_active: true,
      time_remaining_seconds: 900,
      reservation_status: "active",
      reservation_message: null,
    },
  ],
};

function buildOrder(overrides: Partial<OrderDetail> = {}): OrderDetail {
  return {
    order_number: "RM-000001",
    status: "pending_payment",
    status_label: "Pendiente de Pago",
    subtotal: "100000",
    shipping_cost: "5000",
    total: "105000",
    municipality: "Cali",
    address_line: "Calle 10 # 20-30",
    recipient_name: "Ana Pérez",
    phone: "3001234567",
    payment_expires_at: "2026-11-18T18:30:00Z",
    created_at: "2026-11-18T18:00:00Z",
    updated_at: "2026-11-18T18:00:00Z",
    items: [
      {
        id: 1,
        variant_id: 101,
        product_name: "Camiseta Texturizada Negra",
        color: "Negro",
        size: "M",
        unit_price: "50000",
        quantity: 2,
        subtotal: "100000",
      },
    ],
    status_history: [
      {
        from_status: "",
        to_status: "pending_payment",
        to_status_label: "Pendiente de Pago",
        note: "Pedido creado al iniciar el pago.",
        created_at: "2026-11-18T18:00:00Z",
      },
    ],
    ...overrides,
  };
}

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const fetchMock = vi.fn();
let cartResponse: () => Response | Promise<Response>;
let checkoutResponse: (body: Record<string, unknown>) => Response | Promise<Response>;
let payResponse: (
  body: Record<string, unknown>,
  init?: RequestInit,
) => Response | Promise<Response>;
let syncResponse: () => Response | Promise<Response>;
let ordersListResponse: () => Response | Promise<Response>;
let pseBanksResponse: () => Response | Promise<Response>;

function callsTo(path: string, method = "GET") {
  return fetchMock.mock.calls.filter(
    ([url, init]) =>
      new URL(url).pathname === `/api/v1${path}` && (init?.method ?? "GET") === method,
  );
}

function mountApp(initialEntry = "/checkout") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[initialEntry]}>
        <Routes>
          <Route element={<StoreLayout />}>
            <Route path="/" element={<h1>Catálogo Público RM</h1>} />
            <Route element={<RequireAuth />}>
              <Route path="/carrito" element={<CartPage />} />
              <Route path="/checkout" element={<CheckoutPage />} />
              <Route path="/pedidos" element={<OrdersListPage />} />
              <Route path="/pedidos/:numero" element={<OrderResultPage />} />
            </Route>
          </Route>
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

async function fillShippingAddress() {
  const addressInput = await screen.findByPlaceholderText("Calle 10 # 20-30 Apto 401");
  await userEvent.type(addressInput, "Calle 10 # 20-30");
  await userEvent.type(screen.getByPlaceholderText("Ana Pérez"), "Ana Pérez");
  await userEvent.type(screen.getByPlaceholderText("3001234567"), "3001234567");
}

beforeEach(() => {
  Object.assign(session, { isLoaded: true, isSignedIn: true, userId: "customer-a" });
  mpMock.publicKey = "APP_USR-public-key-test";
  mpMock.initMercadoPago.mockReset();
  resetMercadoPagoInitForTests();
  localStorage.clear();
  sessionStorage.clear();

  cartResponse = () => json(activeCart);
  checkoutResponse = () => json(buildOrder(), 201);
  pseBanksResponse = () =>
    json([
      { id: "1007", description: "Bancolombia" },
      { id: "1507", description: "Nequi" },
    ]);
  payResponse = () =>
    json(
      {
        order: buildOrder({
          status: "payment_approved",
          status_label: "Pago aprobado",
          status_history: [
            {
              from_status: "",
              to_status: "pending_payment",
              to_status_label: "Pendiente de Pago",
              note: "Pedido creado al iniciar el pago.",
              created_at: "2026-11-18T18:00:00Z",
            },
            {
              from_status: "pending_payment",
              to_status: "payment_approved",
              to_status_label: "Pago aprobado",
              note: "MercadoPago: processed/accredited",
              created_at: "2026-11-18T18:00:03Z",
            },
          ],
        }),
        payment: {
          method: "debit_card",
          status: "approved",
          status_label: "Aprobado",
          status_detail: "accredited",
          amount: "105000",
          redirect_url: "",
        },
      } satisfies PaymentResult,
      201,
    );
  syncResponse = () =>
    json({
      order: buildOrder(),
      payment: null,
    } satisfies PaymentResult);
  ordersListResponse = () =>
    json([
      {
        order_number: "RM-000001",
        status: "pending_payment",
        status_label: "Pendiente de Pago",
        total: "105000",
        created_at: "2026-11-18T18:00:00Z",
      },
    ] satisfies OrderSummary[]);

  fetchMock.mockReset();
  fetchMock.mockImplementation(async (url: string, init?: RequestInit) => {
    const path = new URL(url).pathname;
    const method = init?.method ?? "GET";
    if (path === "/api/v1/cart" && method === "GET") return cartResponse();
    if (path === "/api/v1/checkout" && method === "POST")
      return checkoutResponse(JSON.parse(init?.body as string));
    if (path === "/api/v1/payments/pse-banks" && method === "GET") return pseBanksResponse();
    if (path === "/api/v1/orders/RM-000001/payments" && method === "POST")
      return payResponse(JSON.parse(init?.body as string), init);
    if (path === "/api/v1/orders/RM-000001/payments/sync" && method === "POST")
      return syncResponse();
    if (path === "/api/v1/orders" && method === "GET") return ordersListResponse();
    throw new Error(`Solicitud inesperada: ${method} ${path}`);
  });
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => vi.unstubAllGlobals());

describe("HU-19, HU-20, HU-21, HU-22, HU-23 y HU-24: Flujos de pago y resultado del pedido", () => {
  it("AC-HU-19-1 y HU-22: inicializa el Card Payment Brick con es-CO, paga con token de tarjeta débito enviando X-Idempotency-Key y muestra Pago aprobado sin opción de cancelar", async () => {
    mountApp("/checkout");

    // Verifica que el resumen sume prenda ($ 100.000) + envío Cali ($ 5.000) = $ 105.000
    expect(await screen.findByLabelText("Total a pagar")).toHaveTextContent(/105\.000/);
    expect(mpMock.initMercadoPago).toHaveBeenCalledWith("APP_USR-public-key-test", {
      locale: "es-CO",
    });

    await fillShippingAddress();
    expect(mpMock.initMercadoPago).toHaveBeenCalledTimes(1);
    await userEvent.click(screen.getByRole("button", { name: "Pagar con tarjeta débito" }));

    expect(await screen.findByText("¡Pago aprobado! Tu compra fue exitosa.")).toBeInTheDocument();
    expect(screen.getByText("Estado: Pago aprobado")).toBeInTheDocument();
    expect(screen.getByText(/no pueden cancelarse desde la tienda web/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /cancelar/i })).not.toBeInTheDocument();

    // Verifica que solo viaja el token del Brick, el X-Idempotency-Key y ningún dato sensible
    const paymentCall = callsTo("/orders/RM-000001/payments", "POST")[0];
    expect(paymentCall).toBeDefined();
    const sentPayload = JSON.parse(paymentCall[1].body as string);
    const sentHeaders = new Headers(paymentCall[1].headers);
    expect(sentHeaders.get("X-Idempotency-Key")).toBeTruthy();
    expect(sentPayload).toEqual({
      method: "debit_card",
      token: "a".repeat(32),
      payment_method_id: "debvisa",
      payment_type: "debit_card",
      first_name: "Ana",
      last_name: "Pérez",
      identification_type: "CC",
      identification_number: "12345678",
    });
    expect(localStorage.length).toBe(0);
    expect(sessionStorage.length).toBe(0);
  });

  it("AC-HU-19-2: rechaza tarjetas de crédito informando que solo se acepta débito y conserva el pedido Pendiente de Pago sin recrearlo", async () => {
    payResponse = (body) => {
      if (body.payment_type === "credit_card") {
        return json(
          {
            code: "only_debit_allowed",
            message:
              "Solo se aceptan tarjetas débito. Intenta con una tarjeta débito Visa o Mastercard.",
            fields: {
              payment_method_id: [
                "Solo se aceptan tarjetas débito. Intenta con una tarjeta débito Visa o Mastercard.",
              ],
            },
          },
          400,
        );
      }
      return json(
        {
          order: buildOrder({ status: "payment_approved", status_label: "Pago aprobado" }),
          payment: { method: "debit_card", status: "approved", status_label: "Aprobado" },
        } satisfies PaymentResult,
        201,
      );
    };

    mountApp("/checkout");

    await fillShippingAddress();
    await userEvent.selectOptions(screen.getByLabelText("Franquicia de la tarjeta"), "credit_visa");
    await userEvent.click(screen.getByRole("button", { name: "Pagar con tarjeta débito" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Solo se aceptan tarjetas débito. Intenta con una tarjeta débito Visa o Mastercard.",
    );
    // El pedido RM-000001 ya fue creado y se muestra en estado "Pendiente de Pago" (HU-21)
    expect(screen.getByLabelText("Estado actual del pedido")).toHaveTextContent(
      "Pendiente de Pago",
    );
    expect(callsTo("/checkout", "POST")).toHaveLength(1);

    // El cliente corrige a tarjeta débito Mastercard y paga el mismo pedido sin llamar de nuevo a /checkout
    await userEvent.selectOptions(screen.getByLabelText("Franquicia de la tarjeta"), "debmaster");
    await userEvent.click(screen.getByRole("button", { name: "Pagar con tarjeta débito" }));

    expect(await screen.findByText("¡Pago aprobado! Tu compra fue exitosa.")).toBeInTheDocument();
    expect(callsTo("/checkout", "POST")).toHaveLength(1);
    expect(callsTo("/orders/RM-000001/payments", "POST")).toHaveLength(2);
  });

  it("muestra aviso de configuración cuando falta VITE_MERCADOPAGO_PUBLIC_KEY sin montar el Brick ni enviar tokens falsos", () => {
    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const onSubmit = vi.fn();
    render(
      <QueryClientProvider client={client}>
        <PaymentMethodForm
          totalAmount={105000}
          mercadopagoPublicKey=""
          busy={false}
          onSubmit={onSubmit}
        />
      </QueryClientProvider>,
    );

    expect(screen.getByRole("alert")).toHaveTextContent(/VITE_MERCADOPAGO_PUBLIC_KEY/i);
    expect(screen.queryByTestId("mp-card-payment-brick")).not.toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("AC-HU-20-1: inicia pago con PSE seleccionando banco, muestra enlace de redirección en Pendiente de Pago y aprueba al sincronizar", async () => {
    payResponse = () =>
      json(
        {
          order: buildOrder({
            status: "pending_payment",
            status_label: "Pendiente de Pago",
          }),
          payment: {
            method: "pse",
            status: "action_required",
            status_label: "Esperando acción del cliente",
            status_detail: "waiting_transfer",
            redirect_url: "https://banco.test/pse/autorizar-123",
          },
        } satisfies PaymentResult,
        201,
      );

    syncResponse = () =>
      json({
        order: buildOrder({
          status: "payment_approved",
          status_label: "Pago aprobado",
          status_history: [
            {
              to_status: "pending_payment",
              to_status_label: "Pendiente de Pago",
              note: "Pedido creado al iniciar el pago.",
              created_at: "2026-11-18T18:00:00Z",
            },
            {
              to_status: "payment_approved",
              to_status_label: "Pago aprobado",
              note: "MercadoPago: processed/accredited",
              created_at: "2026-11-18T18:02:00Z",
            },
          ],
        }),
        payment: {
          method: "pse",
          status: "approved",
          status_label: "Aprobado",
          status_detail: "accredited",
          redirect_url: "https://banco.test/pse/autorizar-123",
        },
      } satisfies PaymentResult);

    mountApp("/checkout");

    await fillShippingAddress();
    await userEvent.click(screen.getByRole("radio", { name: /PSE \(Banca en línea \/ Nequi\)/i }));

    const bankSelect = await screen.findByLabelText("Banco o billetera digital (PSE)");
    await waitFor(() =>
      expect(within(bankSelect).getByRole("option", { name: "Nequi" })).toBeInTheDocument(),
    );
    await userEvent.selectOptions(bankSelect, "1507");
    await userEvent.type(screen.getByPlaceholderText("12345678"), "12345678");

    await userEvent.click(screen.getByRole("button", { name: "Continuar al banco por PSE" }));

    // En la página del pedido se ve Pendiente de Pago y el enlace al banco sin permitir otro cobro
    expect(await screen.findByText("Estado: Pendiente de Pago")).toBeInTheDocument();
    const bankLink = screen.getByRole("link", { name: "Ir al portal del banco" });
    expect(bankLink).toHaveAttribute("href", "https://banco.test/pse/autorizar-123");
    expect(
      screen.queryByRole("button", { name: "Continuar al banco por PSE" }),
    ).not.toBeInTheDocument();

    // Al regresar del banco y pulsar "Actualizar estado", sincroniza y pasa a "Pago aprobado"
    await userEvent.click(screen.getByRole("button", { name: "Actualizar estado" }));
    expect(await screen.findByText("¡Pago aprobado! Tu compra fue exitosa.")).toBeInTheDocument();
    expect(screen.getByText("Estado: Pago aprobado")).toBeInTheDocument();
  });

  it("AC-HU-21-2 y AC-HU-21-3: maneja caída de la pasarela (503) manteniendo el pedido consistente y permite reintentar con nueva clave de idempotencia sin doble cobro", async () => {
    let attempts = 0;
    payResponse = () => {
      attempts += 1;
      if (attempts === 1) {
        return json(
          {
            code: "payment_gateway_unavailable",
            message:
              "No pudimos comunicarnos con el servicio de pagos. Tu pedido sigue pendiente de pago; intenta de nuevo en unos minutos.",
            fields: {},
          },
          503,
        );
      }
      return json(
        {
          order: buildOrder({ status: "payment_approved", status_label: "Pago aprobado" }),
          payment: { method: "debit_card", status: "approved", status_label: "Aprobado" },
        } satisfies PaymentResult,
        201,
      );
    };

    mountApp("/checkout");

    await fillShippingAddress();
    expect(mpMock.initMercadoPago).toHaveBeenCalledTimes(1);
    await userEvent.click(screen.getByRole("button", { name: "Pagar con tarjeta débito" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /No pudimos comunicarnos con el servicio de pagos\. Tu pedido sigue Pendiente de Pago/i,
    );
    expect(screen.getByLabelText("Estado actual del pedido")).toHaveTextContent(
      "Pendiente de Pago",
    );

    // Reintentar cuando la pasarela vuelve a responder
    await userEvent.click(screen.getByRole("button", { name: "Pagar con tarjeta débito" }));

    expect(await screen.findByText("¡Pago aprobado! Tu compra fue exitosa.")).toBeInTheDocument();

    const paymentCalls = callsTo("/orders/RM-000001/payments", "POST");
    expect(paymentCalls).toHaveLength(2);
    const key1 = new Headers(paymentCalls[0][1].headers).get("X-Idempotency-Key");
    const key2 = new Headers(paymentCalls[1][1].headers).get("X-Idempotency-Key");
    expect(key1).toBeTruthy();
    expect(key2).toBeTruthy();
    expect(key1).not.toBe(key2);
    expect(callsTo("/checkout", "POST")).toHaveLength(1);
  });

  it("AC-HU-20-2 y HU-23: ante pago rechazado muestra el pedido Cancelado, oculta códigos técnicos de la pasarela, lista ambos estados en el historial y permite iniciar un nuevo pedido", async () => {
    syncResponse = () =>
      json({
        order: buildOrder({
          status: "cancelled",
          status_label: "Cancelado",
          status_history: [
            {
              to_status: "pending_payment",
              to_status_label: "Pendiente de Pago",
              note: "Pedido creado al iniciar el pago.",
              created_at: "2026-11-18T18:00:00Z",
            },
            {
              to_status: "payment_rejected",
              to_status_label: "Pago rechazado",
              note: "MercadoPago: failed/cc_rejected_insufficient_amount",
              created_at: "2026-11-18T18:01:00Z",
            },
            {
              to_status: "cancelled",
              to_status_label: "Cancelado",
              note: "Cancelado por pago rechazado.",
              created_at: "2026-11-18T18:01:01Z",
            },
          ],
        }),
        payment: {
          method: "debit_card",
          status: "rejected",
          status_label: "Rechazado",
          status_detail: "cc_rejected_insufficient_amount",
        },
      } satisfies PaymentResult);

    mountApp("/pedidos/RM-000001");

    expect(await screen.findByText("Estado: Cancelado")).toBeInTheDocument();
    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent(
      /Tu pago fue rechazado y el pedido se canceló automáticamente/i,
    );
    // Verifica que NO se exponga el código técnico en inglés de MercadoPago (HU-23 / HU-60)
    expect(screen.queryByText(/cc_rejected_insufficient_amount/i)).not.toBeInTheDocument();

    const history = screen.getByRole("list", { name: "Historial del pedido" });
    expect(within(history).getByText("Pendiente de Pago")).toBeInTheDocument();
    expect(within(history).getByText("Pago rechazado")).toBeInTheDocument();
    expect(within(history).getByText("Cancelado")).toBeInTheDocument();

    // AC-HU-23-3: Permite iniciar un nuevo pedido volviendo al catálogo
    await userEvent.click(screen.getByRole("link", { name: "Iniciar un nuevo pedido" }));
    expect(await screen.findByRole("heading", { name: "Catálogo Público RM" })).toBeInTheDocument();
  });

  it("HU-24: refleja la cancelación automática tras 30 minutos sin respuesta en el detalle y en el listado de Mis pedidos", async () => {
    syncResponse = () =>
      json({
        order: buildOrder({
          status: "cancelled",
          status_label: "Cancelado",
          status_history: [
            {
              to_status: "pending_payment",
              to_status_label: "Pendiente de Pago",
              note: "Pedido creado al iniciar el pago.",
              created_at: "2026-11-18T18:00:00Z",
            },
            {
              to_status: "cancelled",
              to_status_label: "Cancelado",
              note: "Cancelado: sin respuesta del pago en 30 minutos.",
              created_at: "2026-11-18T18:30:05Z",
            },
          ],
        }),
        payment: null,
      } satisfies PaymentResult);

    ordersListResponse = () =>
      json([
        {
          order_number: "RM-000001",
          status: "cancelled",
          status_label: "Cancelado",
          total: "105000",
          created_at: "2026-11-18T18:00:00Z",
        },
      ] satisfies OrderSummary[]);

    mountApp("/pedidos/RM-000001");

    expect(await screen.findByText("Estado: Cancelado")).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent(
      /El plazo de 30 minutos para recibir respuesta del pago venció y el pedido se canceló automáticamente/i,
    );

    const history = screen.getByRole("list", { name: "Historial del pedido" });
    expect(
      within(history).getByText(/Cancelado: sin respuesta del pago en 30 minutos/i),
    ).toBeInTheDocument();

    // Navega a "Mis pedidos" y comprueba que el estado en texto figura como "Cancelado"
    await userEvent.click(screen.getByRole("link", { name: "Mis pedidos" }));
    const ordersList = await screen.findByRole("list", { name: "Lista de mis pedidos" });
    expect(within(ordersList).getByText("RM-000001")).toBeInTheDocument();
    expect(within(ordersList).getByText("Cancelado")).toBeInTheDocument();
  });
});
