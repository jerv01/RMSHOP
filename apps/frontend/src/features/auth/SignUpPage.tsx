import { SignUp } from "@clerk/react";

export function SignUpPage() {
  return (
    <div className="flex justify-center">
      {/* Clerk pide el código del correo antes de abrir la sesión (HU-7/HU-8). Al verificarlo,
          el cliente vuelve a donde estaba (`redirect_url`) o, si no hay, al inicio. */}
      <SignUp routing="path" path="/registro" signInUrl="/ingresar" fallbackRedirectUrl="/" />
    </div>
  );
}
