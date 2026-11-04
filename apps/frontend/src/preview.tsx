/** Solo desarrollo: muestra la pantalla de administradores con una API simulada (sin sesión). */
import { ClerkProvider } from "@clerk/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { MemoryRouter } from "react-router";
import { AdministratorsPage } from "@/features/admin/administrators/AdministratorsPage";
import { env } from "@/shared/lib/env";
import "./index.css";

let admins = [
  {
    clerk_user_id: "u1",
    email: "libia@rmshop.test",
    first_name: "Libia",
    last_name: "Palacios",
    is_me: true,
  },
  {
    clerk_user_id: "u2",
    email: "ana@rmshop.test",
    first_name: "Ana",
    last_name: "Pérez",
    is_me: false,
  },
];

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

window.fetch = async (_url, init) => {
  const method = init?.method ?? "GET";
  if (method === "POST") {
    const { email } = JSON.parse(String(init?.body)) as { email: string };
    if (email.includes("cliente"))
      return json(
        {
          code: "email_belongs_to_customer",
          message: "Este correo pertenece a una cuenta de cliente.",
          fields: {},
        },
        409,
      );
    return json({ status: "invited", email }, 201);
  }
  if (method === "DELETE") {
    const id = String(_url).split("/").pop();
    admins = admins.filter((a) => a.clerk_user_id !== id);
    return new Response(null, { status: 204 });
  }
  return json(admins);
};

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ClerkProvider publishableKey={env.clerkPublishableKey}>
      <QueryClientProvider client={new QueryClient()}>
        <MemoryRouter>
          <header className="border-b border-gray-200 p-4 text-lg font-semibold">
            RM Shop · Panel de administración (vista previa)
          </header>
          <main className="p-4">
            <AdministratorsPage />
          </main>
        </MemoryRouter>
      </QueryClientProvider>
    </ClerkProvider>
  </StrictMode>,
);
