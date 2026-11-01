import { describe, expect, it } from "vitest";
import { formatCOP } from "./formatCOP";

// Intl separa el símbolo con un espacio duro (U+00A0); se normaliza para comparar.
const format = (value: number) => formatCOP(value).replace(/ /g, " ");

describe("formatCOP", () => {
  it("usa punto como separador de miles", () => {
    expect(format(25000)).toBe("$ 25.000");
    expect(format(1234567)).toBe("$ 1.234.567");
  });

  it("no muestra decimales", () => {
    expect(format(0)).toBe("$ 0");
    expect(format(9999.6)).toBe("$ 10.000");
  });

  it("formatea valores negativos", () => {
    expect(format(-5000)).toBe("-$ 5.000");
  });
});
