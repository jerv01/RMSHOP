import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def test_checkout_creates_pending_order(customer_api, cart_with_item, checkout_data):
    response = customer_api.post("/api/v1/checkout", checkout_data)

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending_payment"
    assert body["status_label"] == "Pendiente de Pago"
    assert body["total"] == "105000"
    assert len(body["items"]) == 1
    assert body["status_history"][0]["to_status_label"] == "Pendiente de Pago"


def test_checkout_requires_authentication(checkout_data):
    response = APIClient().post("/api/v1/checkout", checkout_data)
    assert response.status_code in (401, 403)


def test_checkout_validates_fields(customer_api, cart_with_item):
    response = customer_api.post("/api/v1/checkout", {"municipality": "Cali", "phone": "abc"})
    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "validation_error"
    assert {"address_line", "recipient_name", "phone"} <= set(body["fields"])


def test_checkout_uncovered_municipality_message(customer_api, cart_with_item, checkout_data):
    response = customer_api.post("/api/v1/checkout", {**checkout_data, "municipality": "Bogotá"})
    assert response.status_code == 400
    assert response.json()["code"] == "municipality_not_covered"
    assert response.json()["message"] == "Solo enviamos a Cali, Palmira, Jamundí y Yumbo."


def test_ac_hu_21_1_customer_sees_pending_order(customer_api, cart_with_item, checkout_data):
    order_number = customer_api.post("/api/v1/checkout", checkout_data).json()["order_number"]

    detail = customer_api.get(f"/api/v1/orders/{order_number}")
    assert detail.status_code == 200
    assert detail.json()["status_label"] == "Pendiente de Pago"

    listing = customer_api.get("/api/v1/orders")
    assert listing.status_code == 200
    assert [o["order_number"] for o in listing.json()] == [order_number]
    assert listing.json()[0]["status_label"] == "Pendiente de Pago"


def test_other_customer_cannot_see_order(
    customer_api, other_customer_api, cart_with_item, checkout_data
):
    order_number = customer_api.post("/api/v1/checkout", checkout_data).json()["order_number"]

    assert other_customer_api.get(f"/api/v1/orders/{order_number}").status_code == 404
    assert other_customer_api.get("/api/v1/orders").json() == []
