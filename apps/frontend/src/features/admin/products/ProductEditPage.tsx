import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Link, useLocation, useNavigate, useParams } from "react-router";
import { useApi } from "@/shared/api/useApi";
import { ErrorNotice, QueryFeedback, SuccessNotice } from "@/shared/ui/Feedback";
import { productPath, useAdminRefresh, useImages, useProduct } from "./api";
import { ProductForm } from "./ProductForm";
import { ProductImages } from "./ProductImages";
import { ProductVariants } from "./ProductVariants";
import { useProductSession } from "./ProductSession";
import { statusLabels } from "./config";
import type { Product, ProductInput } from "./types";

export function ProductEditPage() {
  const params = useParams();
  const id = Number(params.id);
  if (!Number.isSafeInteger(id) || id <= 0)
    return (
      <div>
        <h1>ID de producto inválido</h1>
        <Link className="text-link" to="/admin/productos">
          Volver a productos
        </Link>
      </div>
    );
  return <ProductEditor key={id} id={id} />;
}
function ProductEditor({ id }: { id: number }) {
  const api = useApi();
  const refresh = useAdminRefresh();
  const query = useProduct(id);
  const images = useImages(id);
  const { remember } = useProductSession();
  const location = useLocation();
  const navigate = useNavigate();
  const [saved, setSaved] = useState(false);
  const arrival = location.state as { created?: boolean; warning?: string } | null;
  const update = useMutation({
    mutationFn: (json: ProductInput) => api<Product>(productPath(id), { method: "PATCH", json }),
    onSuccess: async (product) => {
      remember(product);
      setSaved(true);
      await refresh();
    },
  });
  const archive = useMutation({
    mutationFn: () => api<void>(productPath(id), { method: "DELETE" }),
    onSuccess: async () => {
      if (query.data) remember({ ...query.data, status: "archived" });
      await refresh();
      void navigate("/admin/productos", { state: { archived: id } });
    },
  });
  return (
    <div className="space-y-7">
      <Link className="text-link" to="/admin/productos">
        ← Productos
      </Link>
      <QueryFeedback pending={query.isPending} error={query.error} retry={query.refetch} />
      {query.data && (
        <>
          <div className="page-heading">
            <div>
              <p className="eyebrow">Producto #{id}</p>
              <h1>{query.data.name}</h1>
              <span className="badge">{statusLabels[query.data.status]}</span>
            </div>
            <Link className="btn-secondary" to={`/admin/inventario?producto=${id}`}>
              Gestionar inventario
            </Link>
          </div>
          {arrival?.created && (
            <SuccessNotice>Producto creado como borrador. Conserva su ID: {id}.</SuccessNotice>
          )}
          {arrival?.warning && (
            <p className="notice notice-warning" role="status">
              {arrival.warning}
            </p>
          )}
          {saved && <SuccessNotice>Cambios guardados.</SuccessNotice>}
          <section className="panel space-y-5">
            <h2>Datos del producto</h2>
            <ProductForm
              key={query.data.updated_at}
              product={query.data}
              canPublish={images.isSuccess && images.data.length > 0}
              onSave={async (input) => {
                setSaved(false);
                return update.mutateAsync(input);
              }}
              saving={update.isPending || archive.isPending}
              error={update.error}
            />
          </section>
          <ProductImages productId={id} published={query.data.status === "published"} />
          <ProductVariants productId={id} />
          <section className="panel space-y-4">
            <h2>Archivar producto</h2>
            <p className="muted">Lo retira del catálogo conservando sus datos.</p>
            <ErrorNotice error={archive.error} />
            <button
              className="btn-danger"
              disabled={archive.isPending || update.isPending || query.data.status === "archived"}
              onClick={() => {
                if (window.confirm(`¿Archivar «${query.data?.name}»? Se retirará del catálogo.`))
                  archive.mutate();
              }}
            >
              {archive.isPending
                ? "Archivando…"
                : query.data.status === "archived"
                  ? "Producto archivado"
                  : "Archivar producto"}
            </button>
          </section>
        </>
      )}
    </div>
  );
}
