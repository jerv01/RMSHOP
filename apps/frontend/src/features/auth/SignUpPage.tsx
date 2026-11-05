import { SignUp } from "@clerk/react";
import { Link } from "react-router";
import { BrandLogo } from "@/shared/ui/BrandLogo";

export function SignUpPage() {
  return (
    <div className="mx-auto flex max-w-md flex-col items-center py-6">
      <div className="mb-6 flex flex-col items-center text-center">
        <BrandLogo size="lg" />
        <h1 className="mt-4 text-2xl font-bold tracking-tight text-foreground">Crear cuenta</h1>
        <p className="mt-1 text-sm text-muted">
          Regístrate para comprar, guardar tu carrito y recibir atención en el Valle del Cauca.
        </p>
      </div>
      {/* Clerk pide el código del correo antes de abrir la sesión (HU-7/HU-8). Al verificarlo,
          el cliente vuelve a donde estaba (`redirect_url`) o, si no hay, al inicio. */}
      <SignUp routing="path" path="/registro" signInUrl="/ingresar" fallbackRedirectUrl="/" />
      <p className="mt-6 max-w-sm text-center text-xs text-muted">
        Al crear una cuenta aceptas nuestra{" "}
        <Link to="/datos-personales" className="font-semibold text-foreground underline">
          Política de Tratamiento de Datos Personales
        </Link>
        .
      </p>
    </div>
  );
}
