import { esES } from "@clerk/localizations";
import { describe, expect, it } from "vitest";
import { localization } from "./localization";

describe("localization", () => {
  it("usa el mensaje del criterio AC-HU-7-2 para el correo duplicado", () => {
    expect(localization.unstable__errors?.form_identifier_exists__email_address).toBe(
      "Este correo ya está registrado.",
    );
  });

  it("conserva el resto de textos de esES", () => {
    expect(localization.unstable__errors?.form_param_nil).toBe(
      esES.unstable__errors?.form_param_nil,
    );
    expect(localization.signUp?.emailCode?.title).toBe(esES.signUp?.emailCode?.title);
  });
});
