import { env } from "@/shared/lib/env";

export type FieldErrors = Record<string, string[]>;
export type TokenGetter = () => Promise<string | null>;

/** Error de la API normalizado al formato único `{code, message, fields}` del backend. */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly fields: FieldErrors;

  constructor(status: number, code: string, message: string, fields: FieldErrors = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.fields = fields;
  }

  /** Convierte una respuesta de error en `ApiError`, incluso si el cuerpo no es el esperado. */
  static async fromResponse(response: Response): Promise<ApiError> {
    let body: unknown = null;
    try {
      body = await response.json();
    } catch {
      // El cuerpo no es JSON (por ejemplo, una página de error de un proxy).
    }

    if (typeof body === "object" && body !== null) {
      const { code, message, fields } = body as Record<string, unknown>;
      if (typeof code === "string" && typeof message === "string") {
        return new ApiError(response.status, code, message, normalizeFields(fields));
      }
    }
    return new ApiError(
      response.status,
      "unknown_error",
      "Ocurrió un error inesperado. Intenta de nuevo.",
    );
  }
}

function normalizeFields(fields: unknown): FieldErrors {
  if (typeof fields !== "object" || fields === null) return {};
  const result: FieldErrors = {};
  for (const [name, messages] of Object.entries(fields)) {
    result[name] = Array.isArray(messages) ? messages.map(String) : [String(messages)];
  }
  return result;
}

export interface RequestOptions extends Omit<RequestInit, "body"> {
  /** Si se entrega, se agrega `Authorization: Bearer <token>`. */
  getToken?: TokenGetter;
  /** Se envía como JSON. */
  json?: unknown;
}

/** Llama a `VITE_API_URL/api/v1<path>` y lanza `ApiError` si la respuesta no es exitosa. */
export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { getToken, json, headers: extraHeaders, ...init } = options;
  const headers = new Headers(extraHeaders);
  headers.set("Accept", "application/json");
  if (json !== undefined) headers.set("Content-Type", "application/json");

  const token = getToken ? await getToken() : null;
  if (token) headers.set("Authorization", `Bearer ${token}`);

  let response: Response;
  try {
    response = await fetch(`${env.apiUrl}/api/v1${path}`, {
      ...init,
      headers,
      body: json === undefined ? undefined : JSON.stringify(json),
    });
  } catch {
    throw new ApiError(
      0,
      "network_error",
      "No pudimos conectar con el servidor. Revisa tu conexión e intenta de nuevo.",
    );
  }

  if (!response.ok) throw await ApiError.fromResponse(response);
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}
