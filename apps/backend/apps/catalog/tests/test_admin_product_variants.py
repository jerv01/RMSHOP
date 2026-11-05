from decimal import Decimal

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.catalog.models import Category
from apps.catalog.services import create_product, create_product_variant
from apps.users.clerk import ClerkClaims
from apps.users.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_client(db):
    client = APIClient()
    user = User.objects.create(clerk_user_id="admin_var_1", email="admin_var@rmshop.co")
    claims = ClerkClaims(sub="admin_var_1", email="admin_var@rmshop.co", role="admin")
    client.force_authenticate(user=user, token=claims)
    return client


@pytest.fixture
def customer_client(db):
    client = APIClient()
    user = User.objects.create(clerk_user_id="cust_var_1", email="cust_var@rmshop.co")
    claims = ClerkClaims(sub="cust_var_1", email="cust_var@rmshop.co", role=None)
    client.force_authenticate(user=user, token=claims)
    return client


@pytest.fixture
def sample_product(db):
    category = Category.objects.get(slug="camisetas-tops")
    product, _ = create_product(
        name="Camiseta Premium",
        description="Algodón pima peruano",
        price=Decimal("95000"),
        material="100% Algodón Pima",
        category=category,
    )
    return product


@pytest.mark.django_db
def test_admin_can_create_variant(admin_client, sample_product):
    payload = {"color": "negro", "size": "m", "stock_quantity": 4}
    response = admin_client.post(
        f"/api/v1/admin/products/{sample_product.id}/variants/",
        data=payload,
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["id"] is not None
    assert data["product_id"] == sample_product.id
    assert data["color"] == "Negro"
    assert data["size"] == "M"
    assert data["stock_quantity"] == 4


@pytest.mark.django_db
def test_admin_cannot_create_duplicate_variant(admin_client, sample_product):
    create_product_variant(product_id=sample_product.id, color="Azul", size="L")

    response = admin_client.post(
        f"/api/v1/admin/products/{sample_product.id}/variants/",
        data={"color": "azul", "size": "l"},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["code"] == "validation_error"
    assert "non_field_errors" in data["fields"]


@pytest.mark.django_db
def test_admin_can_bulk_create_variants(admin_client, sample_product):
    payload = {
        "colors": ["Negro", "Blanco"],
        "sizes": ["S", "M", "L"],
    }
    response = admin_client.post(
        f"/api/v1/admin/products/{sample_product.id}/variants/bulk/",
        data=payload,
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert len(data) == 6
    assert sample_product.variants.count() == 6


@pytest.mark.django_db
def test_admin_can_list_variants(admin_client, sample_product):
    create_product_variant(product_id=sample_product.id, color="Negro", size="S")
    create_product_variant(product_id=sample_product.id, color="Negro", size="M")

    response = admin_client.get(f"/api/v1/admin/products/{sample_product.id}/variants/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2


@pytest.mark.django_db
def test_admin_can_delete_variant_with_zero_stock(admin_client, sample_product):
    variant = create_product_variant(
        product_id=sample_product.id,
        color="Rojo",
        size="XL",
        stock_quantity=0,
    )

    response = admin_client.delete(
        f"/api/v1/admin/products/{sample_product.id}/variants/{variant.id}/"
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not sample_product.variants.filter(id=variant.id).exists()


@pytest.mark.django_db
def test_admin_cannot_delete_variant_with_positive_stock(admin_client, sample_product):
    variant = create_product_variant(
        product_id=sample_product.id,
        color="Verde",
        size="M",
        stock_quantity=5,
    )

    response = admin_client.delete(
        f"/api/v1/admin/products/{sample_product.id}/variants/{variant.id}/"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["code"] == "validation_error"
    assert "stock_quantity" in data["fields"]
    assert sample_product.variants.filter(id=variant.id).exists()


@pytest.mark.django_db
def test_permissions_variant_endpoints(api_client, customer_client, sample_product):
    url = f"/api/v1/admin/products/{sample_product.id}/variants/"

    # Anónimo
    assert api_client.get(url).status_code == status.HTTP_401_UNAUTHORIZED
    assert api_client.post(url).status_code == status.HTTP_401_UNAUTHORIZED

    # Cliente regular
    assert customer_client.get(url).status_code == status.HTTP_403_FORBIDDEN
    assert customer_client.post(url).status_code == status.HTTP_403_FORBIDDEN
