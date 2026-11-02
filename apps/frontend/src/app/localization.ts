import { esES } from "@clerk/localizations";

/**
 * Textos de Clerk en español, con los mensajes que exigen los criterios de aceptación.
 *
 * AC-HU-7-2: el correo duplicado debe decir "Este correo ya está registrado" (el texto de
 * `esES` es "Ya existe una cuenta con esta dirección de correo electrónico.").
 */
export const localization: typeof esES = {
  ...esES,
  unstable__errors: {
    ...esES.unstable__errors,
    form_identifier_exists__email_address: "Este correo ya está registrado.",
  },
};
