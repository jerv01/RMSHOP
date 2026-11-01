const copFormatter = new Intl.NumberFormat("es-CO", {
  style: "currency",
  currency: "COP",
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});

/** Formatea un valor en pesos colombianos, sin decimales: 25000 -> "$ 25.000". */
export function formatCOP(value: number): string {
  return copFormatter.format(value);
}
