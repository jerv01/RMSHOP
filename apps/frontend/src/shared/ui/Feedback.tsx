import { ApiError } from "@/shared/api/client";

const fieldLabels: Record<string, string> = {
  name: "Nombre",
  description: "Descripción",
  price: "Precio",
  previous_price: "Precio anterior",
  material: "Material",
  category: "Categoría",
  category_id: "Categoría",
  status: "Estado",
  image: "Fotografía",
  image_ids: "Orden de fotografías",
  position: "Posición",
  alt_text: "Texto alternativo",
  color: "Color",
  size: "Talla",
  colors: "Colores",
  sizes: "Tallas",
  stock_quantity: "Stock",
  delta: "Cantidad",
  reason: "Motivo",
  municipality: "Municipio",
  address_line: "Dirección de entrega",
  recipient_name: "Nombre de quien recibe",
  phone: "Teléfono",
  method: "Medio de pago",
  token: "Token de tarjeta",
  payment_method_id: "Tipo de tarjeta",
  payment_type: "Modalidad de tarjeta",
  financial_institution: "Banco PSE",
  entity_type: "Tipo de persona",
  first_name: "Nombre",
  last_name: "Apellido",
  identification_type: "Tipo de documento",
  identification_number: "Número de documento",
  phone_area_code: "Indicativo telefónico",
  phone_number: "Número de teléfono",
  zip_code: "Código postal",
  street_number: "Nomenclatura / número",
  neighborhood: "Barrio",
  non_field_errors: "Validación",
};

export function ErrorNotice({ error }: { error: unknown }) {
  if (!error) return null;
  return (
    <div role="alert" className="notice notice-error">
      <p>{error instanceof Error ? error.message : "No se pudo completar la operación."}</p>
      {error instanceof ApiError &&
        Object.entries(error.fields).map(([field, messages]) => (
          <p key={field}>
            {fieldLabels[field] ?? "Validación"}: {messages.join(" ")}
          </p>
        ))}
    </div>
  );
}
export function QueryFeedback({
  pending,
  error,
  retry,
}: {
  pending: boolean;
  error: unknown;
  retry: () => unknown;
}) {
  if (pending) return <p role="status">Cargando…</p>;
  if (!error) return null;
  return (
    <div>
      <ErrorNotice error={error} />
      <button className="btn-secondary" onClick={() => void retry()}>
        Reintentar
      </button>
    </div>
  );
}
export function SuccessNotice({ children }: { children: React.ReactNode }) {
  return (
    <p role="status" className="notice notice-success">
      {children}
    </p>
  );
}
