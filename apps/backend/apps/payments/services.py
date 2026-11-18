"""Pagos de pedidos con MercadoPago (HU-19 tarjeta débito, HU-20 PSE, HU-21 pendiente de pago)."""

import logging
import math
from dataclasses import dataclass

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound

from apps.core.exceptions import ApiError
from apps.orders.models import Order, OrderStatus
from apps.orders.services import approve_order_payment, reject_order_payment
from apps.payments.exceptions import (
    OrderNotPayable,
    PaymentAlreadyInProgress,
    PaymentGatewayUnavailable,
    PaymentRequestRejected,
)
from apps.payments.gateways.mercadopago import MercadoPagoGateway
from apps.payments.models import (
    ACTIVE_PAYMENT_STATUSES,
    Payment,
    PaymentMethod,
    PaymentStatus,
)
from apps.users.models import User

logger = logging.getLogger(__name__)

# Solo tarjetas débito (AC-HU-19-2). Ids de MercadoPago Colombia.
DEBIT_PAYMENT_METHOD_IDS = {"debvisa", "debmaster"}
ONLY_DEBIT_MESSAGE = (
    "Solo se aceptan tarjetas débito. Intenta con una tarjeta débito Visa o Mastercard."
)

# Código ISO de Valle del Cauca, donde están los municipios con envío.
_STATE_ID = "CO-VAC"
_STATE_NAME = "Valle del Cauca"
_PSE_BANKS_CACHE_KEY = "payments:pse_banks"
_PSE_BANKS_CACHE_SECONDS = 60 * 60
# Llaves que nunca se guardan de una respuesta de MercadoPago.
_SENSITIVE_KEYS = {"token", "client_token"}


def get_gateway() -> MercadoPagoGateway:
    """Punto único para obtener el adaptador; los tests lo reemplazan o simulan su HTTP."""
    return MercadoPagoGateway()


# ---------------------------------------------------------------------------
# Mapeo de estados MercadoPago -> pedido
# ---------------------------------------------------------------------------

OUTCOME_APPROVED = "approved"
OUTCOME_REJECTED = "rejected"
OUTCOME_PENDING = "pending"


@dataclass(frozen=True)
class MpStatus:
    payment_status: str
    outcome: str


def map_mp_status(mp_order: dict) -> MpStatus:
    """Traduce el estado de una orden de MercadoPago al estado del pago y al efecto en el pedido.

    - processed -> pago aprobado, pedido «Pago aprobado».
    - failed / canceled / expired -> pago rechazado, pedido «Pago rechazado» y luego «Cancelado».
    - action_required -> el cliente debe actuar (PSE en el banco, 3DS); pedido sigue pendiente.
    - created / processing / cualquier otro -> en proceso; pedido sigue «Pendiente de Pago».
    """
    mp_status = (mp_order.get("status") or "").lower()
    if mp_status == "processed":
        return MpStatus(PaymentStatus.APPROVED, OUTCOME_APPROVED)
    if mp_status in {"failed", "canceled", "cancelled", "expired"}:
        return MpStatus(PaymentStatus.REJECTED, OUTCOME_REJECTED)
    if mp_status == "action_required":
        return MpStatus(PaymentStatus.ACTION_REQUIRED, OUTCOME_PENDING)
    return MpStatus(PaymentStatus.PROCESSING, OUTCOME_PENDING)


def sanitize_mp_response(value):
    """Copia la respuesta sin tokens ni secretos, para guardarla como referencia."""
    if isinstance(value, dict):
        return {k: sanitize_mp_response(v) for k, v in value.items() if k not in _SENSITIVE_KEYS}
    if isinstance(value, list):
        return [sanitize_mp_response(item) for item in value]
    return value


def _first_mp_payment(mp_order: dict) -> dict:
    payments = (mp_order.get("transactions") or {}).get("payments") or []
    return payments[0] if payments and isinstance(payments[0], dict) else {}


@transaction.atomic
def apply_mp_order(*, payment: Payment, mp_order: dict) -> Payment:
    """Aplica una respuesta de MercadoPago al pago y al pedido.

    Idempotente: se puede llamar varias veces con la misma orden (sync repetido, y más adelante
    el webhook de HU-22) sin duplicar transiciones ni devoluciones de stock, porque los
    servicios de pedidos solo actúan si el pedido sigue en el estado esperado.
    """
    payment = Payment.objects.select_for_update(of=("self",)).get(pk=payment.pk)
    mp_payment = _first_mp_payment(mp_order)
    mapped = map_mp_status(mp_order)

    payment.status = mapped.payment_status
    payment.status_detail = str(
        mp_payment.get("status_detail") or mp_order.get("status_detail") or ""
    )[:60]
    if mp_order.get("id"):
        payment.mp_order_id = str(mp_order["id"])
    if mp_payment.get("id"):
        payment.mp_payment_id = str(mp_payment["id"])
    redirect_url = (mp_payment.get("payment_method") or {}).get("redirect_url")
    if redirect_url:
        payment.redirect_url = redirect_url
    payment.raw_response = sanitize_mp_response(mp_order)
    payment.save()

    order = payment.order
    note = f"MercadoPago: {mp_order.get('status', '')}/{payment.status_detail}".strip("/")
    if mapped.outcome == OUTCOME_APPROVED:
        try:
            approve_order_payment(order=order, note=note)
        except ApiError:
            # Aprobación de un pedido que ya no está pendiente (p. ej. cancelado por tiempo).
            # No se reactiva; queda registrado para revisión del administrador (HU-22/HU-24).
            logger.warning(
                "Pago aprobado para el pedido %s en estado %s; requiere revisión manual.",
                order.order_number,
                order.status,
            )
    elif mapped.outcome == OUTCOME_REJECTED:
        reject_order_payment(order=order, note=note)
    return payment


# ---------------------------------------------------------------------------
# Inicio del pago
# ---------------------------------------------------------------------------


def _validate_debit_card(data: dict) -> None:
    """Rechaza tarjetas de crédito o no aceptadas antes de llamar a MercadoPago (AC-HU-19-2)."""
    if (
        data.get("payment_method_id") not in DEBIT_PAYMENT_METHOD_IDS
        or data.get("payment_type", "debit_card") != "debit_card"
    ):
        raise ApiError(
            detail=ONLY_DEBIT_MESSAGE,
            code="only_debit_allowed",
            fields={"payment_method_id": [ONLY_DEBIT_MESSAGE]},
        )


def _minutes_left(order: Order) -> int:
    return max(1, math.ceil((order.payment_expires_at - timezone.now()).total_seconds() / 60))


def build_mp_order_payload(
    *, order: Order, method: str, data: dict, payer_email: str, ip_address: str | None
) -> dict:
    """Arma el cuerpo de POST /v1/orders para el pedido (montos en COP sin decimales)."""
    amount = str(int(order.total))
    user = order.user
    payer = {"email": payer_email}
    for key, fallback in (("first_name", user.first_name), ("last_name", user.last_name)):
        if value := (data.get(key) or fallback or "").strip():
            payer[key] = value
    if data.get("identification_type") and data.get("identification_number"):
        payer["identification"] = {
            "type": data["identification_type"],
            "number": data["identification_number"],
        }

    if method == PaymentMethod.DEBIT_CARD:
        payment_method = {
            "id": data["payment_method_id"],
            "type": "debit_card",
            "token": data["token"],
            "installments": 1,
        }
        mp_payment = {"amount": amount, "payment_method": payment_method}
    else:
        payment_method = {
            "id": "pse",
            "type": "bank_transfer",
            "financial_institution": data["financial_institution"],
        }
        mp_payment = {
            "amount": amount,
            "payment_method": payment_method,
            "expiration_time": f"PT{_minutes_left(order)}M",
        }
        address = {
            "zip_code": data["zip_code"],
            "street_name": order.address_line,
            "street_number": data["street_number"],
            "city": order.municipality,
            "state": _STATE_NAME,
        }
        payer.update(
            {
                "entity_type": data["entity_type"],
                "phone": {"area_code": data["phone_area_code"], "number": data["phone_number"]},
                "address": {**address, "neighborhood": data["neighborhood"]},
            }
        )

    payload = {
        "type": "online",
        "processing_mode": "automatic",
        "external_reference": order.order_number,
        "total_amount": amount,
        "description": f"Pedido {order.order_number} RM Shop",
        "payer": payer,
        "transactions": {"payments": [mp_payment]},
        "items": [
            {
                "title": item.product_name[:150],
                "unit_price": str(int(item.unit_price)),
                "quantity": item.quantity,
                "description": f"{item.color} / {item.size}"[:100],
            }
            for item in order.items.all()
        ],
        "config": {"location": {"state_id": _STATE_ID}},
    }
    if method == PaymentMethod.PSE:
        payload["shipment"] = {"address": address}
        payload["config"]["online"] = {
            "callback_url": f"{settings.FRONTEND_BASE_URL.rstrip('/')}/pedidos/{order.order_number}"
        }
        if ip_address:
            payload["additional_info"] = {"payer": {"ip_address": ip_address}}
    return payload


def _get_customer_order_for_update(*, user: User, order_number: str) -> Order:
    order = (
        Order.objects.select_for_update(of=("self",))
        .filter(user=user, order_number=order_number)
        .first()
    )
    if order is None:
        raise NotFound()
    return order


@transaction.atomic
def _register_payment_attempt(*, user: User, order_number: str, method: str) -> Payment:
    """Valida que el pedido se pueda pagar y registra el intento, con el pedido bloqueado.

    El bloqueo y la restricción única de pago activo garantizan que dos clics o dos pestañas
    no generen dos cobros (AC-HU-21-3).
    """
    order = _get_customer_order_for_update(user=user, order_number=order_number)
    if order.status != OrderStatus.PENDING_PAYMENT:
        raise OrderNotPayable(
            detail=f"El pedido {order.order_number} está «{order.get_status_display()}» y "
            "ya no se puede pagar."
        )
    if order.payment_expires_at <= timezone.now():
        raise OrderNotPayable(
            detail="El tiempo para pagar este pedido terminó. Vuelve a hacer tu pedido.",
            code="payment_window_expired",
        )

    active = order.payments.filter(status__in=ACTIVE_PAYMENT_STATUSES).first()
    if active:
        fields = {"payment_status": active.status}
        if active.redirect_url:
            fields["redirect_url"] = active.redirect_url
        raise PaymentAlreadyInProgress(fields=fields)

    return Payment.objects.create(
        order=order, method=method, amount=order.total, status=PaymentStatus.INITIATED
    )


def _mark_payment_error(payment: Payment, reason: str) -> None:
    Payment.objects.filter(pk=payment.pk, status=PaymentStatus.INITIATED).update(
        status=PaymentStatus.ERROR, status_detail=reason[:60], updated_at=timezone.now()
    )


def start_payment(
    *,
    user: User,
    order_number: str,
    method: str,
    data: dict,
    payer_email: str,
    ip_address: str | None = None,
) -> Payment:
    """Inicia el pago de un pedido «Pendiente de Pago» en MercadoPago (HU-19, HU-20, HU-21).

    Reglas de negocio:
    - Tarjeta: solo débito (debvisa/debmaster); el token lo genera el Card Payment Brick en el
      navegador, así que los datos de la tarjeta nunca llegan al backend.
    - Se registra el intento antes de llamar a MercadoPago, fuera del bloqueo del pedido, y se
      envía su idempotency_key como X-Idempotency-Key.
    - Si MercadoPago no responde o falla, el intento queda en `error`, el pedido sigue
      «Pendiente de Pago» y se puede reintentar (AC-HU-21-2).
    - La respuesta se aplica con apply_mp_order: aprobado, rechazado (cancela y devuelve stock)
      o pendiente (PSE devuelve la URL del banco).
    """
    if method == PaymentMethod.DEBIT_CARD:
        _validate_debit_card(data)

    payment = _register_payment_attempt(user=user, order_number=order_number, method=method)
    payload = build_mp_order_payload(
        order=payment.order,
        method=method,
        data=data,
        payer_email=payer_email,
        ip_address=ip_address,
    )
    try:
        mp_order = get_gateway().create_order(
            payload=payload, idempotency_key=str(payment.idempotency_key)
        )
    except PaymentGatewayUnavailable:
        _mark_payment_error(payment, "gateway_unavailable")
        raise
    except PaymentRequestRejected:
        _mark_payment_error(payment, "request_rejected")
        raise
    except Exception:
        _mark_payment_error(payment, "unexpected_error")
        raise

    return apply_mp_order(payment=payment, mp_order=mp_order)


def sync_payment(*, user: User, order_number: str) -> Order:
    """Consulta en MercadoPago el último pago del pedido y aplica su estado (vuelta de PSE).

    Idempotente: si el pedido ya no está pendiente no consulta nada; así repetir la llamada
    nunca devuelve el stock dos veces.
    """
    order = Order.objects.filter(user=user, order_number=order_number).first()
    if order is None:
        raise NotFound()
    if order.status != OrderStatus.PENDING_PAYMENT:
        return order

    payment = order.payments.exclude(mp_order_id__isnull=True).first()
    if payment is None:
        return order

    mp_order = get_gateway().get_order(mp_order_id=payment.mp_order_id)
    apply_mp_order(payment=payment, mp_order=mp_order)
    order.refresh_from_db()
    return order


def list_pse_banks() -> list[dict]:
    """Bancos de PSE para el formulario de pago; se guardan en caché una hora."""
    banks = cache.get(_PSE_BANKS_CACHE_KEY)
    if banks is None:
        banks = get_gateway().list_pse_banks()
        if banks:
            cache.set(_PSE_BANKS_CACHE_KEY, banks, _PSE_BANKS_CACHE_SECONDS)
    return banks
