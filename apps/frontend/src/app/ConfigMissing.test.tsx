import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ConfigMissing } from "./ConfigMissing";

describe("ConfigMissing", () => {
  it("explica qué variable falta y dónde está la guía", () => {
    render(<ConfigMissing />);

    expect(screen.getByRole("heading", { name: "Falta configurar Clerk" })).toBeInTheDocument();
    expect(screen.getByText("VITE_CLERK_PUBLISHABLE_KEY")).toBeInTheDocument();
    expect(screen.getByText("docs/clerk-setup.md")).toBeInTheDocument();
  });
});
