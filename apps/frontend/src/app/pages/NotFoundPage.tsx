import { Link } from "react-router";

export function NotFoundPage() {
  return (
    <>
      <h1 className="text-2xl font-bold">Página no encontrada</h1>
      <p className="mt-2">La dirección que buscas no existe.</p>
      <Link to="/" className="mt-4 inline-block underline">
        Volver al inicio
      </Link>
    </>
  );
}
