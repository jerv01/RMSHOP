import json

import httpx
import pytest
from django.utils import timezone

from apps.inventory.models import StockMovement
from apps.orders.models import OrderStatus
from apps.orders.services import cancel_order
from apps.payments.models import Payment, PaymentStatus
from apps.payments.services import apply_mp_order, map_mp_status, sanitize_mp_response

from .conftest import DEBIT_PAYLOAD, PSE_PAYLOAD, mp_order

pytestmark = pytest.mark.django_db


def _pay(api, order, payload):
    return api.post(f"/api/v1/orders/{order.order_number}/payments", payload)


def _sent_body(route):
    return json.loads(route.calls.last.request.content)


# ---------------------------------------------------------------------------
# HU-19: tarjeta débito
# ---------------------------------------------------------------------------


def test_ac_hu_19_1_approved_debit_card_marks_order_paid(customer_api, pending_order, mp):
    route = mp.post("/v1/orders").respond(201, json=mp_order("processed", "accredited"))

    response = _pay(customer_api, pending_order, DEBIT_PAYLOAD)

    assert response.status_code == 201
    body = response.json()
    assert body["order"]["status"] == "payment_approved"
    assert body["order"]["status_label"] == "Pago aprobado"
    assert body["payment"]["status"] == "approved"

    payment = Payment.objects.get()
    sent = _sent_body(route)
    request = route.calls.last.request
    assert request.headers["X-Idempotency-Key"] == str(payment.idempotency_key)
    assert request.headers["Authorization"] == "Bearer APP_USR-token-de-prueba"
    assert sent["external_reference"] == pending_order.order_number
    assert sent["total_amount"] == "105000"
    assert sent["processing_mode"] == "automatic"
    assert sent["transactions"]["payments"][0]["payment_method"] == {
        "id": "debvisa",
        "type": "debit_card",
        "token": "a" * 32,
        "installments": 1,
    }
    assert sent["payer"]["email"] == pending_order.user.email
    assert sent["payer"]["identification"] == {"type": "CC", "number": "12345678"}

    assert payment.mp_order_id == "ORD01TEST"
    assert payment.mp_payment_id == "PAY01TEST"
    assert "tok_secreto" not in json.dumps(payment.raw_response)
    assert "client-token-secreto" not in json.dumps(payment.raw_response)
    assert pending_order.status_history.filter(to_status=OrderStatus.PAYMENT_APPROVED).exists()


@pytest.mark.parametrize(
    "overrides",
    [
        {"payment_method_id": "visa", "payment_type": "credit_card"},
        {"payment_method_id": "master"},
        {"payment_method_id": "debmaster", "payment_type": "credit_card"},
        {"payment_method_id": "amex"},
    ],
)
def test_ac_hu_19_2_credit_or_unaccepted_card_is_rejected(
    customer_api, pending_order, mp, overrides
):
    route = mp.post("/v1/orders").respond(201, json=mp_order("processed", "accredited"))

    response = _pay(customer_api, pending_order, {**DEBIT_PAYLOAD, **overrides})

    assert response.status_code == 400
    assert response.json()["code"] == "only_debit_allowed"
    assert "Solo se aceptan tarjetas débito" in response.json()["message"]
    assert not route.called
    assert not Payment.objects.exists()
    pending_order.refresh_from_db()
    assert pending_order.status == OrderStatus.PENDING_PAYMENT


def test_ac_hu_19_3_unfinished_payment_keeps_order_pending(customer_api, pending_order, mp):
    mp.post("/v1/orders").respond(201, json=mp_order("processing", "in_process"))

    response = _pay(customer_api, pending_order, DEBIT_PAYLOAD)

    assert response.status_code == 201
    detail = customer_api.get(f"/api/v1/orders/{pending_order.order_number}").json()
    assert detail["status"] == "pending_payment"
    assert detail["status_label"] == "Pendiente de Pago"


def test_debit_card_requires_token(customer_api, pending_order, mp):
    payload = {key: value for key, value in DEBIT_PAYLOAD.items() if key != "token"}
    response = _pay(customer_api, pending_order, payload)
    assert response.status_code == 400
    assert "token" in response.json()["fields"]


# ---------------------------------------------------------------------------
# HU-20: PSE
# ---------------------------------------------------------------------------


def test_ac_hu_20_1_pse_redirects_to_bank_then_sync_approves(customer_api, pending_order, mp):
    bank_url = "https://banco.test/pse/123"
    create = mp.post("/v1/orders").respond(
        201, json=mp_order("action_required", "waiting_transfer", redirect_url=bank_url)
    )

    response = _pay(customer_api, pending_order, PSE_PAYLOAD)

    assert response.status_code == 201
    body = response.json()
    assert body["payment"]["redirect_url"] == bank_url
    assert body["order"]["status_label"] == "Pendiente de Pago"

    sent = _sent_body(create)
    pse = sent["transactions"]["payments"][0]
    assert pse["payment_method"] == {
        "id": "pse",
        "type": "bank_transfer",
        "financial_institution": "1007",
    }
    assert pse["expiration_time"] in {"PT29M", "PT30M"}
    assert sent["payer"]["entity_type"] == "individual"
    assert sent["payer"]["address"]["city"] == "Cali"
    assert sent["shipment"]["address"]["street_name"] == "Calle 10 # 20-30"
    assert sent["config"]["online"]["callback_url"] == (
        f"http://tienda.test/pedidos/{pending_order.order_number}"
    )
    assert sent["additional_info"]["payer"]["ip_address"]

    mp.get("/v1/orders/ORD01TEST").respond(200, json=mp_order("processed", "accredited"))
    synced = customer_api.post(f"/api/v1/orders/{pending_order.order_number}/payments/sync")

    assert synced.status_code == 200
    assert synced.json()["order"]["status"] == "payment_approved"
    assert synced.json()["payment"]["status"] == "approved"


def test_pse_requires_bank_and_payer_data(customer_api, pending_order, mp):
    response = _pay(customer_api, pending_order, {"method": "pse"})
    assert response.status_code == 400
    assert {"financial_institution", "entity_type", "identification_number"} <= set(
        response.json()["fields"]
    )


def test_ac_hu_20_2_rejected_payment_cancels_order_and_restocks_once(
    customer_api, pending_order, variant, mp
):
    mp.post("/v1/orders").respond(
        201, json=mp_order("action_required", "waiting_transfer", redirect_url="https://b.test")
    )
    _pay(customer_api, pending_order, PSE_PAYLOAD)
    get_route = mp.get("/v1/orders/ORD01TEST").respond(
        200, json=mp_order("failed", "rejected_by_issuer")
    )

    first = customer_api.post(f"/api/v1/orders/{pending_order.order_number}/payments/sync")
    second = customer_api.post(f"/api/v1/orders/{pending_order.order_number}/payments/sync")

    assert first.status_code == second.status_code == 200
    assert second.json()["order"]["status_label"] == "Cancelado"
    assert get_route.call_count == 1
    assert [h["to_status"] for h in second.json()["order"]["status_history"]] == [
        "pending_payment",
        "payment_rejected",
        "cancelled",
    ]
    variant.refresh_from_db()
    assert variant.stock_quantity == 5
    assert (
        StockMovement.objects.filter(
            reason=f"Devolución pedido {pending_order.order_number}"
        ).count()
        == 1
    )


def test_card_rejected_with_402_cancels_order(customer_api, pending_order, variant, mp):
    mp.post("/v1/orders").respond(
        402, json=mp_order("failed", "card_insufficient_amount", order_id="ORD02")
    )

    response = _pay(customer_api, pending_order, DEBIT_PAYLOAD)

    assert response.status_code == 201
    assert response.json()["payment"]["status"] == "rejected"
    assert response.json()["order"]["status"] == "cancelled"
    variant.refresh_from_db()
    assert variant.stock_quantity == 5


# ---------------------------------------------------------------------------
# HU-21: pedido pendiente, pasarela caída y no doble cobro
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "failure",
    [httpx.ConnectTimeout("timeout"), httpx.Response(500), httpx.Response(429)],
    ids=["timeout", "error-500", "rate-limit"],
)
def test_ac_hu_21_2_gateway_down_keeps_order_consistent(customer_api, pending_order, mp, failure):
    route = mp.post("/v1/orders")
    route.side_effect = [failure]

    response = _pay(customer_api, pending_order, DEBIT_PAYLOAD)

    assert response.status_code == 503
    assert response.json()["code"] == "payment_gateway_unavailable"
    assert "sigue pendiente" in response.json()["message"]
    pending_order.refresh_from_db()
    assert pending_order.status == OrderStatus.PENDING_PAYMENT
    assert Payment.objects.get().status == PaymentStatus.ERROR

    # Cuando MercadoPago vuelve, el cliente puede reintentar con un pago nuevo.
    route.side_effect = None
    route.respond(201, json=mp_order("processed", "accredited"))
    retry = _pay(customer_api, pending_order, DEBIT_PAYLOAD)

    assert retry.status_code == 201
    assert retry.json()["order"]["status"] == "payment_approved"
    keys = set(Payment.objects.values_list("idempotency_key", flat=True))
    assert len(keys) == 2


def test_ac_hu_21_3_second_payment_attempt_does_not_charge_twice(customer_api, pending_order, mp):
    route = mp.post("/v1/orders").respond(
        201, json=mp_order("action_required", "waiting_transfer", redirect_url="https://b.test")
    )

    first = _pay(customer_api, pending_order, PSE_PAYLOAD)
    second = _pay(customer_api, pending_order, PSE_PAYLOAD)

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["code"] == "payment_already_in_progress"
    assert second.json()["fields"]["redirect_url"] == "https://b.test"
    assert route.call_count == 1
    assert Payment.objects.count() == 1


def test_approved_order_cannot_be_paid_again(customer_api, pending_order, mp):
    route = mp.post("/v1/orders").respond(201, json=mp_order("processed", "accredited"))
    _pay(customer_api, pending_order, DEBIT_PAYLOAD)

    again = _pay(customer_api, pending_order, DEBIT_PAYLOAD)

    assert again.status_code == 409
    assert again.json()["code"] == "order_not_payable"
    assert route.call_count == 1


def test_expired_payment_window_is_not_payable(customer_api, pending_order, mp):
    pending_order.payment_expires_at = timezone.now()
    pending_order.save(update_fields=["payment_expires_at"])

    response = _pay(customer_api, pending_order, DEBIT_PAYLOAD)

    assert response.status_code == 409
    assert response.json()["code"] == "payment_window_expired"


def test_invalid_request_to_gateway_returns_clear_error(customer_api, pending_order, mp):
    mp.post("/v1/orders").respond(
        400, json={"errors": [{"code": "invalid_properties", "message": "token inválido"}]}
    )

    response = _pay(customer_api, pending_order, DEBIT_PAYLOAD)

    assert response.status_code == 400
    assert response.json()["code"] == "payment_request_invalid"
    assert response.json()["fields"]["gateway_errors"] == ["invalid_properties"]
    assert Payment.objects.get().status == PaymentStatus.ERROR
    pending_order.refresh_from_db()
    assert pending_order.status == OrderStatus.PENDING_PAYMENT


def test_missing_access_token_returns_503(customer_api, pending_order, mp, settings):
    settings.MERCADOPAGO_ACCESS_TOKEN = ""
    response = _pay(customer_api, pending_order, DEBIT_PAYLOAD)
    assert response.status_code == 503
    assert response.json()["code"] == "payment_gateway_not_configured"


def test_other_customer_cannot_pay_or_sync_order(other_customer_api, pending_order, mp):
    route = mp.post("/v1/orders").respond(201, json=mp_order("processed", "accredited"))

    assert _pay(other_customer_api, pending_order, DEBIT_PAYLOAD).status_code == 404
    sync_url = f"/api/v1/orders/{pending_order.order_number}/payments/sync"
    assert other_customer_api.post(sync_url).status_code == 404
    assert not route.called


def test_late_approval_does_not_reactivate_cancelled_order(customer_api, pending_order, mp):
    mp.post("/v1/orders").respond(201, json=mp_order("processing", "in_process"))
    _pay(customer_api, pending_order, DEBIT_PAYLOAD)
    cancel_order(order=pending_order, note="Vencido")

    payment = apply_mp_order(
        payment=Payment.objects.get(), mp_order=mp_order("processed", "accredited")
    )

    pending_order.refresh_from_db()
    assert pending_order.status == OrderStatus.CANCELLED
    assert payment.status == PaymentStatus.APPROVED


def test_pse_banks_are_listed_and_cached(customer_api, mp):
    route = mp.get("/v1/payment_methods").respond(
        200,
        json=[
            {"id": "visa", "payment_type_id": "credit_card"},
            {
                "id": "pse",
                "payment_type_id": "bank_transfer",
                "financial_institutions": [
                    {"id": "1007", "description": "Bancolombia"},
                    {"id": "1051", "description": "Davivienda"},
                ],
            },
        ],
    )

    first = customer_api.get("/api/v1/payments/pse-banks")
    second = customer_api.get("/api/v1/payments/pse-banks")

    assert first.status_code == 200
    assert first.json() == [
        {"id": "1007", "description": "Bancolombia"},
        {"id": "1051", "description": "Davivienda"},
    ]
    assert second.json() == first.json()
    assert route.call_count == 1


# ---------------------------------------------------------------------------
# Unidades
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("mp_status", "payment_status", "outcome"),
    [
        ("processed", "approved", "approved"),
        ("failed", "rejected", "rejected"),
        ("canceled", "rejected", "rejected"),
        ("expired", "rejected", "rejected"),
        ("action_required", "action_required", "pending"),
        ("processing", "processing", "pending"),
        ("created", "processing", "pending"),
    ],
)
def test_map_mp_status(mp_status, payment_status, outcome):
    mapped = map_mp_status({"status": mp_status})
    assert (mapped.payment_status, mapped.outcome) == (payment_status, outcome)


def test_sanitize_removes_tokens_at_any_depth():
    cleaned = sanitize_mp_response(mp_order("processed", "accredited"))
    text = json.dumps(cleaned)
    assert "tok_secreto" not in text
    assert "client-token-secreto" not in text
    assert cleaned["transactions"]["payments"][0]["id"] == "PAY01TEST"
