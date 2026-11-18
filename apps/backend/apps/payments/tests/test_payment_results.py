"""HU-22 (pago aprobado), HU-23 (pago rechazado) y HU-24 (cancelación a los 30 minutos)."""

import hashlib
import hmac
from datetime import timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIClient

from apps.inventory.models import StockMovement
from apps.orders.models import OrderStatus
from apps.payments.models import Payment
from apps.payments.services import cancel_expired_orders

from .conftest import DEBIT_PAYLOAD, mp_order

pytestmark = pytest.mark.django_db

WEBHOOK_URL = "/api/v1/webhooks/payments/mercadopago"
WEBHOOK_SECRET = "secreto-webhook"


@pytest.fixture(autouse=True)
def secrets(settings):
    settings.MERCADOPAGO_WEBHOOK_SECRET = WEBHOOK_SECRET
    settings.CRON_SECRET = "secreto-cron"


@pytest.fixture
def paying_order(customer_api, pending_order, mp):
    """Pedido pendiente con un pago enviado a MercadoPago que aún no tiene respuesta final."""
    mp.post("/v1/orders").respond(201, json=mp_order("processing", "in_process"))
    customer_api.post(f"/api/v1/orders/{pending_order.order_number}/payments", DEBIT_PAYLOAD)
    return pending_order


def _notify(data_id="ORD01TEST", *, secret=WEBHOOK_SECRET, request_id="req-1", ts="1700000000"):
    manifest = f"id:{data_id.lower()};request-id:{request_id};ts:{ts};"
    signature = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    return APIClient().post(
        f"{WEBHOOK_URL}?data.id={data_id}&type=order",
        {"type": "order", "action": "order.processed", "data": {"id": data_id}},
        format="json",
        HTTP_X_SIGNATURE=f"ts={ts},v1={signature}",
        HTTP_X_REQUEST_ID=request_id,
    )


def _history(order):
    return list(order.status_history.values_list("to_status", flat=True))


# HU-22 -----------------------------------------------------------------------


def test_ac_hu_22_1_and_3_confirmation_approves_once(paying_order, mp):
    mp.get("/v1/orders/ORD01TEST").respond(200, json=mp_order("processed", "accredited"))

    first, second = _notify(), _notify()

    assert first.status_code == second.status_code == 200
    paying_order.refresh_from_db()
    assert paying_order.status == OrderStatus.PAYMENT_APPROVED
    assert _history(paying_order).count(OrderStatus.PAYMENT_APPROVED) == 1


def test_ac_hu_22_2_confirmation_for_cancelled_order_is_flagged(paying_order, mp):
    paying_order.payment_expires_at = timezone.now() - timedelta(seconds=1)
    paying_order.save(update_fields=["payment_expires_at"])
    get = mp.get("/v1/orders/ORD01TEST")
    get.respond(200, json=mp_order("processing", "in_process"))
    assert cancel_expired_orders() == 1

    get.respond(200, json=mp_order("processed", "accredited"))
    assert _notify().status_code == 200

    paying_order.refresh_from_db()
    assert paying_order.status == OrderStatus.CANCELLED
    assert Payment.objects.get().needs_review is True


def test_invalid_signature_is_rejected_without_calling_gateway(paying_order, mp):
    get = mp.get("/v1/orders/ORD01TEST").respond(200, json=mp_order("processed", "accredited"))

    response = _notify(secret="otro-secreto")

    assert response.status_code == 400
    assert response.json()["code"] == "invalid_signature"
    assert not get.called


def test_unknown_order_notification_is_ignored(mp):
    get = mp.get("/v1/orders/ORD-AJENA")
    assert _notify("ORD-AJENA").status_code == 200
    assert not get.called


# HU-23 -----------------------------------------------------------------------


def test_ac_hu_23_rejection_cancels_restocks_and_allows_new_order(
    paying_order, customer, variant, customer_api, checkout_data, mp
):
    mp.get("/v1/orders/ORD01TEST").respond(200, json=mp_order("failed", "rejected_by_issuer"))

    assert _notify().status_code == 200

    detail = customer_api.get(f"/api/v1/orders/{paying_order.order_number}").json()
    assert detail["status_label"] == "Cancelado"
    assert [h["to_status"] for h in detail["status_history"]] == [
        "pending_payment",
        "payment_rejected",
        "cancelled",
    ]
    variant.refresh_from_db()
    assert variant.stock_quantity == 5

    # AC-HU-23-3: el reintento es un pedido nuevo con el stock disponible.
    customer_api.post("/api/v1/cart/items", {"variant_id": variant.id, "quantity": 2})
    new_order = customer_api.post("/api/v1/checkout", checkout_data)
    assert new_order.status_code == 201
    assert new_order.json()["order_number"] != paying_order.order_number


# HU-24 -----------------------------------------------------------------------


def _expire(order):
    order.payment_expires_at = timezone.now() - timedelta(seconds=1)
    order.save(update_fields=["payment_expires_at"])


def test_ac_hu_24_1_expired_order_is_cancelled_and_restocked_once(pending_order, variant):
    _expire(pending_order)

    assert cancel_expired_orders() == 1
    assert cancel_expired_orders() == 0

    pending_order.refresh_from_db()
    variant.refresh_from_db()
    assert pending_order.status == OrderStatus.CANCELLED
    assert variant.stock_quantity == 5
    reason = f"Devolución pedido {pending_order.order_number}"
    assert StockMovement.objects.filter(reason=reason).count() == 1


def test_ac_hu_24_2_gateway_answer_before_timeout_prevents_cancellation(paying_order, mp):
    _expire(paying_order)
    mp.get("/v1/orders/ORD01TEST").respond(200, json=mp_order("processed", "accredited"))

    assert cancel_expired_orders() == 0

    paying_order.refresh_from_db()
    assert paying_order.status == OrderStatus.PAYMENT_APPROVED


def test_gateway_down_postpones_cancellation(paying_order, mp):
    _expire(paying_order)
    mp.get("/v1/orders/ORD01TEST").respond(500)

    assert cancel_expired_orders() == 0
    paying_order.refresh_from_db()
    assert paying_order.status == OrderStatus.PENDING_PAYMENT


def test_order_within_window_is_not_touched(pending_order):
    assert cancel_expired_orders() == 0
    pending_order.refresh_from_db()
    assert pending_order.status == OrderStatus.PENDING_PAYMENT


def test_scheduled_tasks_endpoint_requires_cron_secret(pending_order):
    _expire(pending_order)
    url = "/api/v1/internal/run-scheduled-tasks"

    assert APIClient().post(url).status_code == 403
    assert APIClient().post(url, HTTP_X_CRON_SECRET="incorrecto").status_code == 403

    response = APIClient().post(url, HTTP_X_CRON_SECRET="secreto-cron")
    assert response.status_code == 200
    assert response.json() == {"released_reservations": 0, "cancelled_orders": 1}


def test_run_scheduled_tasks_command(pending_order, capsys):
    _expire(pending_order)
    call_command("run_scheduled_tasks")
    assert "Pedidos cancelados: 1" in capsys.readouterr().out
