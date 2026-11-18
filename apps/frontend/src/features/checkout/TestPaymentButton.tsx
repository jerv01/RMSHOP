import { useState } from "react";
import { useApi } from "@/shared/api/useApi";
import { ErrorNotice } from "@/shared/ui/Feedback";

type Order = { order_number: string; status_label: string };
type PaymentResult = {
  order: Order;
  payment: { status_label: string; redirect_url: string } | null;
};

// shortcut: dirección y datos del pagador fijos solo para probar MercadoPago (PSE);
// reemplazar por el formulario real de checkout y el Card Payment Brick.
const TEST_ADDRESS = {
  municipality: "Cali",
  address_line: "Calle 10 # 20-30",
  recipient_name: "Cliente Prueba",
  phone: "3001234567",
};
const TEST_PSE_PAYER = {
  method: "pse",
  entity_type: "individual",
  first_name: "Cliente",
  last_name: "Prueba",
  identification_type: "CC",
  identification_number: "12345678",
  phone_area_code: "57",
  phone_number: "3001234567",
  zip_code: "760001",
  street_number: "20-30",
  neighborhood: "Centro",
};

/** Botón de prueba: crea el pedido desde el carrito y lo paga con PSE en MercadoPago. */
export function TestPaymentButton() {
  const api = useApi();
  const [step, setStep] = useState<string | null>(null);
  const [error, setError] = useState<unknown>(null);

  async function pay() {
    setError(null);
    try {
      setStep("Creando pedido…");
      const order = await api<Order>("/checkout", { method: "POST", json: TEST_ADDRESS });

      setStep("Consultando bancos PSE…");
      const banks = await api<{ id: string; description: string }[]>("/payments/pse-banks");
      if (banks.length === 0) throw new Error("MercadoPago no devolvió bancos PSE.");

      setStep(`Pagando ${order.order_number} con ${banks[0].description}…`);
      const result = await api<PaymentResult>(`/orders/${order.order_number}/payments`, {
        method: "POST",
        json: { ...TEST_PSE_PAYER, financial_institution: banks[0].id },
      });
      if (result.payment?.redirect_url) {
        window.location.assign(result.payment.redirect_url);
        return;
      }
      setStep(`Pedido ${order.order_number}: ${result.order.status_label}`);
    } catch (err) {
      setStep(null);
      setError(err);
    }
  }

  return (
    <div className="space-y-2 text-right">
      <button type="button" className="btn-primary" disabled={!!step} onClick={pay}>
        Pagar con PSE (prueba)
      </button>
      {step && (
        <p role="status" className="text-sm">
          {step}
        </p>
      )}
      <ErrorNotice error={error} />
    </div>
  );
}
