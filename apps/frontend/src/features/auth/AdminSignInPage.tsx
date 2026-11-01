import { SignIn } from "@clerk/react";

export function AdminSignInPage() {
  return (
    <div className="flex justify-center">
      <SignIn routing="path" path="/admin/ingresar" forceRedirectUrl="/admin/productos" />
    </div>
  );
}
