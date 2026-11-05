import { useMutation } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router";
import { useApi } from "@/shared/api/useApi";
import { ProductForm } from "./ProductForm";
import { useProductSession } from "./ProductSession";
import type { Product, ProductInput } from "./types";

export function ProductCreatePage() {
  const api = useApi();
  const navigate = useNavigate();
  const { remember } = useProductSession();
  const create = useMutation({
    mutationFn: (json: ProductInput) => api<Product>("/admin/products", { method: "POST", json }),
    onSuccess: (product) => {
      remember(product, true);
      void navigate(`/admin/productos/${product.id}`, {
        replace: true,
        state: { created: true, warning: product.warning },
      });
    },
  });
  return (
    <div className="space-y-6">
      <Link className="text-link" to="/admin/productos">
        ← Productos
      </Link>
      <div>
        <p className="eyebrow">Nuevo diseño</p>
        <h1>Crear producto</h1>
        <p className="muted">
          Guarda los datos como borrador. Después podrás agregar fotos, colores y tallas.
        </p>
      </div>
      <section className="panel">
        <ProductForm onSave={create.mutateAsync} saving={create.isPending} error={create.error} />
      </section>
    </div>
  );
}
