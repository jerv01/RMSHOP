import { useMemo } from "react";
import { Link, useLocation, useNavigate } from "react-router";
import { QueryFeedback, SuccessNotice } from "@/shared/ui/Feedback";
import { formatCOP } from "@/shared/lib/formatCOP";
import { useAdminProducts } from "./api";
import { ProductLookup } from "./ProductLookup";
import { useProductSession } from "./ProductSession";
import { statusLabels } from "./config";

export function ProductsPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const archived = (location.state as { archived?: number } | null)?.archived;
  const { products: sessionProducts } = useProductSession();
  const adminProducts = useAdminProducts();

  const allProducts = useMemo(() => {
    const fromServer = Array.isArray(adminProducts.data) ? adminProducts.data : [];
    const seen = new Set<number>();
    const merged = [];
    for (const item of [...fromServer, ...sessionProducts]) {
      if (seen.has(item.id)) continue;
      seen.add(item.id);
      merged.push(item);
    }
    return merged;
  }, [adminProducts.data, sessionProducts]);

  return (
    <div className="space-y-8">
      <div className="page-heading">
        <div>
          <p className="eyebrow">Catálogo · Administración</p>
          <h1>Productos</h1>
        </div>
        <Link className="btn-primary" to="/admin/productos/nuevo">
          Nuevo producto
        </Link>
      </div>
      {archived && <SuccessNotice>Producto #{archived} archivado.</SuccessNotice>}
      <section className="panel space-y-4">
        <h2>Consultar un producto por ID</h2>
        <p className="muted">
          Ingresa su ID para ir directamente a editar datos, fotos y variantes, o selecciónalo en el
          listado inferior.
        </p>
        <ProductLookup onSelect={(id) => void navigate(`/admin/productos/${id}`)} />
      </section>
      <section className="space-y-4">
        <div className="page-heading">
          <h2>Catálogo registrado ({allProducts.length})</h2>
          <button
            type="button"
            className="btn-secondary"
            disabled={adminProducts.isFetching}
            onClick={() => void adminProducts.refetch()}
          >
            Actualizar lista
          </button>
        </div>
        <QueryFeedback
          pending={adminProducts.isPending && sessionProducts.length === 0}
          error={adminProducts.error}
          retry={adminProducts.refetch}
        />
        {!adminProducts.isPending && allProducts.length === 0 ? (
          <p className="panel muted">Todavía no hay productos registrados en el catálogo.</p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {allProducts.map((product) => (
              <article className="panel flex flex-col justify-between space-y-3" key={product.id}>
                <div className="space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <span className="badge">{statusLabels[product.status]}</span>
                    <span className="text-xs font-mono text-muted">ID #{product.id}</span>
                  </div>
                  <h3>{product.name}</h3>
                  <p className="muted text-sm">{product.category.name}</p>
                  <p className="font-semibold">{formatCOP(Number(product.price))}</p>
                </div>
                <div className="flex flex-wrap items-center gap-3 pt-2">
                  <Link className="btn-secondary text-xs" to={`/admin/productos/${product.id}`}>
                    Administrar producto
                  </Link>
                  <Link
                    className="text-link text-xs"
                    to={`/admin/inventario?producto=${product.id}`}
                  >
                    Inventario
                  </Link>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
