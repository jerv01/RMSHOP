import { Link, useLocation, useNavigate } from "react-router";
import { SuccessNotice } from "@/shared/ui/Feedback";
import { formatCOP } from "@/shared/lib/formatCOP";
import { ProductLookup } from "./ProductLookup";
import { useProductSession } from "./ProductSession";
import { statusLabels } from "./config";

export function ProductsPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const archived = (location.state as { archived?: number } | null)?.archived;
  const { products } = useProductSession();
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
        <h2>Consultar un producto</h2>
        <p className="muted">
          Ingresa su ID para editar datos, fotos y variantes. La consulta del catálogo completo aún
          no está disponible.
        </p>
        <ProductLookup onSelect={(id) => void navigate(`/admin/productos/${id}`)} />
      </section>
      <section className="space-y-4">
        <h2>Creados durante esta sesión</h2>
        <p className="muted">
          Esta lista solo incluye productos creados aquí. Se vacía al recargar o cambiar de cuenta.
        </p>
        {products.length === 0 ? (
          <p className="panel muted">Todavía no has creado productos en esta sesión.</p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            {products.map((product) => (
              <article className="panel space-y-3" key={product.id}>
                <span className="badge">{statusLabels[product.status]}</span>
                <h3>{product.name}</h3>
                <p className="muted">
                  ID {product.id} · {product.category.name}
                </p>
                <p>{formatCOP(Number(product.price))}</p>
                <Link className="text-link" to={`/admin/productos/${product.id}`}>
                  Administrar producto
                </Link>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
