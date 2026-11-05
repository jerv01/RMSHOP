import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { StoreLayout } from "@/app/layouts/StoreLayout";
import { CatalogSection } from "./CatalogSection";
import { ProductDetailPage } from "./ProductDetailPage";
import type { CatalogProduct } from "./types";

vi.mock("@clerk/react", () => ({
  useAuth: () => ({ isLoaded: true, isSignedIn: false }),
  useClerk: () => ({ signOut: vi.fn() }),
}));

const sampleProducts: CatalogProduct[] = [
  {
    id: 1,
    name: "Camiseta Oversize Lobo",
    slug: "camiseta-oversize-lobo",
    description: "Camiseta pesada de algodón peinado con estampado frontal.",
    price: "75000",
    previous_price: "90000",
    material: "Algodón 100% 260g",
    design: "Estampado Lobo RM · Corte Oversize",
    category: { id: 1, name: "Camisetas / Tops", slug: "camisetas-tops" },
    status: "published",
    is_new: true,
    in_stock: true,
    images: [
      {
        id: 10,
        product_id: 1,
        image_url: "/media/products/camiseta-1.webp",
        alt_text: "Frente de Camiseta Oversize Lobo",
        position: 1,
        created_at: "2026-11-04T12:00:00Z",
      },
      {
        id: 11,
        product_id: 1,
        image_url: "/media/products/camiseta-2.webp",
        alt_text: "Espalda de Camiseta Oversize Lobo",
        position: 2,
        created_at: "2026-11-04T12:00:00Z",
      },
    ],
    variants: [
      {
        id: 101,
        product_id: 1,
        color: "Negro",
        size: "M",
        stock_quantity: 5,
        created_at: "2026-11-04T12:00:00Z",
        updated_at: "2026-11-04T12:00:00Z",
      },
      {
        id: 102,
        product_id: 1,
        color: "Blanco",
        size: "L",
        stock_quantity: 0,
        created_at: "2026-11-04T12:00:00Z",
        updated_at: "2026-11-04T12:00:00Z",
      },
    ],
    created_at: "2026-11-04T12:00:00Z",
    updated_at: "2026-11-04T12:00:00Z",
  },
  {
    id: 2,
    name: "Buzo Hoodie RM",
    slug: "buzo-hoodie-rm",
    description: "Buzo con capota en algodón perchado para clima fresco.",
    price: "135000",
    previous_price: null,
    material: "Algodón perchado 320g",
    category: { id: 2, name: "Buzos / Sacos", slug: "buzos-sacos" },
    status: "published",
    in_stock: false,
    images: [
      {
        id: 20,
        product_id: 2,
        image_url: "/media/products/buzo-1.webp",
        alt_text: "Buzo Hoodie RM gris",
        position: 1,
        created_at: "2026-11-04T12:00:00Z",
      },
    ],
    variants: [
      {
        id: 201,
        product_id: 2,
        color: "Gris",
        size: "U",
        stock_quantity: 0,
        created_at: "2026-11-04T12:00:00Z",
        updated_at: "2026-11-04T12:00:00Z",
      },
    ],
    created_at: "2026-11-04T12:00:00Z",
    updated_at: "2026-11-04T12:00:00Z",
  },
];

let productsResponse: () => Response;
let detailResponse: (slug: string) => Response;
const fetchMock = vi.fn();

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function renderStore(initialEntry = "/") {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[initialEntry]}>
        <Routes>
          <Route element={<StoreLayout />}>
            <Route path="/" element={<CatalogSection />} />
            <Route path="/categoria/:slug" element={<CatalogSection />} />
            <Route path="/producto/:slug" element={<ProductDetailPage />} />
          </Route>
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  productsResponse = () => json(sampleProducts);
  detailResponse = (slug: string) => {
    const found = sampleProducts.find((p) => p.slug === slug);
    if (!found) {
      return json({ code: "not_found", message: "No encontrado", fields: {} }, 404);
    }
    return json(found);
  };

  fetchMock.mockReset();
  fetchMock.mockImplementation(async (url: string) => {
    const parsed = new URL(url, "http://localhost:8000");
    if (parsed.pathname === "/api/v1/products") {
      return productsResponse();
    }
    if (parsed.pathname.startsWith("/api/v1/products/")) {
      const slug = decodeURIComponent(parsed.pathname.replace("/api/v1/products/", ""));
      return detailResponse(slug);
    }
    return json({ status: "ok", database: "ok" });
  });
  vi.stubGlobal("fetch", fetchMock);
});

describe("HU-1: Exploración del catálogo público sin registro", () => {
  it("AC-HU-1-1: muestra los productos publicados con nombre, foto, categoría y precios en COP a un visitante sin sesión", async () => {
    renderStore("/");

    const list = await screen.findByRole("region", { name: "Listado de productos" });
    expect(within(list).getByText("Camiseta Oversize Lobo")).toBeInTheDocument();
    expect(within(list).getByText("Buzo Hoodie RM")).toBeInTheDocument();
    expect(
      within(list).getByRole("img", { name: "Frente de Camiseta Oversize Lobo" }),
    ).toBeInTheDocument();
    // Precios en COP (vigente y anterior tachado)
    expect(within(list).getByText(/\$\s?75\.000/)).toBeInTheDocument();
    expect(within(list).getByText(/\$\s?90\.000/)).toBeInTheDocument();
    expect(within(list).getByText(/\$\s?135\.000/)).toBeInTheDocument();
    // Badges de estado
    expect(within(list).getByText("Nuevo")).toBeInTheDocument();
    expect(within(list).getByText("Agotado")).toBeInTheDocument();
  });

  it("AC-HU-1-2: muestra 'No hay productos disponibles por el momento' cuando no hay prendas publicadas", async () => {
    productsResponse = () => json([]);
    renderStore("/");

    expect(
      await screen.findByText("No hay productos disponibles por el momento"),
    ).toBeInTheDocument();
  });

  it("AC-HU-1-3: muestra hasta 30 productos publicados sin duplicados ni omisiones", async () => {
    const thirtyProducts: CatalogProduct[] = Array.from({ length: 30 }, (_, index) => ({
      ...sampleProducts[0],
      id: index + 1,
      name: `Prenda RM #${index + 1}`,
      slug: `prenda-rm-${index + 1}`,
    }));
    productsResponse = () => json(thirtyProducts);
    renderStore("/");

    const list = await screen.findByRole("region", { name: "Listado de productos" });
    const items = within(list).getAllByRole("listitem");
    expect(items).toHaveLength(30);
    expect(within(list).getByText("Prenda RM #1")).toBeInTheDocument();
    expect(within(list).getByText("Prenda RM #30")).toBeInTheDocument();
  });
});

describe("HU-2: Filtrado y navegación por categoría", () => {
  it("AC-HU-2-1 y AC-HU-2-3: filtra por 'Buzos / Sacos' y restaura el catálogo al elegir 'Todos'", async () => {
    renderStore("/");
    await screen.findByText("Camiseta Oversize Lobo");

    const filterGroup = screen.getByRole("group", { name: "Categorías de prendas" });
    const buzosBtn = within(filterGroup).getByRole("button", { name: "Buzos / Sacos" });

    // Operable con teclado y clic
    buzosBtn.focus();
    await userEvent.keyboard("{Enter}");

    expect(buzosBtn).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("Buzo Hoodie RM")).toBeInTheDocument();
    expect(screen.queryByText("Camiseta Oversize Lobo")).not.toBeInTheDocument();

    const todosBtn = within(filterGroup).getByRole("button", { name: "Todos" });
    await userEvent.click(todosBtn);

    expect(todosBtn).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText("Camiseta Oversize Lobo")).toBeInTheDocument();
    expect(screen.getByText("Buzo Hoodie RM")).toBeInTheDocument();
  });

  it("AC-HU-2-2: muestra 'No hay productos en esta categoría' cuando la categoría elegida no tiene prendas", async () => {
    renderStore("/");
    await screen.findByText("Camiseta Oversize Lobo");

    const filterGroup = screen.getByRole("group", { name: "Categorías de prendas" });
    await userEvent.click(within(filterGroup).getByRole("button", { name: "Conjuntos" }));

    expect(await screen.findByText("No hay productos en esta categoría")).toBeInTheDocument();
  });
});

describe("HU-3: Ficha de detalle de prenda", () => {
  it("AC-HU-3-1: navega desde el catálogo a la ficha y muestra nombre, descripción, precio, material, fotografías y diseño", async () => {
    renderStore("/");
    const cardLink = await screen.findByRole("link", {
      name: "Ver detalle de Camiseta Oversize Lobo",
    });
    await userEvent.click(cardLink);

    expect(
      await screen.findByRole("heading", { name: "Camiseta Oversize Lobo" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Camiseta pesada de algodón peinado con estampado frontal."),
    ).toBeInTheDocument();
    expect(screen.getByText("Algodón 100% 260g")).toBeInTheDocument();
    expect(screen.getByText("Estampado Lobo RM · Corte Oversize")).toBeInTheDocument();
    expect(screen.getByText(/\$\s?75\.000/)).toBeInTheDocument();
    expect(screen.getByText(/\$\s?90\.000/)).toBeInTheDocument();

    const gallery = screen.getByRole("region", { name: "Fotografías del producto" });
    expect(within(gallery).getAllByRole("img")).toHaveLength(2);
    expect(
      within(gallery).getByRole("img", { name: "Frente de Camiseta Oversize Lobo" }),
    ).toBeInTheDocument();
    expect(
      within(gallery).getByRole("img", { name: "Espalda de Camiseta Oversize Lobo" }),
    ).toBeInTheDocument();
  });

  it("AC-HU-3-2: muestra 'Producto no disponible' y enlace al catálogo cuando el producto no existe o fue despublicado", async () => {
    renderStore("/producto/prenda-inexistente");

    expect(
      await screen.findByRole("heading", { name: "Producto no disponible" }),
    ).toBeInTheDocument();
    const backLink = screen.getByRole("link", { name: "Volver al catálogo" });
    expect(backLink).toHaveAttribute("href", "/");
  });

  it("AC-HU-3-3: muestra una sola fotografía sin espacios vacíos cuando la prenda tiene 1 foto", async () => {
    renderStore("/producto/buzo-hoodie-rm");

    await screen.findByRole("heading", { name: "Buzo Hoodie RM" });
    const gallery = screen.getByRole("region", { name: "Fotografías del producto" });
    const photos = within(gallery).getAllByRole("img");
    expect(photos).toHaveLength(1);
    expect(photos[0]).toHaveAttribute("alt", "Buzo Hoodie RM gris");
  });
});

describe("HU-59 y HU-60: Diseño adaptable e idioma español", () => {
  it("AC-HU-59-1 y AC-HU-60-1: incluye barra de anuncio en español, contenedor sin desborde horizontal y chips táctiles de 44px (min-h-11)", async () => {
    const { container } = renderStore("/");
    await screen.findByText("Camiseta Oversize Lobo");

    expect(container.firstElementChild).toHaveClass("overflow-x-hidden");
    expect(screen.getByRole("region", { name: "Anuncio de envíos" })).toHaveTextContent(
      /Cali \$ 5\.000/,
    );

    const filterGroup = screen.getByRole("group", { name: "Categorías de prendas" });
    for (const button of within(filterGroup).getAllByRole("button")) {
      expect(button).toHaveClass("min-h-11");
    }
  });
});
