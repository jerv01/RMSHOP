import { useState, type FormEvent } from "react";
import { Link } from "react-router";
import { useMutation } from "@tanstack/react-query";
import { useApi } from "@/shared/api/useApi";
import { ErrorNotice, QueryFeedback, SuccessNotice } from "@/shared/ui/Feedback";
import { productPath, useAdminRefresh, useMovements, useVariants } from "./api";
import type { StockMovement, Variant } from "./types";

export function splitAttributes(value: string): string[] {
  const unique = new Map<string, string>();
  for (const raw of value.split(",")) {
    const item = raw.trim();
    const key = item.toLocaleLowerCase();
    if (item && !unique.has(key)) unique.set(key, item);
  }
  return [...unique.values()];
}
export function isDuplicate(variants: Variant[], color: string, size: string) {
  return variants.some(
    (item) =>
      item.color.toLocaleLowerCase() === color.trim().toLocaleLowerCase() &&
      item.size.toLocaleLowerCase() === size.trim().toLocaleLowerCase(),
  );
}
export function ProductVariants({ productId }: { productId: number }) {
  const api = useApi();
  const refresh = useAdminRefresh();
  const query = useVariants(productId);
  const [color, setColor] = useState("");
  const [size, setSize] = useState("");
  const [colors, setColors] = useState("");
  const [sizes, setSizes] = useState("");
  const [message, setMessage] = useState("");
  const [validation, setValidation] = useState("");
  const create = useMutation({
    mutationFn: async ({ bulk }: { bulk: boolean }): Promise<Variant | Variant[]> =>
      bulk
        ? api<Variant[]>(`${productPath(productId)}/variants/bulk`, {
            method: "POST",
            json: { colors: splitAttributes(colors), sizes: splitAttributes(sizes) },
          })
        : api<Variant>(`${productPath(productId)}/variants`, {
            method: "POST",
            json: { color: color.trim(), size: size.trim(), stock_quantity: 0 },
          }),
    onSuccess: async (_, { bulk }) => {
      if (bulk) {
        setColors("");
        setSizes("");
      } else {
        setColor("");
        setSize("");
      }
      setMessage(
        bulk
          ? "Combinaciones guardadas. Las existentes se conservaron."
          : "Variante creada con stock cero.",
      );
      await refresh();
    },
  });
  function submit(event: FormEvent, bulk: boolean) {
    event.preventDefault();
    setMessage("");
    setValidation("");
    create.reset();
    if (bulk) {
      const cs = splitAttributes(colors);
      const ss = splitAttributes(sizes);
      if (
        !cs.length ||
        !ss.length ||
        cs.some((value) => value.length > 50) ||
        ss.some((value) => value.length > 20)
      ) {
        setValidation(
          "Indica al menos un color (máximo 50 caracteres) y una talla (máximo 20), separados por comas.",
        );
        return;
      }
    } else if (!color.trim() || !size.trim() || isDuplicate(query.data ?? [], color, size)) {
      setValidation("Indica color y talla sin repetir una combinación existente.");
      return;
    }
    create.mutate({ bulk });
  }
  return (
    <section className="panel space-y-5">
      <div className="page-heading">
        <div>
          <h2>Colores y tallas</h2>
          <p className="muted">
            Las nuevas combinaciones empiezan en cero. Registra los ingresos desde inventario.
          </p>
        </div>
        <Link className="text-link" to={`/admin/inventario?producto=${productId}`}>
          Abrir inventario
        </Link>
      </div>
      <QueryFeedback pending={query.isPending} error={query.error} retry={query.refetch} />
      {query.isSuccess && (
        <>
          {query.data.length ? (
            <ul className="divide-y divide-border">
              {query.data.map((variant) => (
                <VariantRow key={variant.id} variant={variant} />
              ))}
            </ul>
          ) : (
            <p className="muted">Aún no hay variantes.</p>
          )}
          <p className="muted text-sm">
            Solo se permite quitar variantes sin stock y sin historial de movimientos.
          </p>
          <ErrorNotice error={create.error} />
          {validation && (
            <p role="alert" className="field-error">
              {validation}
            </p>
          )}
          {message && <SuccessNotice>{message}</SuccessNotice>}
          <form
            onSubmit={(event) => submit(event, false)}
            className="space-y-3 border-t border-border pt-5"
          >
            <h3>Agregar una combinación</h3>
            <fieldset disabled={create.isPending} className="flex flex-wrap items-end gap-3">
              <label className="field flex-1">
                Color
                <input
                  required
                  maxLength={50}
                  value={color}
                  onChange={(event) => setColor(event.target.value)}
                  placeholder="Negro"
                />
              </label>
              <label className="field flex-1">
                Talla
                <input
                  required
                  maxLength={20}
                  value={size}
                  onChange={(event) => setSize(event.target.value)}
                  placeholder="M"
                />
              </label>
              <button className="btn-primary" type="submit" disabled={create.isPending}>
                Agregar variante
              </button>
            </fieldset>
          </form>
          <form
            onSubmit={(event) => submit(event, true)}
            className="space-y-3 border-t border-border pt-5"
          >
            <h3>Generar combinaciones</h3>
            <p className="muted text-sm">
              Se combinan todos los colores con todas las tallas. Los duplicados se omiten.
            </p>
            <fieldset disabled={create.isPending} className="grid gap-3 sm:grid-cols-2">
              <label className="field">
                Colores separados por comas
                <input
                  required
                  value={colors}
                  onChange={(event) => setColors(event.target.value)}
                  placeholder="Negro, Blanco"
                />
              </label>
              <label className="field">
                Tallas separadas por comas
                <input
                  required
                  value={sizes}
                  onChange={(event) => setSizes(event.target.value)}
                  placeholder="S, M, L"
                />
              </label>
              <p className="muted text-sm sm:col-span-2">
                Hasta {splitAttributes(colors).length * splitAttributes(sizes).length}{" "}
                combinaciones.
              </p>
              <button
                className="btn-secondary sm:col-span-2"
                disabled={create.isPending}
                type="submit"
              >
                {create.isPending ? "Guardando…" : "Generar variantes"}
              </button>
            </fieldset>
          </form>
        </>
      )}
    </section>
  );
}
function VariantRow({ variant }: { variant: Variant }) {
  const api = useApi();
  // No se habilita la eliminación mientras no se haya verificado el historial.
  const history = useMovements(variant.stock_quantity === 0 ? variant.id : 0);
  const refresh = useAdminRefresh();
  const remove = useMutation({
    mutationFn: async () => {
      const movements = await api<StockMovement[]>(`/admin/variants/${variant.id}/stock-movements`);
      if (movements.length) throw new Error("Esta variante tiene historial y debe conservarse.");
      const variants = await api<Variant[]>(`${productPath(variant.product_id)}/variants`);
      if (variants.find((item) => item.id === variant.id)?.stock_quantity !== 0)
        throw new Error("El stock cambió. Actualiza las variantes antes de continuar.");
      return api<void>(`${productPath(variant.product_id)}/variants/${variant.id}`, {
        method: "DELETE",
      });
    },
    onSuccess: refresh,
  });
  const safe = variant.stock_quantity === 0 && history.isSuccess && history.data.length === 0;
  return (
    <li className="py-4 space-y-2">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <span className="font-medium">
            {variant.color} / {variant.size}
          </span>
          <p className="muted text-sm">
            Variante #{variant.id} ·{" "}
            {variant.stock_quantity > 0 ? `${variant.stock_quantity} unidades` : "Agotado"}
          </p>
        </div>
        {safe ? (
          <button
            className="btn-danger"
            disabled={remove.isPending}
            onClick={() => {
              if (window.confirm(`¿Eliminar la variante ${variant.color} / ${variant.size}?`))
                remove.mutate();
            }}
          >
            {remove.isPending ? "Eliminando…" : `Eliminar ${variant.color} / ${variant.size}`}
          </button>
        ) : (
          <span className="muted text-sm">
            {variant.stock_quantity > 0
              ? "Tiene stock"
              : history.isPending
                ? "Verificando historial…"
                : history.isError
                  ? "No se pudo verificar el historial"
                  : "Conservada por historial"}
          </span>
        )}
      </div>
      <ErrorNotice error={remove.error} />
      {history.isError && (
        <button className="text-link" onClick={() => void history.refetch()}>
          Reintentar historial de variante #{variant.id}
        </button>
      )}
    </li>
  );
}
