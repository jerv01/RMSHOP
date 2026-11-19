export interface ShippingZoneOption {
  municipality: string;
  fee: number;
  estimatedDelivery: string;
}

/** Zonas de cobertura y tarifas fijas en el Valle del Cauca (HU-25 a HU-28). */
export const SHIPPING_ZONES: readonly ShippingZoneOption[] = [
  { municipality: "Cali", fee: 5000, estimatedDelivery: "3 a 5 días" },
  { municipality: "Palmira", fee: 10000, estimatedDelivery: "3 a 5 días" },
  { municipality: "Jamundí", fee: 10000, estimatedDelivery: "3 a 5 días" },
  { municipality: "Yumbo", fee: 10000, estimatedDelivery: "3 a 5 días" },
] as const;

export const ESTIMATED_DELIVERY_RANGE = "3 a 5 días";
export const MUNICIPALITY_NOT_COVERED_MESSAGE = "Solo enviamos a Cali, Palmira, Jamundí y Yumbo.";

/** Normaliza un municipio igual que el backend (minúsculas, sin tildes ni espacios extra). */
export function normalizeMunicipality(value: string): string {
  return (value ?? "")
    .trim()
    .replace(/\s+/g, " ")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

export function findShippingZone(municipality: string): ShippingZoneOption | null {
  const target = normalizeMunicipality(municipality);
  if (!target) return null;
  return SHIPPING_ZONES.find((zone) => normalizeMunicipality(zone.municipality) === target) ?? null;
}
