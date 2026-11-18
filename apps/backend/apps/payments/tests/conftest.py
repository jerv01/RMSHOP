import pytest
import respx

from apps.orders.services import create_order_from_cart
from apps.orders.tests.conftest import *  # noqa: F403 - reutiliza clientes, variante y carrito

MP_BASE_URL = "https://api.mercadopago.test"


@pytest.fixture(autouse=True)
def mp_settings(settings):
    settings.MERCADOPAGO_ACCESS_TOKEN = "APP_USR-token-de-prueba"
    settings.MERCADOPAGO_API_BASE_URL = MP_BASE_URL
    settings.MERCADOPAGO_TIMEOUT_SECONDS = 1
    settings.MERCADOPAGO_CALLBACK_BASE_URL = "https://tienda.test"
    return settings


@pytest.fixture
def mp():
    with respx.mock(base_url=MP_BASE_URL, assert_all_called=False) as mock:
        yield mock


@pytest.fixture
def pending_order(customer, cart_with_item):
    """Pedido «Pendiente de Pago» de 105.000 COP (2 x 50.000 + envío Cali 5.000)."""
    return create_order_from_cart(
        user=customer,
        municipality="Cali",
        address_line="Calle 10 # 20-30",
        recipient_name="Ana Pérez",
        phone="3001234567",
    )


def mp_order(status, status_detail, *, order_id="ORD01TEST", payment_id="PAY01TEST", **pm):
    """Respuesta de MercadoPago con la forma documentada del Orders API."""
    return {
        "id": order_id,
        "status": status,
        "status_detail": status_detail,
        "transactions": {
            "payments": [
                {
                    "id": payment_id,
                    "amount": "105000",
                    "status": status,
                    "status_detail": status_detail,
                    "payment_method": {"id": None, "type": None, "token": "tok_secreto", **pm},
                }
            ]
        },
        "client_token": "client-token-secreto",
    }


DEBIT_PAYLOAD = {
    "method": "debit_card",
    "token": "a" * 32,
    "payment_method_id": "debvisa",
    "payment_type": "debit_card",
    "identification_type": "CC",
    "identification_number": "12345678",
}

PSE_PAYLOAD = {
    "method": "pse",
    "financial_institution": "1007",
    "entity_type": "individual",
    "first_name": "Ana",
    "last_name": "Pérez",
    "identification_type": "CC",
    "identification_number": "12345678",
    "phone_area_code": "57",
    "phone_number": "3001234567",
    "zip_code": "760001",
    "street_number": "20-30",
    "neighborhood": "Centro",
}
