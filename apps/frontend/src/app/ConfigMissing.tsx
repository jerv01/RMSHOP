/** Se muestra en lugar de la app cuando falta la clave publicable de Clerk. */
export function ConfigMissing() {
  return (
    <main className="mx-auto max-w-xl p-8">
      <h1 className="text-2xl font-bold">Falta configurar Clerk</h1>
      <p className="mt-4">
        La aplicación necesita la variable <code>VITE_CLERK_PUBLISHABLE_KEY</code> en{" "}
        <code>apps/frontend/.env</code>.
      </p>
      <p className="mt-2">
        Copia la clave publicable desde el panel de Clerk, guarda el archivo y reinicia el servicio
        con <code>docker compose restart frontend</code>.
      </p>
      <p className="mt-2">
        Los pasos completos están en <code>docs/clerk-setup.md</code>.
      </p>
    </main>
  );
}
