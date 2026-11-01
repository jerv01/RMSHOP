/** Único lugar donde se leen las variables de entorno del frontend. */
export const env = {
  apiUrl: (import.meta.env.VITE_API_URL ?? "http://localhost:8000").replace(/\/+$/, ""),
  clerkPublishableKey: import.meta.env.VITE_CLERK_PUBLISHABLE_KEY ?? "",
};
