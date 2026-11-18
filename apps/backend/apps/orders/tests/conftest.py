from decimal import Decimal

import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from apps.cart.services import add_to_cart
from apps.catalog.models import Category, Product, ProductStatus, ProductVariant
from apps.users.clerk import ClerkClaims
from apps.users.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def _clear_throttle_cache():
    cache.clear()
    yield
    cache.clear()


def make_api_client(user) -> APIClient:
    client = APIClient()
    client.force_authenticate(
        user=user, token=ClerkClaims(sub=user.clerk_user_id, email=user.email, role=None)
    )
    return client


@pytest.fixture
def customer(db):
    return UserFactory()


@pytest.fixture
def other_customer(db):
    return UserFactory()


@pytest.fixture
def customer_api(customer):
    return make_api_client(customer)


@pytest.fixture
def other_customer_api(other_customer):
    return make_api_client(other_customer)


@pytest.fixture
def variant(db):
    category, _ = Category.objects.get_or_create(
        slug="pedidos-tests", defaults={"name": "Pedidos Tests"}
    )
    product = Product.objects.create(
        name="Camiseta Pedido",
        slug="camiseta-pedido",
        description="Prenda para pruebas de pedidos.",
        price=Decimal("50000"),
        material="Algodón",
        category=category,
        status=ProductStatus.PUBLISHED,
    )
    return ProductVariant.objects.create(product=product, color="Negro", size="M", stock_quantity=5)


@pytest.fixture
def cart_with_item(customer, variant):
    """Carrito del cliente con 2 unidades reservadas de la variante (stock físico 5)."""
    add_to_cart(user=customer, variant_id=variant.id, quantity=2)
    return customer.cart


@pytest.fixture
def checkout_data():
    return {
        "municipality": "cali",
        "address_line": "Calle 10 # 20-30",
        "recipient_name": "Ana Pérez",
        "phone": "3001234567",
    }
