import { SignUp } from "@clerk/react";

export function SignUpPage() {
  return (
    <div className="flex justify-center">
      <SignUp routing="path" path="/registro" signInUrl="/ingresar" />
    </div>
  );
}
