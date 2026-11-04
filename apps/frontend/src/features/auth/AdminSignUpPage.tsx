import { SignUp } from "@clerk/react";

/**
 * Destino del enlace de invitación de administrador (HU-12). Clerk lee el `__clerk_ticket` de
 * la URL, crea la cuenta con `public_metadata.role = "admin"` y, al terminar, abre el panel.
 */
export function AdminSignUpPage() {
  return (
    <div className="flex justify-center">
      <SignUp
        routing="path"
        path="/admin/registro"
        signInUrl="/admin/ingresar"
        fallbackRedirectUrl="/admin/productos"
      />
    </div>
  );
}
