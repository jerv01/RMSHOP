import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { ApiError } from "@/shared/api/client";
import { useInviteAdministrator } from "./api";
import { inviteSchema, type InviteValues } from "./schema";

export function InviteForm() {
  const invite = useInviteAdministrator();
  const [sentTo, setSentTo] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    setError,
    reset,
    formState: { errors },
  } = useForm<InviteValues>({ resolver: zodResolver(inviteSchema), defaultValues: { email: "" } });

  const onSubmit = handleSubmit(async ({ email }) => {
    setSentTo(null);
    try {
      const result = await invite.mutateAsync(email);
      setSentTo(result.email);
      reset();
    } catch (error) {
      const message =
        error instanceof ApiError
          ? error.message
          : "Ocurrió un error inesperado. Intenta de nuevo.";
      setError("email", { message });
    }
  });

  const error = errors.email?.message;

  return (
    <form onSubmit={onSubmit} noValidate className="max-w-lg">
      <label htmlFor="admin-email" className="block text-sm font-semibold text-foreground">
        Correo del nuevo administrador
      </label>
      <div className="mt-1.5 flex flex-col gap-2 sm:flex-row">
        <input
          id="admin-email"
          type="email"
          placeholder="correo@ejemplo.com"
          autoComplete="off"
          aria-invalid={error ? true : undefined}
          aria-describedby="admin-email-help admin-email-error"
          className="min-h-11 min-w-0 flex-1 rounded-[2px] border border-border-strong bg-background px-3.5 py-2 text-sm text-foreground placeholder:text-muted aria-[invalid=true]:border-accent-sale"
          {...register("email")}
        />
        <button
          type="submit"
          disabled={invite.isPending}
          className="inline-flex min-h-11 items-center justify-center rounded-[2px] bg-primary px-5 py-2 text-sm font-semibold uppercase tracking-wider text-primary-foreground transition-opacity hover:bg-foreground/90 disabled:opacity-60"
        >
          {invite.isPending ? "Enviando…" : "Agregar"}
        </button>
      </div>
      <p id="admin-email-help" className="mt-1.5 text-xs text-muted">
        Enviaremos un enlace a este correo para que cree su cuenta de administrador.
      </p>
      {/* La región en vivo existe siempre: los lectores de pantalla anuncian el cambio. */}
      <p
        id="admin-email-error"
        aria-live="polite"
        className="mt-1 min-h-5 text-sm font-medium text-accent-sale"
      >
        {error}
      </p>
      <p role="status" className="text-sm font-semibold text-accent-success">
        {sentTo ? `Invitación enviada a ${sentTo}` : ""}
      </p>
    </form>
  );
}
