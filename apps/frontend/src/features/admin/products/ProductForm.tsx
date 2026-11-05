import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { ApiError } from "@/shared/api/client";
import { ErrorNotice } from "@/shared/ui/Feedback";
import { initialCategories, statusLabels } from "./config";
import type { Product, ProductInput, ProductStatus } from "./types";

const money = z
  .string()
  .regex(
    /^[1-9]\d{0,11}$/,
    "Ingresa un precio positivo en COP, sin decimales (máximo 12 dígitos).",
  );
export const productSchema = z.object({
  name: z.string().trim().min(1, "Ingresa el nombre.").max(255),
  description: z.string().trim().min(1, "Ingresa la descripción."),
  price: money,
  previous_price: z.union([z.literal(""), money]),
  material: z.string().trim().min(1, "Ingresa el material.").max(120),
  category_id: z
    .string()
    .regex(/^[1-9]\d*$/, "Ingresa un ID de categoría positivo.")
    .refine((value) => Number.isSafeInteger(Number(value)), "ID fuera de rango."),
  status: z.enum(["draft", "published", "archived"]),
});
type Values = z.infer<typeof productSchema>;

export function ProductForm({
  product,
  canPublish,
  onSave,
  saving,
  error,
}: {
  product?: Product;
  canPublish?: boolean;
  onSave: (data: ProductInput) => Promise<unknown>;
  saving: boolean;
  error: unknown;
}) {
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<Values>({
    resolver: zodResolver(productSchema),
    defaultValues: {
      name: product?.name ?? "",
      description: product?.description ?? "",
      price: product?.price ?? "",
      previous_price: product?.previous_price ?? "",
      material: product?.material ?? "",
      category_id: String(product?.category.id ?? initialCategories[0].id),
      status: product?.status ?? "draft",
    },
  });
  const hasPreviousPrice = Boolean(product?.previous_price);
  async function submit(values: Values) {
    if (hasPreviousPrice && !values.previous_price) {
      setError("previous_price", {
        message: "El precio anterior no puede quitarse todavía. Conserva o cambia su valor.",
      });
      return;
    }
    if (values.status === "published" && !canPublish) {
      setError("status", {
        message:
          "Carga al menos una fotografía y espera a que termine la consulta antes de publicar.",
      });
      return;
    }
    if (
      product &&
      product.status !== "archived" &&
      values.status === "archived" &&
      !window.confirm(`¿Archivar «${product.name}»? Se retirará del catálogo.`)
    )
      return;
    const input: ProductInput = {
      name: values.name,
      description: values.description,
      price: values.price,
      material: values.material,
      category_id: Number(values.category_id),
      ...(values.previous_price ? { previous_price: values.previous_price } : {}),
      ...(product ? { status: values.status as ProductStatus } : {}),
    };
    try {
      await onSave(input);
    } catch (cause) {
      if (cause instanceof ApiError) {
        for (const [field, messages] of Object.entries(cause.fields)) {
          const key = field === "category" ? "category_id" : field;
          if (key in values) setError(key as keyof Values, { message: messages.join(" ") });
        }
      }
    }
  }
  const fieldError = (name: keyof Values) =>
    errors[name] && (
      <span id={`error-${name}`} className="field-error">
        {errors[name]?.message}
      </span>
    );
  const accessibility = (name: keyof Values) => ({
    "aria-invalid": Boolean(errors[name]),
    "aria-describedby": errors[name] ? `error-${name}` : undefined,
  });
  return (
    <form noValidate onSubmit={handleSubmit(submit)} className="space-y-5">
      <ErrorNotice error={error} />
      <fieldset disabled={saving || isSubmitting} className="grid gap-5 sm:grid-cols-2">
        <label className="field sm:col-span-2">
          Nombre
          <input {...register("name")} {...accessibility("name")} maxLength={255} />
          {fieldError("name")}
        </label>
        <label className="field sm:col-span-2">
          Descripción
          <textarea {...register("description")} {...accessibility("description")} rows={4} />
          {fieldError("description")}
        </label>
        <label className="field">
          Precio (COP)
          <input
            {...register("price")}
            {...accessibility("price")}
            inputMode="numeric"
            placeholder="Ej. 75000"
          />
          {fieldError("price")}
        </label>
        <label className="field">
          Precio anterior (opcional)
          <input
            {...register("previous_price")}
            {...accessibility("previous_price")}
            inputMode="numeric"
            placeholder="Sin precio anterior"
          />
          {fieldError("previous_price")}
          {hasPreviousPrice && (
            <span className="muted text-sm">
              Por ahora puedes cambiar este precio, pero no quitarlo.
            </span>
          )}
        </label>
        <label className="field">
          Material
          <input {...register("material")} {...accessibility("material")} maxLength={120} />
          {fieldError("material")}
        </label>
        <label className="field">
          Categoría (ID)
          <input
            {...register("category_id")}
            {...accessibility("category_id")}
            list="initial-categories"
            inputMode="numeric"
          />
          {fieldError("category_id")}
          <datalist id="initial-categories">
            {initialCategories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </datalist>
        </label>
        <div className="sm:col-span-2 text-sm muted">
          <p>
            Categorías iniciales esperadas:{" "}
            {initialCategories.map((category) => `${category.id}: ${category.name}`).join(" · ")}.
          </p>
          {product && (
            <p>
              Categoría actual: {product.category.name} (ID {product.category.id}).
            </p>
          )}
        </div>
        {product && (
          <label className="field">
            Estado
            <select aria-label="Estado" {...register("status")} {...accessibility("status")}>
              {Object.entries(statusLabels).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
            {fieldError("status")}
            <span className="muted text-sm">Para publicar se necesita al menos una foto.</span>
          </label>
        )}
      </fieldset>
      <button className="btn-primary" disabled={saving || isSubmitting} type="submit">
        {saving || isSubmitting ? "Guardando…" : product ? "Guardar cambios" : "Crear borrador"}
      </button>
    </form>
  );
}
