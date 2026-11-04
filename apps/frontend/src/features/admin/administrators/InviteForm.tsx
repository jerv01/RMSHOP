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
    <form onSubmit={onSubmit} noValidate className="max-w-md">
      <label htmlFor="admin-email" className="block font-medium">
        Correo del nuevo administrador
      </label>
      <div className="mt-1 flex gap-2">
        <input
          id="admin-email"
          type="email"
          autoComplete="off"
          aria-invalid={error ? true : undefined}
          aria-describedby="admin-email-help admin-email-error"
          className="min-w-0 flex-1 rounded border border-gray-600 px-3 py-2"
          {...register("email")}
        />
        <button
          type="submit"
          disabled={invite.isPending}
          className="rounded bg-gray-900 px-4 py-2 text-white disabled:opacity-60"
        >
          {invite.isPending ? "Enviando…" : "Agregar"}
        </button>
      </div>
      <p id="admin-email-help" className="mt-1 text-sm text-gray-700">
        Enviaremos un enlace a este correo para que cree su cuenta de administrador.
      </p>
      {/* La región en vivo existe siempre: los lectores de pantalla anuncian el cambio. */}
      <p id="admin-email-error" aria-live="polite" className="mt-1 min-h-5 text-sm text-red-700">
        {error}
      </p>
      <p role="status" className="text-sm text-green-800">
        {sentTo ? `Invitación enviada a ${sentTo}` : ""}
      </p>
    </form>
  );
}
