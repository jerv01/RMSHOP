import { Link } from "react-router";

export function DataPolicyPage() {
  return (
    <article className="mx-auto max-w-3xl rounded-[2px] border border-border bg-background p-6 shadow-(--shadow-soft)">
      <h1 className="text-2xl font-bold text-foreground">
        Política de Tratamiento de Datos Personales
      </h1>
      <p className="mt-2 text-sm text-muted">
        RM Shop · Cumplimiento de la Ley 1581 de 2012 (Colombia)
      </p>
      <div className="mt-4 space-y-3 text-sm leading-relaxed text-foreground">
        <p>
          RM Shop recolecta y trata tus datos personales (nombre, correo electrónico, teléfono y
          dirección de entrega en Cali, Palmira, Jamundí y Yumbo) únicamente para gestionar tu
          cuenta, procesar tus pedidos, coordinar envíos y enviarte notificaciones transaccionales.
        </p>
        <p>
          Como titular de los datos tienes derecho a conocer, actualizar, rectificar y solicitar la
          supresión de tu información personal en cualquier momento a través de nuestros canales de
          atención.
        </p>
      </div>
      <div className="mt-6">
        <Link
          to="/registro"
          className="inline-flex min-h-11 items-center justify-center rounded-[2px] border border-border-strong bg-background px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-surface-alt"
        >
          Volver al registro
        </Link>
      </div>
    </article>
  );
}
