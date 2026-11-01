import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, apiFetch } from "./client";

function jsonResponse(body: unknown, status: number) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

afterEach(() => vi.unstubAllGlobals());

describe("ApiError.fromResponse", () => {
  it("normaliza el formato {code, message, fields}", async () => {
    const response = jsonResponse(
      { code: "validation_error", message: "Datos no válidos.", fields: { email: ["Requerido"] } },
      400,
    );

    const error = await ApiError.fromResponse(response);

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      status: 400,
      code: "validation_error",
      message: "Datos no válidos.",
      fields: { email: ["Requerido"] },
    });
  });

  it("usa un objeto de campos vacío si la API no lo envía", async () => {
    const error = await ApiError.fromResponse(
      jsonResponse({ code: "not_found", message: "No encontramos lo que buscas." }, 404),
    );

    expect(error.fields).toEqual({});
  });

  it("convierte un cuerpo que no es JSON en un error genérico", async () => {
    const error = await ApiError.fromResponse(
      new Response("<html>Bad Gateway</html>", { status: 502 }),
    );

    expect(error.status).toBe(502);
    expect(error.code).toBe("unknown_error");
    expect(error.message).toBe("Ocurrió un error inesperado. Intenta de nuevo.");
  });

  it("convierte un JSON con otra forma en un error genérico", async () => {
    const error = await ApiError.fromResponse(jsonResponse({ detail: "algo" }, 500));

    expect(error.code).toBe("unknown_error");
  });
});

describe("apiFetch", () => {
  it("antepone la URL de la API y agrega el token Bearer", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ status: "ok" }, 200));
    vi.stubGlobal("fetch", fetchMock);

    const result = await apiFetch("/me", { getToken: async () => "abc" });

    expect(result).toEqual({ status: "ok" });
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("http://localhost:8000/api/v1/me");
    expect(new Headers(init.headers).get("Authorization")).toBe("Bearer abc");
  });

  it("no envía Authorization si no hay token", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({}, 200));
    vi.stubGlobal("fetch", fetchMock);

    await apiFetch("/health", { getToken: async () => null });

    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(new Headers(init.headers).has("Authorization")).toBe(false);
  });

  it("lanza ApiError con el error de la API", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          jsonResponse(
            { code: "not_authenticated", message: "Debes iniciar sesión.", fields: {} },
            401,
          ),
        ),
    );

    await expect(apiFetch("/me")).rejects.toMatchObject({
      name: "ApiError",
      status: 401,
      code: "not_authenticated",
    });
  });

  it("lanza ApiError si no hay conexión", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));

    await expect(apiFetch("/health")).rejects.toMatchObject({ status: 0, code: "network_error" });
  });
});
