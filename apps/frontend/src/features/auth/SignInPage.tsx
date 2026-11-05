import { SignIn } from "@clerk/react";
import { Link } from "react-router";
import { BrandLogo } from "@/shared/ui/BrandLogo";

export function SignInPage() {
  return (
    <div className="mx-auto flex max-w-md flex-col items-center py-6">
      <div className="mb-6 flex flex-col items-center text-center">
        <BrandLogo size="lg" />
        <h1 className="mt-4 text-2xl font-bold tracking-tight text-foreground">Iniciar sesión</h1>
        <p className="mt-1 text-sm text-muted">
          Ingresa con tu correo y contraseña para acceder a tu cuenta.
        </p>
      </div>
      <SignIn routing="path" path="/ingresar" signUpUrl="/registro" fallbackRedirectUrl="/" />
      <p className="mt-6 text-center text-xs text-muted">
        ¿Eres administrador?{" "}
        <Link to="/admin/ingresar" className="font-semibold text-foreground underline">
          Ingresa al panel administrativo
        </Link>
      </p>
    </div>
  );
}
