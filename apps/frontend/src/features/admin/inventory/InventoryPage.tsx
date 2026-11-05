import { useState, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router";
import { useMutation } from "@tanstack/react-query";
import { useApi } from "@/shared/api/useApi";
import { ErrorNotice, QueryFeedback, SuccessNotice } from "@/shared/ui/Feedback";
import {
  useAdminProducts,
  useAdminRefresh,
  useMovements,
  useProduct,
  useVariants,
} from "../products/api";
import { statusLabels } from "../products/config";
import { ProductLookup } from "../products/ProductLookup";
import type { StockMovement, Variant } from "../products/types";

export function positiveQuantity(value: string): number | null {
  if (!/^[1-9]\d*$/.test(value)) return null;
  const quantity = Number(value);
  return Number.isSafeInteger(quantity) && quantity <= 2147483647 ? quantity : null;
}
export function InventoryPage() {
  const [search, setSearch] = useSearchParams();
  const rawId = search.get("producto");
  const id = Number(rawId);
  const valid = Number.isSafeInteger(id) && id > 0;
  const adminProducts = useAdminProducts(!valid);
  const productList = Array.isArray(adminProducts.data) ? adminProducts.data : [];

  return (
    <div className="space-y-7">
      <div>
        <p className="eyebrow">Existencias · Administración</p>
        <h1>Inventario</h1>
        <p className="muted">
          Consulta un producto y registra ingresos o retiros por color y talla.
        </p>
      </div>
      <section className="panel space-y-4">
        <h2>Seleccionar producto</h2>
        <ProductLookup onSelect={(value) => setSearch({ producto: String(value) })} />
        {!valid && productList.length > 0 && (
          <div className="space-y-2 pt-2">
            <p className="text-xs font-semibold uppercase tracking-wider text-muted">
              O elige un producto del catálogo:
            </p>
            <div className="flex flex-wrap gap-2">
              {productList.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setSearch({ producto: String(item.id) })}
                  className="btn-secondary text-xs"
                >
                  #{item.id} · {item.name} ({statusLabels[item.status]})
                </button>
              ))}
            </div>
          </div>
        )}
      </section>
      {rawId && !valid && (
        <p role="alert" className="field-error">
          El ID debe ser un número entero positivo.
        </p>
      )}
      {valid && <ProductInventory key={id} productId={id} />}
    </div>
  );
}
function ProductInventory({ productId }: { productId: number }) {
  const product = useProduct(productId);
  const variants = useVariants(productId);
  const [selectedId, setSelectedId] = useState(0);
  const selected = variants.data?.find((item) => item.id === selectedId);
  return (
    <section className="space-y-5">
      <QueryFeedback pending={product.isPending} error={product.error} retry={product.refetch} />
      {product.data && (
        <>
          <div className="page-heading">
            <div>
              <h2>{product.data.name}</h2>
              <p className="muted">Producto #{productId}</p>
            </div>
            <button
              className="btn-secondary"
              disabled={variants.isFetching}
              onClick={() => void variants.refetch()}
            >
              Actualizar stock
            </button>
            <Link className="text-link" to={`/admin/productos/${productId}`}>
              Editar producto y variantes
            </Link>
          </div>
          <QueryFeedback
            pending={variants.isPending}
            error={variants.error}
            retry={variants.refetch}
          />
          {variants.isSuccess && (
            <>
              {!variants.data.length ? (
                <p className="panel muted">
                  No hay variantes. Agrega colores y tallas desde la edición del producto.
                </p>
              ) : (
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {variants.data.map((variant) => (
                    <button
                      key={variant.id}
                      className={`panel text-left ${selectedId === variant.id ? "ring-2 ring-black" : "hover:border-black"}`}
                      aria-pressed={selectedId === variant.id}
                      onClick={() => setSelectedId(variant.id)}
                    >
                      <span className="font-medium">
                        {variant.color} / {variant.size}
                      </span>
                      <span className="block muted text-sm">Variante #{variant.id}</span>
                      <span className="mt-3 block text-2xl font-semibold">
                        {variant.stock_quantity}
                        <span className="ml-2 text-sm font-normal">unidades</span>
                      </span>
                      {variant.stock_quantity === 0 && <span className="badge mt-2">Agotado</span>}
                    </button>
                  ))}
                </div>
              )}
              {variants.data.length > 0 && !selected && (
                <p className="muted">
                  Selecciona una combinación para agregar o retirar unidades y consultar sus
                  movimientos.
                </p>
              )}
              {selected && <VariantStock key={selected.id} variant={selected} />}
            </>
          )}
        </>
      )}
    </section>
  );
}
function VariantStock({ variant }: { variant: Variant }) {
  const api = useApi();
  const refresh = useAdminRefresh();
  const history = useMovements(variant.id);
  const [quantity, setQuantity] = useState("");
  const [reason, setReason] = useState("");
  const [validation, setValidation] = useState("");
  const [operation, setOperation] = useState<"add" | "remove">("add");
  const withdrawing = operation === "remove";
  const amount = positiveQuantity(quantity);
  const projectedStock =
    amount === null ? null : variant.stock_quantity + (withdrawing ? -amount : amount);
  const adjustment = useMutation({
    mutationFn: (delta: number) =>
      api<{ variant: Variant; movement: StockMovement }>(`/admin/variants/${variant.id}/stock`, {
        method: "POST",
        json: {
          delta,
          reason: reason.trim() || (delta < 0 ? "Retiro de mercancía" : "Ingreso de mercancía"),
        },
      }),
    onSuccess: async () => {
      setQuantity("");
      setReason("");
      await refresh();
    },
  });
  function submit(event: FormEvent) {
    event.preventDefault();
    setValidation("");
    adjustment.reset();
    const amount = positiveQuantity(quantity);
    if (amount === null) {
      setValidation("Ingresa una cantidad entera mayor que cero (máximo 2147483647).");
      return;
    }
    if (withdrawing && amount > variant.stock_quantity) {
      setValidation(`No puedes retirar más de las ${variant.stock_quantity} unidades disponibles.`);
      return;
    }
    const delta = withdrawing ? -amount : amount;
    if (delta + variant.stock_quantity > 2147483647) {
      setValidation("El stock resultante supera el máximo admitido.");
      return;
    }
    if (
      withdrawing &&
      !window.confirm(
        `¿Retirar ${amount} unidades de ${variant.color} / ${variant.size}? El stock quedará en ${variant.stock_quantity - amount} unidades.`,
      )
    )
      return;
    adjustment.mutate(delta);
  }
  return (
    <div className="space-y-5">
      <section className="panel space-y-5">
        <div>
          <h2>
            Gestionar stock · {variant.color} / {variant.size}
          </h2>
          <p className="muted">Stock actual: {variant.stock_quantity} unidades.</p>
        </div>
        <form noValidate onSubmit={submit} className="space-y-4">
          <fieldset disabled={adjustment.isPending}>
            <legend className="mb-2 text-sm font-medium">Tipo de movimiento</legend>
            <div className="flex flex-wrap gap-3">
              {(
                [
                  ["add", "Agregar stock"],
                  ["remove", "Retirar stock"],
                ] as const
              ).map(([value, label]) => (
                <label
                  key={value}
                  className={`flex min-h-11 cursor-pointer items-center gap-2 rounded border px-4 py-2 text-sm ${operation === value ? "border-black bg-surface font-medium" : "border-border"}`}
                >
                  <input
                    type="radio"
                    name="stock-operation"
                    value={value}
                    checked={operation === value}
                    onChange={() => {
                      setOperation(value);
                      setValidation("");
                      adjustment.reset();
                    }}
                    className="accent-black"
                  />
                  {label}
                </label>
              ))}
            </div>
          </fieldset>
          <fieldset disabled={adjustment.isPending} className="grid gap-4 sm:grid-cols-2">
            <label className="field">
              {withdrawing ? "Unidades a retirar" : "Unidades a ingresar"}
              <input
                required
                type="number"
                min="1"
                max="2147483647"
                step="1"
                value={quantity}
                onChange={(event) => {
                  setQuantity(event.target.value);
                  setValidation("");
                  adjustment.reset();
                }}
                aria-describedby={validation ? "stock-validation" : undefined}
                aria-invalid={Boolean(validation)}
              />
            </label>
            <label className="field">
              Motivo (opcional)
              <input
                value={reason}
                maxLength={255}
                onChange={(event) => setReason(event.target.value)}
                placeholder={withdrawing ? "Retiro de mercancía" : "Ingreso de mercancía"}
              />
            </label>
          </fieldset>
          {validation && (
            <p id="stock-validation" role="alert" className="field-error">
              {validation}
            </p>
          )}
          {projectedStock !== null && projectedStock >= 0 && projectedStock <= 2147483647 && (
            <p className="muted">Stock previsto: {projectedStock} unidades.</p>
          )}
          <ErrorNotice error={adjustment.error} />
          {adjustment.isSuccess && (
            <SuccessNotice>
              {adjustment.data.movement.delta < 0 ? "Retiro registrado." : "Ingreso registrado."}{" "}
              Stock al guardar: {adjustment.data.variant.stock_quantity} unidades.
            </SuccessNotice>
          )}
          <button
            className={withdrawing ? "btn-danger" : "btn-primary"}
            disabled={adjustment.isPending}
            type="submit"
          >
            {adjustment.isPending
              ? "Registrando…"
              : withdrawing
                ? "Registrar retiro"
                : "Registrar ingreso"}
          </button>
        </form>
      </section>
      <section className="panel space-y-4">
        <div className="page-heading">
          <h2>Historial de movimientos</h2>
          <button
            className="btn-secondary"
            disabled={history.isFetching}
            onClick={() => void history.refetch()}
          >
            Actualizar historial
          </button>
        </div>
        <QueryFeedback pending={history.isPending} error={history.error} retry={history.refetch} />
        {history.isSuccess &&
          (history.data.length ? (
            <ol className="divide-y divide-border">
              {history.data.map((movement) => (
                <li key={movement.id} className="py-4 space-y-1">
                  <div className="flex flex-wrap justify-between gap-2">
                    <strong>
                      {movement.delta > 0 ? "+" : ""}
                      {movement.delta} unidades · Stock: {movement.resulting_stock}
                    </strong>
                    <time dateTime={movement.created_at} className="muted text-sm">
                      {new Intl.DateTimeFormat("es-CO", {
                        dateStyle: "medium",
                        timeStyle: "short",
                        timeZone: "America/Bogota",
                      }).format(new Date(movement.created_at))}
                    </time>
                  </div>
                  <p>{movement.reason}</p>
                  <p className="muted text-sm">
                    {movement.admin
                      ? [movement.admin.first_name, movement.admin.last_name]
                          .filter(Boolean)
                          .join(" ") || movement.admin.email
                      : "Administrador no disponible"}
                  </p>
                </li>
              ))}
            </ol>
          ) : (
            <p className="muted">Esta variante todavía no tiene movimientos registrados.</p>
          ))}
      </section>
    </div>
  );
}
