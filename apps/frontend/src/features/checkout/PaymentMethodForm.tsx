import { CardPayment, initMercadoPago } from "@mercadopago/sdk-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { usePseBanks } from "@/features/orders/api";
import type { PaymentMethodCode, StartPaymentInput } from "@/features/orders/types";
import { env } from "@/shared/lib/env";
import { formatCOP } from "@/shared/lib/formatCOP";

const DEBIT_METHOD_IDS = new Set(["debvisa", "debmaster"]);

/**
 * Configuración visual y de medios de pago constante a nivel de módulo.
 * Al tener referencia inmutable, nunca provoca que CardPayment desmonte o recree el Brick.
 */
const BRICK_CUSTOMIZATION = {
  paymentMethods: {
    types: {
      included: ["debit_card" as const],
    },
    minInstallments: 1,
    maxInstallments: 1,
  },
  visual: {
    style: {
      theme: "default" as const,
      customVariables: {
        baseColor: "#000000",
        textPrimaryColor: "#000000",
        textSecondaryColor: "#767677",
        inputBackgroundColor: "#FFFFFF",
        formBackgroundColor: "#FFFFFF",
        borderRadiusSmall: "2px",
        borderRadiusMedium: "2px",
        borderRadiusLarge: "2px",
        errorColor: "#E4002B",
      },
    },
  },
};

let initializedMpKey: string | null = null;

function ensureMercadoPagoInitialized(publicKey: string) {
  const cleanKey = publicKey.trim();
  if (!cleanKey || initializedMpKey === cleanKey) return;
  initMercadoPago(cleanKey, { locale: "es-CO" });
  initializedMpKey = cleanKey;
}

/** Permite reiniciar el estado de inicialización en pruebas unitarias. */
export function resetMercadoPagoInitForTests() {
  initializedMpKey = null;
}

function splitFullName(fullName: string): { firstName: string; lastName: string } {
  const parts = fullName.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return { firstName: "Cliente", lastName: "RM" };
  if (parts.length === 1) return { firstName: parts[0], lastName: "RM" };
  return {
    firstName: parts[0],
    lastName: parts.slice(1).join(" "),
  };
}

export interface PaymentMethodFormProps {
  totalAmount: number;
  defaultHolderName?: string;
  defaultPhone?: string;
  mercadopagoPublicKey?: string;
  busy: boolean;
  submitLabel?: string;
  onSubmit: (payload: StartPaymentInput) => void | Promise<void>;
}

export function PaymentMethodForm({
  totalAmount,
  defaultHolderName = "",
  defaultPhone = "",
  mercadopagoPublicKey = env.mercadopagoPublicKey,
  busy,
  submitLabel,
  onSubmit,
}: PaymentMethodFormProps) {
  const [method, setMethod] = useState<PaymentMethodCode>("debit_card");

  // Campos de PSE (HU-20)
  const [pseBankId, setPseBankId] = useState<string>("");
  const [entityType, setEntityType] = useState<"individual" | "association">("individual");
  const [docType, setDocType] = useState<string>("CC");
  const [docNumber, setDocNumber] = useState<string>("");
  const [pseFirstName, setPseFirstName] = useState<string>("");
  const [pseLastName, setPseLastName] = useState<string>("");
  const [pseAreaCode, setPseAreaCode] = useState<string>("57");
  const [psePhone, setPsePhone] = useState<string>("");
  const [zipCode, setZipCode] = useState<string>("760001");
  const [streetNumber, setStreetNumber] = useState<string>("10-20");
  const [neighborhood, setNeighborhood] = useState<string>("Centro");

  const [validationError, setValidationError] = useState<string | null>(null);

  const activePublicKey = mercadopagoPublicKey.trim();
  // Inicializamos el SDK de MercadoPago de forma síncrona una única vez (singleton) antes de que
  // el efecto del hijo <CardPayment /> solicite MercadoPagoInstance.getInstance().
  if (activePublicKey) {
    ensureMercadoPagoInitialized(activePublicKey);
  }

  // Referencias mutables para que los callbacks del Brick sean 100 % estables ([]),
  // evitando que escribir la dirección o el nombre en CheckoutPage desmonte y recree el Brick.
  const busyRef = useRef(busy);
  const onSubmitRef = useRef(onSubmit);
  const defaultHolderNameRef = useRef(defaultHolderName);
  const brickReadyRef = useRef(false);

  useEffect(() => {
    busyRef.current = busy;
    onSubmitRef.current = onSubmit;
    defaultHolderNameRef.current = defaultHolderName;
  }, [busy, onSubmit, defaultHolderName]);

  const normalizedAmount = Math.max(1, Math.round(totalAmount));

  // El objeto initialization se crea una sola vez al montar el formulario para no disparar
  // el useEffect interno de @mercadopago/sdk-react; si cambia el monto (p. ej. al cambiar
  // de municipio), actualizamos el Brick en vivo con controller.update({ amount }).
  const [brickInitialization] = useState(() => ({
    amount: normalizedAmount,
  }));

  useEffect(() => {
    if (!brickReadyRef.current) return;
    const win = window as unknown as {
      cardPaymentBrickController?: { update?: (values: { amount: number }) => void };
    };
    win.cardPaymentBrickController?.update?.({ amount: normalizedAmount });
  }, [normalizedAmount]);

  const defaultSplit = splitFullName(defaultHolderName);
  const effectivePseFirstName = pseFirstName || defaultSplit.firstName;
  const effectivePseLastName = pseLastName || defaultSplit.lastName;
  const effectivePsePhone = psePhone || defaultPhone.replace(/\D/g, "").slice(-10);

  const pseBanksQuery = usePseBanks(method === "pse");
  const banks = pseBanksQuery.data ?? [];
  const selectedBankId = pseBankId || (banks[0]?.id ?? "");

  const handleBrickReady = useCallback(() => {
    brickReadyRef.current = true;
  }, []);

  const handleBrickError = useCallback(() => {
    setValidationError(
      "No se pudo cargar o procesar el formulario de MercadoPago. Revisa los datos de tu tarjeta débito e intenta de nuevo.",
    );
  }, []);

  const handleBrickSubmit = useCallback(
    async (
      formData: {
        token?: string;
        payment_method_id?: string;
        payer?: {
          email?: string;
          first_name?: string;
          last_name?: string;
          identification?: { type?: string; number?: string };
        };
      },
      additionalData?: unknown,
    ) => {
      if (busyRef.current) return;
      setValidationError(null);

      const token = String(formData?.token ?? "").trim();
      const paymentMethodId = String(formData?.payment_method_id ?? "")
        .trim()
        .toLowerCase();

      if (!token || !paymentMethodId) {
        setValidationError(
          "No pudimos tokenizar los datos de la tarjeta en MercadoPago. Revisa los campos e intenta de nuevo.",
        );
        return;
      }

      const extra =
        typeof additionalData === "object" && additionalData !== null
          ? (additionalData as Record<string, unknown>)
          : {};
      const rawForm = formData as unknown as Record<string, unknown>;

      const explicitPaymentType =
        (typeof extra.paymentTypeId === "string" && extra.paymentTypeId) ||
        (typeof rawForm.payment_type_id === "string" && rawForm.payment_type_id) ||
        (typeof rawForm.payment_type === "string" && rawForm.payment_type) ||
        "";

      const paymentType =
        explicitPaymentType ||
        (DEBIT_METHOD_IDS.has(paymentMethodId) ? "debit_card" : "credit_card");

      const cardholderName =
        (typeof extra.cardholderName === "string" && extra.cardholderName.trim()) ||
        defaultHolderNameRef.current;
      const holderSplit = splitFullName(cardholderName);

      const firstName = formData.payer?.first_name?.trim() || holderSplit.firstName;
      const lastName = formData.payer?.last_name?.trim() || holderSplit.lastName;
      const identificationType = formData.payer?.identification?.type?.trim() || "CC";
      const identificationNumber = formData.payer?.identification?.number?.trim() || undefined;

      await onSubmitRef.current({
        method: "debit_card",
        token,
        payment_method_id: paymentMethodId,
        payment_type: paymentType,
        first_name: firstName,
        last_name: lastName,
        identification_type: identificationNumber ? identificationType : undefined,
        identification_number: identificationNumber,
      });
    },
    [],
  );

  async function handlePseSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    setValidationError(null);

    if (!selectedBankId) {
      setValidationError("Selecciona tu entidad bancaria para continuar con PSE.");
      return;
    }
    if (!effectivePseFirstName.trim() || !effectivePseLastName.trim()) {
      setValidationError("Ingresa el nombre y apellido del titular de la cuenta bancaria.");
      return;
    }
    if (!docNumber.trim() || !/^\d{5,20}$/.test(docNumber.trim())) {
      setValidationError("Ingresa un número de documento válido (solo números).");
      return;
    }
    const cleanPsePhone = effectivePsePhone.replace(/[^\d -]/g, "").trim();
    if (cleanPsePhone.replace(/\D/g, "").length < 7) {
      setValidationError("Ingresa un teléfono celular válido para PSE.");
      return;
    }
    if (!/^\d{4,10}$/.test(zipCode.trim())) {
      setValidationError("Ingresa un código postal válido (por ejemplo 760001).");
      return;
    }
    if (!streetNumber.trim() || !neighborhood.trim()) {
      setValidationError("Completa la nomenclatura y el barrio del pagador para PSE.");
      return;
    }

    await onSubmit({
      method: "pse",
      financial_institution: selectedBankId,
      entity_type: entityType,
      first_name: effectivePseFirstName.trim(),
      last_name: effectivePseLastName.trim(),
      identification_type: docType,
      identification_number: docNumber.trim(),
      phone_area_code: pseAreaCode.trim() || "57",
      phone_number: cleanPsePhone,
      zip_code: zipCode.trim(),
      street_number: streetNumber.trim(),
      neighborhood: neighborhood.trim(),
    });
  }

  return (
    <div className="space-y-6">
      <div className="space-y-3">
        <span className="block text-sm font-semibold uppercase tracking-wider">
          Selecciona tu medio de pago
        </span>
        <div
          role="radiogroup"
          aria-label="Medio de pago"
          className="grid grid-cols-1 gap-3 sm:grid-cols-2"
        >
          <button
            type="button"
            role="radio"
            aria-checked={method === "debit_card"}
            disabled={busy}
            onClick={() => {
              setMethod("debit_card");
              setValidationError(null);
            }}
            className={`flex min-h-11 flex-col items-start justify-center rounded-[2px] border p-4 text-left transition-colors ${
              method === "debit_card"
                ? "border-primary bg-primary text-primary-foreground"
                : "border-border bg-background text-foreground hover:bg-surface-alt"
            }`}
          >
            <span className="text-sm font-bold">Tarjeta débito</span>
            <span
              className={`text-xs ${
                method === "debit_card" ? "text-primary-foreground/80" : "text-muted"
              }`}
            >
              Visa o Mastercard débito (sin redirección)
            </span>
          </button>

          <button
            type="button"
            role="radio"
            aria-checked={method === "pse"}
            disabled={busy}
            onClick={() => {
              setMethod("pse");
              setValidationError(null);
            }}
            className={`flex min-h-11 flex-col items-start justify-center rounded-[2px] border p-4 text-left transition-colors ${
              method === "pse"
                ? "border-primary bg-primary text-primary-foreground"
                : "border-border bg-background text-foreground hover:bg-surface-alt"
            }`}
          >
            <span className="text-sm font-bold">PSE (Banca en línea / Nequi)</span>
            <span
              className={`text-xs ${
                method === "pse" ? "text-primary-foreground/80" : "text-muted"
              }`}
            >
              Transferencia desde tu banco o billetera
            </span>
          </button>
        </div>
      </div>

      {validationError && (
        <div role="alert" className="notice notice-error">
          {validationError}
        </div>
      )}

      {/* Mantenemos el contenedor del Brick montado y solo alternamos su visibilidad
          para no destruir ni reinicializar el iframe de MercadoPago al cambiar de pestaña. */}
      <div
        hidden={method !== "debit_card"}
        className={
          method === "debit_card"
            ? "space-y-4 rounded-[2px] border border-border p-4 sm:p-5"
            : "hidden"
        }
      >
        <div className="space-y-1">
          <h3 className="text-sm font-semibold">Pago con tarjeta débito (MercadoPago)</h3>
          <p className="text-xs text-muted">
            Solo aceptamos tarjetas débito Visa o Mastercard (1 cuota, sin crédito). Tus datos se
            tokenizan directamente en el Card Payment Brick de MercadoPago y nunca se almacenan en
            RM Shop.
          </p>
        </div>

        {!activePublicKey ? (
          <div role="alert" className="notice notice-warning space-y-1">
            <p className="font-semibold">
              Falta configurar la clave pública de MercadoPago en el frontend
            </p>
            <p className="text-xs">
              Agrega{" "}
              <code className="rounded-[2px] bg-surface px-1 py-0.5 font-mono">
                VITE_MERCADOPAGO_PUBLIC_KEY
              </code>{" "}
              en{" "}
              <code className="rounded-[2px] bg-surface px-1 py-0.5 font-mono">
                apps/frontend/.env
              </code>{" "}
              y recrea el contenedor con{" "}
              <code className="rounded-[2px] bg-surface px-1 py-0.5 font-mono">
                docker compose up -d
              </code>{" "}
              para cargar el formulario oficial de tarjeta débito, o selecciona PSE.
            </p>
          </div>
        ) : (
          <div aria-busy={busy} className={busy ? "pointer-events-none opacity-60" : ""}>
            <CardPayment
              initialization={brickInitialization}
              customization={BRICK_CUSTOMIZATION}
              onReady={handleBrickReady}
              onSubmit={handleBrickSubmit}
              onError={handleBrickError}
            />
          </div>
        )}

        <div className="flex items-center justify-between border-t border-border pt-3">
          <p className="text-sm text-muted">
            Total a pagar:{" "}
            <strong className="text-base font-bold text-foreground">
              {formatCOP(totalAmount)}
            </strong>
          </p>
          {busy && (
            <span role="status" className="text-xs font-semibold">
              Procesando pago…
            </span>
          )}
        </div>
      </div>

      {method === "pse" && (
        <form onSubmit={(e) => void handlePseSubmit(e)} className="space-y-6" noValidate>
          <fieldset
            disabled={busy}
            className="space-y-4 rounded-[2px] border border-border p-4 sm:p-5"
          >
            <legend className="px-2 text-sm font-semibold">
              Pago por PSE (Banca en línea / Nequi)
            </legend>
            <p className="text-xs text-muted">
              Serás redirigido al portal seguro de tu entidad financiera para autorizar el débito.
              No almacenamos tus datos bancarios.
            </p>

            {pseBanksQuery.isPending && (
              <p role="status" className="text-sm text-muted">
                Cargando bancos habilitados en PSE…
              </p>
            )}

            {pseBanksQuery.error && (
              <div role="alert" className="notice notice-error space-y-2">
                <p>No pudimos cargar la lista de bancos de PSE en este momento.</p>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => void pseBanksQuery.refetch()}
                >
                  Reintentar carga de bancos
                </button>
              </div>
            )}

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <label className="field sm:col-span-2">
                <span>Banco o billetera digital (PSE)</span>
                <select
                  aria-label="Banco o billetera digital (PSE)"
                  value={selectedBankId}
                  onChange={(e) => setPseBankId(e.target.value)}
                >
                  {banks.length === 0 ? (
                    <option value="">Selecciona un banco</option>
                  ) : (
                    banks.map((bank) => (
                      <option key={bank.id} value={bank.id}>
                        {bank.description}
                      </option>
                    ))
                  )}
                </select>
              </label>

              <label className="field">
                <span>Tipo de persona</span>
                <select
                  aria-label="Tipo de persona"
                  value={entityType}
                  onChange={(e) => setEntityType(e.target.value as "individual" | "association")}
                >
                  <option value="individual">Persona natural</option>
                  <option value="association">Persona jurídica</option>
                </select>
              </label>

              <label className="field">
                <span>Tipo de documento</span>
                <select
                  aria-label="Tipo de documento"
                  value={docType}
                  onChange={(e) => setDocType(e.target.value)}
                >
                  <option value="CC">Cédula de ciudadanía (CC)</option>
                  <option value="CE">Cédula de extranjería (CE)</option>
                  <option value="NIT">NIT</option>
                  <option value="PP">Pasaporte (PP)</option>
                </select>
              </label>

              <label className="field">
                <span>Nombre del titular</span>
                <input
                  type="text"
                  placeholder="Ana"
                  value={effectivePseFirstName}
                  onChange={(e) => setPseFirstName(e.target.value)}
                />
              </label>

              <label className="field">
                <span>Apellido del titular</span>
                <input
                  type="text"
                  placeholder="Pérez"
                  value={effectivePseLastName}
                  onChange={(e) => setPseLastName(e.target.value)}
                />
              </label>

              <label className="field">
                <span>Número de documento</span>
                <input
                  type="text"
                  inputMode="numeric"
                  placeholder="12345678"
                  value={docNumber}
                  onChange={(e) => setDocNumber(e.target.value)}
                />
              </label>

              <div className="grid grid-cols-3 gap-2">
                <label className="field">
                  <span>Indicativo</span>
                  <input
                    type="text"
                    inputMode="numeric"
                    value={pseAreaCode}
                    onChange={(e) => setPseAreaCode(e.target.value)}
                  />
                </label>
                <label className="field col-span-2">
                  <span>Teléfono celular</span>
                  <input
                    type="text"
                    inputMode="numeric"
                    placeholder="3001234567"
                    value={effectivePsePhone}
                    onChange={(e) => setPsePhone(e.target.value)}
                  />
                </label>
              </div>

              <label className="field">
                <span>Código postal</span>
                <input
                  type="text"
                  inputMode="numeric"
                  placeholder="760001"
                  value={zipCode}
                  onChange={(e) => setZipCode(e.target.value)}
                />
              </label>

              <label className="field">
                <span>Nomenclatura / número</span>
                <input
                  type="text"
                  placeholder="20-30"
                  value={streetNumber}
                  onChange={(e) => setStreetNumber(e.target.value)}
                />
              </label>

              <label className="field sm:col-span-2">
                <span>Barrio</span>
                <input
                  type="text"
                  placeholder="Centro"
                  value={neighborhood}
                  onChange={(e) => setNeighborhood(e.target.value)}
                />
              </label>
            </div>
          </fieldset>

          <div className="flex flex-col items-stretch justify-between gap-3 border-t border-border pt-4 sm:flex-row sm:items-center">
            <p className="text-sm text-muted">
              Total a pagar:{" "}
              <strong className="text-base font-bold text-foreground">
                {formatCOP(totalAmount)}
              </strong>
            </p>

            <button
              type="submit"
              className="btn-primary min-h-11 px-6"
              disabled={busy || pseBanksQuery.isPending}
            >
              {busy ? "Procesando pago…" : (submitLabel ?? "Continuar al banco por PSE")}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
