import { SignUp } from "@clerk/react";
import { BrandLogo } from "@/shared/ui/BrandLogo";

/**
 * Destino del enlace de invitación de administrador (HU-12). Clerk lee el `__clerk_ticket` de
 * la URL, crea la cuenta con `public_metadata.role = "admin"` y, al terminar, abre el panel.
 */
export function AdminSignUpPage() {
  return (
    <div className="mx-auto flex max-w-md flex-col items-center py-6">
      <div className="mb-6 flex flex-col items-center text-center">
        <BrandLogo size="lg" subtitle="Invitación administrativa" />
        <h1 className="mt-4 text-2xl font-bold tracking-tight text-foreground">
          Activar cuenta de administrador
        </h1>
        <p className="mt-1 text-sm text-muted">
          Completa tu registro con el enlace de invitación para acceder al panel.
        </p>
      </div>
      <SignUp
        routing="path"
        path="/admin/registro"
        signInUrl="/admin/ingresar"
        fallbackRedirectUrl="/admin/productos"
      />
    </div>
  );
}
