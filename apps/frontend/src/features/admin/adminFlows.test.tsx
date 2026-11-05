import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ReactNode } from "react";
import { ApiError } from "@/shared/api/client";
import { ProductCreatePage } from "./products/ProductCreatePage";
import { ProductEditPage } from "./products/ProductEditPage";
import { ProductSessionProvider } from "./products/ProductSession";
import { ProductImages, imageUrl, validatePhoto } from "./products/ProductImages";
import { ProductVariants } from "./products/ProductVariants";
import { InventoryPage, positiveQuantity } from "./inventory/InventoryPage";
import type { Product, ProductImage, StockMovement, Variant } from "./products/types";

const { api } = vi.hoisted(() => ({ api: vi.fn() }));
vi.mock("@/shared/api/useApi", () => ({ useApi: () => api }));
vi.mock("@clerk/react", () => ({ useAuth: () => ({ userId: "admin-1" }) }));
const product: Product = {
  id: 9,
  name: "Camiseta RM",
  slug: "camiseta-rm",
  description: "Camiseta de algodón",
  material: "Algodón",
  price: "75000",
  previous_price: "90000",
  category: { id: 1, name: "Camisetas / Tops", slug: "camisetas-tops" },
  status: "draft",
  created_at: "2026-11-04T12:00:00Z",
  updated_at: "2026-11-04T12:00:00Z",
};
const variant: Variant = {
  id: 5,
  product_id: 9,
  color: "Negro",
  size: "M",
  stock_quantity: 0,
  created_at: product.created_at,
  updated_at: product.updated_at,
};
const photo: ProductImage = {
  id: 2,
  product_id: 9,
  image_url: "/media/black.webp",
  alt_text: "Camiseta negra",
  position: 1,
  created_at: product.created_at,
};

function setup(children: ReactNode, route = "/") {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[route]}>
        <ProductSessionProvider>{children}</ProductSessionProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}
function fillProduct() {
  fireEvent.change(screen.getByLabelText("Nombre"), { target: { value: product.name } });
  fireEvent.change(screen.getByLabelText("Descripción"), {
    target: { value: product.description },
  });
  fireEvent.change(screen.getByLabelText("Precio (COP)"), { target: { value: product.price } });
  fireEvent.change(screen.getByLabelText("Material"), { target: { value: product.material } });
}
beforeEach(() => {
  api.mockReset();
});
afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("HU-33 y HU-34", () => {
  it("conserva las categorías sin mostrar el aviso eliminado", () => {
    setup(<ProductCreatePage />);
    expect(screen.queryByText(/Si el ID no coincide con tu base/)).not.toBeInTheDocument();
    expect(screen.getByLabelText(/^Categoría \(ID\)/)).toHaveValue("1");
    expect(screen.getByText("Camisetas / Tops", { selector: "option" })).toHaveValue("1");
    expect(screen.getAllByRole("option", { hidden: true })).toHaveLength(4);
  });
  it("crea un borrador con datos reales del formulario y navega al ID devuelto", async () => {
    api.mockResolvedValue({ ...product, previous_price: null });
    setup(
      <Routes>
        <Route path="/" element={<ProductCreatePage />} />
        <Route path="/admin/productos/:id" element={<p>Detalle guardado</p>} />
      </Routes>,
    );
    fillProduct();
    fireEvent.click(screen.getByRole("button", { name: "Crear borrador" }));
    await screen.findByText("Detalle guardado");
    expect(api).toHaveBeenCalledWith("/admin/products", {
      method: "POST",
      json: {
        name: product.name,
        description: product.description,
        price: "75000",
        material: "Algodón",
        category_id: 1,
      },
    });
  });
  it("rechaza precios inválidos sin enviar una creación", async () => {
    setup(<ProductCreatePage />);
    fillProduct();
    fireEvent.change(screen.getByLabelText("Precio (COP)"), { target: { value: "-10" } });
    fireEvent.click(screen.getByRole("button", { name: "Crear borrador" }));
    await screen.findByText(/Ingresa un precio positivo/);
    expect(api).not.toHaveBeenCalled();
  });
  it("edita por ID, impide quitar el precio anterior y confirma el archivado", async () => {
    api.mockImplementation((path: string, options?: { method: string }) => {
      if (options?.method === "PATCH")
        return Promise.resolve({
          ...product,
          name: "Nuevo nombre",
          updated_at: "2026-11-04T13:00:00Z",
        });
      if (options?.method === "DELETE") return Promise.resolve(undefined);
      return Promise.resolve(path === "/admin/products/9" ? product : []);
    });
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
    setup(
      <Routes>
        <Route path="/admin/productos/:id" element={<ProductEditPage />} />
        <Route path="/admin/productos" element={<p>Listado de sesión</p>} />
      </Routes>,
      "/admin/productos/9",
    );
    await screen.findByDisplayValue("Camiseta RM");
    fireEvent.change(screen.getByLabelText(/Precio anterior/), { target: { value: "" } });
    fireEvent.click(screen.getByRole("button", { name: "Guardar cambios" }));
    await screen.findByText(/El precio anterior no puede quitarse/);
    expect(api.mock.calls.some(([, options]) => options?.method === "PATCH")).toBe(false);
    fireEvent.change(screen.getByLabelText(/Precio anterior/), { target: { value: "95000" } });
    fireEvent.change(screen.getByLabelText("Nombre"), { target: { value: "Nuevo nombre" } });
    fireEvent.click(screen.getByRole("button", { name: "Guardar cambios" }));
    await screen.findByText("Cambios guardados.");
    expect(api).toHaveBeenCalledWith(
      "/admin/products/9",
      expect.objectContaining({
        method: "PATCH",
        json: expect.objectContaining({ name: "Nuevo nombre", previous_price: "95000" }),
      }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Archivar producto" }));
    expect(api.mock.calls.some(([, options]) => options?.method === "DELETE")).toBe(false);
    confirm.mockReturnValue(true);
    fireEvent.click(screen.getByRole("button", { name: "Archivar producto" }));
    await screen.findByText("Listado de sesión");
    expect(api).toHaveBeenCalledWith("/admin/products/9", { method: "DELETE" });
  });
  it("no permite publicar sin fotos", async () => {
    api.mockImplementation((path: string) =>
      Promise.resolve(path === "/admin/products/9" ? product : []),
    );
    setup(
      <Routes>
        <Route path="/admin/productos/:id" element={<ProductEditPage />} />
      </Routes>,
      "/admin/productos/9",
    );
    await screen.findByDisplayValue("Camiseta RM");
    fireEvent.change(screen.getByLabelText("Estado"), { target: { value: "published" } });
    fireEvent.click(screen.getByRole("button", { name: "Guardar cambios" }));
    await screen.findByText(/Carga al menos una fotografía/);
    expect(api.mock.calls.some(([, options]) => options?.method === "PATCH")).toBe(false);
  });
});

describe("HU-35", () => {
  it("resuelve URLs relativas y valida tamaño y formato", () => {
    expect(imageUrl("/media/photo.webp")).toBe("http://localhost:8000/media/photo.webp");
    expect(imageUrl("https://cdn.example.com/photo.webp")).toBe(
      "https://cdn.example.com/photo.webp",
    );
    expect(validatePhoto(new File(["x"], "a.txt", { type: "text/plain" }))).toMatch(/JPG/);
    expect(
      validatePhoto(
        new File([new Uint8Array(5 * 1024 * 1024 + 1)], "a.jpg", { type: "image/jpeg" }),
      ),
    ).toMatch(/5 MB/);
  });
  it("sube multipart con texto alternativo y muestra la foto guardada", async () => {
    let uploaded = false;
    api.mockImplementation((_: string, options?: { method: string }) => {
      if (options?.method === "POST") {
        uploaded = true;
        return Promise.resolve(photo);
      }
      return Promise.resolve(uploaded ? [photo] : []);
    });
    vi.stubGlobal(
      "URL",
      class extends URL {
        static createObjectURL() {
          return "blob:preview";
        }
        static revokeObjectURL = vi.fn();
      },
    );
    setup(<ProductImages productId={9} published={false} />);
    await screen.findByText("Este producto todavía no tiene fotografías.");
    const file = new File(["image"], "black.jpg", { type: "image/jpeg" });
    fireEvent.change(screen.getByLabelText("Nueva fotografía"), { target: { files: [file] } });
    fireEvent.change(screen.getByLabelText(/Texto alternativo/), {
      target: { value: "Camiseta negra" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Subir fotografía" }));
    await screen.findByAltText("Camiseta negra");
    const options = api.mock.calls.find(([, options]) => options?.method === "POST")?.[1];
    expect(options.formData.get("image")).toBe(file);
    expect(options.formData.get("alt_text")).toBe("Camiseta negra");
  });
  it("reordena usando todos los IDs y respeta la cancelación al eliminar", async () => {
    api.mockResolvedValue([photo, { ...photo, id: 3, position: 2, alt_text: "Dorso" }]);
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
    setup(<ProductImages productId={9} published={false} />);
    fireEvent.click(await screen.findByRole("button", { name: "Mover foto 1 después" }));
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith("/admin/products/9/images/reorder", {
        method: "PATCH",
        json: { image_ids: [3, 2] },
      }),
    );
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Eliminar foto 1" })).toBeEnabled(),
    );
    fireEvent.click(screen.getByRole("button", { name: "Eliminar foto 1" }));
    expect(confirm).toHaveBeenCalled();
    expect(api.mock.calls.some(([, options]) => options?.method === "DELETE")).toBe(false);
  });
});

describe("HU-36", () => {
  it("vuelve a comprobar el historial antes de eliminar una variante", async () => {
    let historyReads = 0;
    api.mockImplementation((path: string) => {
      if (path.endsWith("stock-movements"))
        return Promise.resolve(++historyReads === 1 ? [] : [{ id: 10 }]);
      return Promise.resolve([variant]);
    });
    vi.spyOn(window, "confirm").mockReturnValue(true);
    setup(<ProductVariants productId={9} />);
    fireEvent.click(await screen.findByRole("button", { name: "Eliminar Negro / M" }));
    await screen.findByText("Esta variante tiene historial y debe conservarse.");
    expect(api.mock.calls.some(([, options]) => options?.method === "DELETE")).toBe(false);
  });
  it("conserva variantes con historial y crea combinaciones con stock cero", async () => {
    api.mockImplementation((path: string) =>
      Promise.resolve(path.endsWith("stock-movements") ? [{ id: 1 }] : [variant]),
    );
    setup(<ProductVariants productId={9} />);
    await screen.findByText("Conservada por historial");
    expect(screen.queryByRole("button", { name: /Eliminar Negro/ })).not.toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Color"), { target: { value: "Blanco" } });
    fireEvent.change(screen.getByLabelText("Talla"), { target: { value: "L" } });
    fireEvent.click(screen.getByRole("button", { name: "Agregar variante" }));
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith("/admin/products/9/variants", {
        method: "POST",
        json: { color: "Blanco", size: "L", stock_quantity: 0 },
      }),
    );
  });
  it("evita duplicados normalizados y genera colores por tallas", async () => {
    api.mockImplementation((path: string) =>
      Promise.resolve(path.endsWith("stock-movements") ? [] : [variant]),
    );
    setup(<ProductVariants productId={9} />);
    await screen.findByText("Negro / M");
    fireEvent.change(screen.getByLabelText("Color"), { target: { value: " negro " } });
    fireEvent.change(screen.getByLabelText("Talla"), { target: { value: "m" } });
    fireEvent.click(screen.getByRole("button", { name: "Agregar variante" }));
    await screen.findByText(/sin repetir una combinación/);
    expect(api.mock.calls.some(([, options]) => options?.method === "POST")).toBe(false);
    fireEvent.change(screen.getByLabelText("Colores separados por comas"), {
      target: { value: "Negro, Blanco, negro" },
    });
    fireEvent.change(screen.getByLabelText("Tallas separadas por comas"), {
      target: { value: "S, M" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Generar variantes" }));
    await waitFor(() =>
      expect(api).toHaveBeenCalledWith("/admin/products/9/variants/bulk", {
        method: "POST",
        json: { colors: ["Negro", "Blanco"], sizes: ["S", "M"] },
      }),
    );
  });
});

describe("HU-37", () => {
  function mockStockApi() {
    let stock = 10;
    const movements: StockMovement[] = [
      {
        id: 1,
        variant_id: 5,
        delta: 10,
        resulting_stock: 10,
        reason: "Ingreso inicial",
        admin: null,
        created_at: product.created_at,
      },
    ];
    api.mockImplementation(
      (path: string, options?: { method: string; json: { delta: number; reason: string } }) => {
        if (options?.method === "POST") {
          stock += options.json.delta;
          const movement = {
            id: movements.length + 1,
            variant_id: 5,
            delta: options.json.delta,
            resulting_stock: stock,
            reason: options.json.reason,
            admin: null,
            created_at: product.created_at,
          };
          movements.unshift(movement);
          return Promise.resolve({ variant: { ...variant, stock_quantity: stock }, movement });
        }
        if (path.endsWith("stock-movements")) return Promise.resolve([...movements]);
        if (path.endsWith("variants"))
          return Promise.resolve([{ ...variant, stock_quantity: stock }]);
        return Promise.resolve(product);
      },
    );
  }
  async function openStock(withdraw = false) {
    setup(<InventoryPage />, "/admin/inventario?producto=9");
    fireEvent.click(await screen.findByRole("button", { name: /Negro \/ M/ }));
    if (withdraw) fireEvent.click(screen.getByRole("radio", { name: "Retirar stock" }));
  }
  it.each([
    ["3", 7],
    ["10", 0],
  ])("retira %s unidades con confirmación y conserva el historial", async (amount, remaining) => {
    mockStockApi();
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(true);
    await openStock(true);
    fireEvent.change(screen.getByLabelText("Unidades a retirar"), { target: { value: amount } });
    fireEvent.change(screen.getByLabelText("Motivo (opcional)"), {
      target: { value: "Prenda dañada" },
    });
    expect(screen.getByText(`Stock previsto: ${remaining} unidades.`)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Registrar retiro" }));
    await screen.findByText(/Retiro registrado/);
    expect(confirm).toHaveBeenCalledWith(expect.stringContaining(`Retirar ${amount} unidades`));
    expect(api).toHaveBeenCalledWith("/admin/variants/5/stock", {
      method: "POST",
      json: { delta: -Number(amount), reason: "Prenda dañada" },
    });
    expect(await screen.findByText(`Stock actual: ${remaining} unidades.`)).toBeInTheDocument();
    const history = await screen.findByRole("list");
    expect(
      within(history).getByText(`-${amount} unidades · Stock: ${remaining}`),
    ).toBeInTheDocument();
    expect(within(history).getByText("Ingreso inicial")).toBeInTheDocument();
  });
  it("cancela un retiro sin enviar la operación", async () => {
    mockStockApi();
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
    await openStock(true);
    fireEvent.change(screen.getByLabelText("Unidades a retirar"), { target: { value: "3" } });
    fireEvent.click(screen.getByRole("button", { name: "Registrar retiro" }));
    expect(confirm).toHaveBeenCalled();
    expect(api.mock.calls.some(([, options]) => options?.method === "POST")).toBe(false);
    expect(screen.getByText("Stock actual: 10 unidades.")).toBeInTheDocument();
  });
  it("bloquea retiros mayores al stock antes de pedir confirmación", async () => {
    mockStockApi();
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(true);
    await openStock(true);
    fireEvent.change(screen.getByLabelText("Unidades a retirar"), { target: { value: "11" } });
    fireEvent.click(screen.getByRole("button", { name: "Registrar retiro" }));
    expect(screen.getByRole("alert")).toHaveTextContent(
      "No puedes retirar más de las 10 unidades disponibles.",
    );
    expect(confirm).not.toHaveBeenCalled();
    expect(api.mock.calls.some(([, options]) => options?.method === "POST")).toBe(false);
  });
  it.each([false, true])(
    "rechaza cantidades inválidas en el formulario (retiro: %s)",
    async (withdraw) => {
      mockStockApi();
      await openStock(withdraw);
      for (const amount of ["0", "-2", "1.5", "abc"]) {
        fireEvent.change(
          screen.getByLabelText(withdraw ? "Unidades a retirar" : "Unidades a ingresar"),
          { target: { value: amount } },
        );
        fireEvent.click(
          screen.getByRole("button", { name: withdraw ? "Registrar retiro" : "Registrar ingreso" }),
        );
        expect(screen.getByRole("alert")).toHaveTextContent(
          "Ingresa una cantidad entera mayor que cero",
        );
      }
      expect(api.mock.calls.some(([, options]) => options?.method === "POST")).toBe(false);
    },
  );
  it("muestra el error del servidor sin anunciar ni simular un retiro exitoso", async () => {
    mockStockApi();
    vi.spyOn(window, "confirm").mockReturnValue(true);
    await openStock(true);
    api.mockRejectedValueOnce(
      new ApiError(400, "validation_error", "El stock disponible cambió. Actualiza el stock.", {
        delta: ["El stock resultante no puede ser negativo."],
      }),
    );
    fireEvent.change(screen.getByLabelText("Unidades a retirar"), { target: { value: "3" } });
    fireEvent.click(screen.getByRole("button", { name: "Registrar retiro" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("El stock disponible cambió.");
    expect(screen.queryByText(/Retiro registrado/)).not.toBeInTheDocument();
    expect(screen.getByText("Stock actual: 10 unidades.")).toBeInTheDocument();
  });
  it("rechaza cero, negativos, decimales y cantidades fuera de rango", () => {
    for (const value of ["", "0", "-2", "1.5", "abc", "2147483648"])
      expect(positiveQuantity(value)).toBeNull();
    expect(positiveQuantity("2")).toBe(2);
  });
  it("registra un ingreso positivo y actualiza stock e historial", async () => {
    const confirm = vi.spyOn(window, "confirm");
    let stock = 0;
    const movement = {
      id: 1,
      variant_id: 5,
      delta: 2,
      resulting_stock: 2,
      reason: "Nueva entrega",
      admin: null,
      created_at: product.created_at,
    };
    api.mockImplementation((path: string, options?: { method: string }) => {
      if (options?.method === "POST") {
        stock = 2;
        return Promise.resolve({ variant: { ...variant, stock_quantity: stock }, movement });
      }
      if (path.endsWith("stock-movements")) return Promise.resolve(stock ? [movement] : []);
      if (path.endsWith("variants"))
        return Promise.resolve([{ ...variant, stock_quantity: stock }]);
      return Promise.resolve(product);
    });
    setup(<InventoryPage />, "/admin/inventario?producto=9");
    fireEvent.click(await screen.findByRole("button", { name: /Negro \/ M/ }));
    expect(screen.getByRole("radio", { name: "Agregar stock" })).toBeChecked();
    fireEvent.change(screen.getByLabelText("Unidades a ingresar"), { target: { value: "2" } });
    fireEvent.change(screen.getByLabelText("Motivo (opcional)"), {
      target: { value: "Nueva entrega" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Registrar ingreso" }));
    await screen.findByText(/Ingreso registrado/);
    expect(api).toHaveBeenCalledWith("/admin/variants/5/stock", {
      method: "POST",
      json: { delta: 2, reason: "Nueva entrega" },
    });
    expect(await screen.findByText(/Stock actual: 2 unidades/)).toBeInTheDocument();
    const list = await screen.findByRole("list");
    expect(within(list).getByText("Nueva entrega")).toBeInTheDocument();
    expect(confirm).not.toHaveBeenCalled();
  });
});
