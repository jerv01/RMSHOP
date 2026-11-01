import { SignIn } from "@clerk/react";

export function SignInPage() {
  return (
    <div className="flex justify-center">
      <SignIn routing="path" path="/ingresar" signUpUrl="/registro" />
    </div>
  );
}
