import { z } from "zod";

export const inviteSchema = z.object({
  email: z.string().trim().min(1, "Ingresa el correo.").pipe(z.email("Ingresa un correo válido.")),
});

export type InviteValues = z.infer<typeof inviteSchema>;
