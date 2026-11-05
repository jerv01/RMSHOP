import { SignIn } from "@clerk/react";
import { BrandLogo } from "@/shared/ui/BrandLogo";

export function AdminSignInPage() {
  return (
    <div className="mx-auto flex max-w-md flex-col items-center py-6">
      <div className="mb-6 flex flex-col items-center text-center">
        <BrandLogo size="lg" subtitle="Acceso administrativo" />
        <h1 className="mt-4 text-2xl font-bold tracking-tight text-foreground">
          Panel de administración
        </h1>
        <p className="mt-1 text-sm text-muted">
          Exclusivo para cuentas autorizadas de administración de RM Shop.
        </p>
      </div>
      <SignIn routing="path" path="/admin/ingresar" forceRedirectUrl="/admin/productos" />
    </div>
  );
}
