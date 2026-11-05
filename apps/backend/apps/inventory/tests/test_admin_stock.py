from decimal import Decimal

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.catalog.models import Category, Product, ProductVariant
from apps.inventory.models import StockMovement
from apps.users.clerk import ClerkClaims
from apps.users.models import User


@pytest.fixture
def product(db):
    category = Category.objects.get(slug="camisetas-tops")
    return Product.objects.create(
        name="Chaqueta Bomber Streetwear",
        slug="chaqueta-bomber-streetwear",
        description="Chaqueta ligera para clima frío con acabados de alta calidad.",
        price=Decimal("180000"),
        material="Poliéster impermeable",
        category=category,
    )


@pytest.fixture
def variant(product):
    return ProductVariant.objects.create(
        product=product,
        color="Negro",
        size="M",
        stock_quantity=3,
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create(
        clerk_user_id="admin_stock_tester",
        email="admin_tester@rmshop.co",
        first_name="Admin",
        last_name="Tester",
    )


@pytest.fixture
def admin_client(admin_user):
    client = APIClient()
    claims = ClerkClaims(
        sub=admin_user.clerk_user_id,
        email=admin_user.email,
        role="admin",
    )
    client.force_authenticate(user=admin_user, token=claims)
    return client


@pytest.fixture
def customer_client(db):
    user = User.objects.create(
        clerk_user_id="customer_stock_tester",
        email="customer@rmshop.co",
    )
    client = APIClient()
    claims = ClerkClaims(
        sub=user.clerk_user_id,
        email=user.email,
        role=None,
    )
    client.force_authenticate(user=user, token=claims)
    return client


@pytest.mark.django_db
def test_admin_adjust_stock_increase_happy_path(admin_client, variant, admin_user):
    """AC-HU-37-1: Dada combinación con stock 3, al sumar 2, el stock pasa a 5."""
    url = f"/api/v1/admin/variants/{variant.id}/stock"
    payload = {
        "delta": 2,
        "reason": "Ingreso de lote semanal",
    }

    response = admin_client.post(url, data=payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["variant"]["id"] == variant.id
    assert data["variant"]["stock_quantity"] == 5

    assert data["movement"]["delta"] == 2
    assert data["movement"]["resulting_stock"] == 5
    assert data["movement"]["reason"] == "Ingreso de lote semanal"
    assert data["movement"]["admin"]["email"] == admin_user.email

    # Verificar persistencia en base de datos
    variant.refresh_from_db()
    assert variant.stock_quantity == 5

    movement = StockMovement.objects.get(id=data["movement"]["id"])
    assert movement.variant == variant
    assert movement.admin == admin_user
    assert movement.delta == 2
    assert movement.resulting_stock == 5


@pytest.mark.django_db
def test_admin_adjust_stock_exhausted_to_available(admin_client, variant):
    """AC-HU-37-3: Combinación agotada (stock 0), al incrementarse queda disponible."""
    variant.stock_quantity = 0
    variant.save(update_fields=["stock_quantity"])

    url = f"/api/v1/admin/variants/{variant.id}/stock"
    payload = {"delta": 8, "reason": "Reposición de agotados"}

    response = admin_client.post(url, data=payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["variant"]["stock_quantity"] == 8

    variant.refresh_from_db()
    assert variant.stock_quantity == 8


@pytest.mark.django_db
def test_admin_adjust_stock_negative_delta_valid(admin_client, variant):
    """Permite restar stock siempre que no sea menor a 0."""
    url = f"/api/v1/admin/variants/{variant.id}/stock"
    payload = {"delta": -2, "reason": "Merma en tienda"}

    response = admin_client.post(url, data=payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["variant"]["stock_quantity"] == 1
    assert data["movement"]["delta"] == -2
    assert data["movement"]["resulting_stock"] == 1


@pytest.mark.django_db
def test_admin_adjust_stock_negative_resulting_stock_rejected(admin_client, variant):
    """AC-HU-37-2: Cantidad que resulte en stock negativo se rechaza con validation_error."""
    url = f"/api/v1/admin/variants/{variant.id}/stock"
    payload = {"delta": -5}

    response = admin_client.post(url, data=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["code"] == "validation_error"
    assert "delta" in data["fields"]

    variant.refresh_from_db()
    assert variant.stock_quantity == 3
    assert StockMovement.objects.count() == 0


@pytest.mark.django_db
def test_admin_adjust_stock_non_numeric_delta_rejected(admin_client, variant):
    """AC-HU-37-2: Cantidad no numérica se rechaza con validation_error."""
    url = f"/api/v1/admin/variants/{variant.id}/stock"
    payload = {"delta": "diez"}

    response = admin_client.post(url, data=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["code"] == "validation_error"
    assert "delta" in data["fields"]


@pytest.mark.django_db
def test_admin_adjust_stock_zero_delta_rejected(admin_client, variant):
    """Delta cero se rechaza."""
    url = f"/api/v1/admin/variants/{variant.id}/stock"
    payload = {"delta": 0}

    response = admin_client.post(url, data=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["code"] == "validation_error"
    assert "delta" in data["fields"]


@pytest.mark.django_db
def test_admin_adjust_stock_product_context_url(admin_client, product, variant):
    """Funciona a través de la ruta con contexto de producto."""
    url = f"/api/v1/admin/products/{product.id}/variants/{variant.id}/stock"
    payload = {"delta": 4}

    response = admin_client.post(url, data=payload)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["variant"]["stock_quantity"] == 7


@pytest.mark.django_db
def test_admin_adjust_stock_mismatched_product_returns_404(admin_client, variant):
    """Retorna 404 si el product_id en la ruta no coincide con la variante."""
    url = f"/api/v1/admin/products/99999/variants/{variant.id}/stock"
    payload = {"delta": 4}

    response = admin_client.post(url, data=payload)

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_admin_get_stock_movements_history(admin_client, variant, admin_user):
    """Auditoría: consulta historial cronológico descendente de movimientos de una variante."""
    url = f"/api/v1/admin/variants/{variant.id}/stock"

    # Realizar dos ajustes sucesivos
    admin_client.post(url, data={"delta": 5, "reason": "Ingreso 1"})
    admin_client.post(url, data={"delta": -2, "reason": "Venta directa tienda"})

    history_url = f"/api/v1/admin/variants/{variant.id}/stock-movements"
    response = admin_client.get(history_url)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2

    # Primer elemento es el más reciente (delta: -2)
    assert data[0]["delta"] == -2
    assert data[0]["resulting_stock"] == 6
    assert data[0]["reason"] == "Venta directa tienda"
    assert data[0]["admin"]["email"] == admin_user.email

    # Segundo elemento es el anterior (delta: 5)
    assert data[1]["delta"] == 5
    assert data[1]["resulting_stock"] == 8
    assert data[1]["reason"] == "Ingreso 1"


@pytest.mark.django_db
def test_stock_adjust_permissions(customer_client, variant):
    """Usuarios no administradores reciben 403 Forbidden y anónimos reciben 401."""
    url = f"/api/v1/admin/variants/{variant.id}/stock"
    payload = {"delta": 2}

    # Cliente regular (no admin) -> 403
    response = customer_client.post(url, data=payload)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Anónimo -> 401
    anon_client = APIClient()
    response_anon = anon_client.post(url, data=payload)
    assert response_anon.status_code == status.HTTP_401_UNAUTHORIZED
