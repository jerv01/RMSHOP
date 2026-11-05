from decimal import Decimal

import pytest
from rest_framework import status

from apps.catalog.models import Category, Product, ProductStatus
from apps.users.clerk import ClerkClaims
from apps.users.models import User

URL = "/api/v1/admin/products"


@pytest.fixture
def admin_client(api_client):
    user = User.objects.create(clerk_user_id="admin_1", email="admin@rmshop.co")
    claims = ClerkClaims(sub="admin_1", email="admin@rmshop.co", role="admin")
    api_client.force_authenticate(user=user, token=claims)
    return api_client


@pytest.fixture
def customer_client(api_client):
    user = User.objects.create(clerk_user_id="customer_1", email="cliente@rmshop.co")
    claims = ClerkClaims(sub="customer_1", email="cliente@rmshop.co", role=None)
    api_client.force_authenticate(user=user, token=claims)
    return api_client


@pytest.mark.django_db
def test_admin_create_product_success(admin_client):
    category = Category.objects.get(slug="camisetas-tops")
    payload = {
        "name": "Camiseta Oversize Negra",
        "description": "Camiseta pesada de corte holgado.",
        "price": 75000,
        "previous_price": 90000,
        "material": "100% Algodón 240g",
        "category_id": category.id,
    }

    response = admin_client.post(URL, data=payload)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Camiseta Oversize Negra"
    assert data["slug"] == "camiseta-oversize-negra"
    assert data["price"] == "75000"
    assert data["previous_price"] == "90000"
    assert data["material"] == "100% Algodón 240g"
    assert data["category"]["slug"] == "camisetas-tops"
    assert data["status"] == "draft"
    assert data.get("warning") is None

    # Verificar persistencia en base de datos
    product = Product.objects.get(id=data["id"])
    assert product.status == ProductStatus.DRAFT
    assert product.price == Decimal("75000")


@pytest.mark.django_db
def test_admin_create_product_rejects_negative_or_zero_price(admin_client):
    category = Category.objects.get(slug="camisetas-tops")
    payload = {
        "name": "Camiseta Inválida",
        "description": "Descripción",
        "price": -1000,
        "material": "Algodón",
        "category_id": category.id,
    }

    response = admin_client.post(URL, data=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["code"] == "validation_error"
    assert "price" in data["fields"]


@pytest.mark.django_db
def test_admin_create_product_rejects_non_numeric_price(admin_client):
    category = Category.objects.get(slug="camisetas-tops")
    payload = {
        "name": "Camiseta Inválida",
        "description": "Descripción",
        "price": "gratis",
        "material": "Algodón",
        "category_id": category.id,
    }

    response = admin_client.post(URL, data=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["code"] == "validation_error"
    assert "price" in data["fields"]


@pytest.mark.django_db
def test_admin_create_product_rejects_non_existent_category(admin_client):
    payload = {
        "name": "Camiseta",
        "description": "Descripción",
        "price": 50000,
        "material": "Algodón",
        "category_id": 999999,
    }

    response = admin_client.post(URL, data=payload)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["code"] == "validation_error"
    assert "category_id" in data["fields"]


@pytest.mark.django_db
def test_admin_create_product_warns_when_catalog_reaches_30_products(admin_client):
    category = Category.objects.get(slug="camisetas-tops")

    Product.objects.bulk_create(
        [
            Product(
                name=f"Prenda Catálogo {i}",
                slug=f"prenda-catalogo-{i}",
                description="Descripción",
                price=Decimal("45000"),
                material="Algodón",
                category=category,
                status=ProductStatus.DRAFT,
            )
            for i in range(30)
        ]
    )

    payload = {
        "name": "Prenda Número 31",
        "description": "Supera umbral sugerido",
        "price": 85000,
        "material": "Lino",
        "category_id": category.id,
    }

    response = admin_client.post(URL, data=payload)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Prenda Número 31"
    assert "warning" in data
    assert "30 productos" in data["warning"]


@pytest.mark.django_db
def test_anonymous_user_cannot_create_product(api_client):
    category = Category.objects.get(slug="camisetas-tops")
    payload = {
        "name": "Prenda Anónima",
        "description": "Descripción",
        "price": 50000,
        "material": "Algodón",
        "category_id": category.id,
    }

    response = api_client.post(URL, data=payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["code"] == "not_authenticated"


@pytest.mark.django_db
def test_customer_user_cannot_create_product(customer_client):
    category = Category.objects.get(slug="camisetas-tops")
    payload = {
        "name": "Prenda de Cliente",
        "description": "Descripción",
        "price": 50000,
        "material": "Algodón",
        "category_id": category.id,
    }

    response = customer_client.post(URL, data=payload)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert data["code"] == "permission_denied"


# --- Pruebas HU-34: Edición y Eliminación ---


@pytest.mark.django_db
def test_admin_update_product_price_success(admin_client):
    category = Category.objects.get(slug="camisetas-tops")
    product = Product.objects.create(
        name="Camiseta Original",
        slug="camiseta-original",
        description="Descripción",
        price=Decimal("45000"),
        material="Algodón",
        category=category,
        status=ProductStatus.DRAFT,
    )

    detail_url = f"{URL}/{product.id}"
    response = admin_client.patch(detail_url, data={"price": 60000})

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["price"] == "60000"
    assert data["name"] == "Camiseta Original"

    product.refresh_from_db()
    assert product.price == Decimal("60000")


@pytest.mark.django_db
def test_admin_update_product_rejects_invalid_price(admin_client):
    category = Category.objects.get(slug="camisetas-tops")
    product = Product.objects.create(
        name="Camiseta Prueba",
        slug="camiseta-prueba",
        description="Descripción",
        price=Decimal("45000"),
        material="Algodón",
        category=category,
    )

    detail_url = f"{URL}/{product.id}"
    response = admin_client.patch(detail_url, data={"price": -500})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["code"] == "validation_error"
    assert "price" in data["fields"]


@pytest.mark.django_db
def test_admin_update_product_status_and_name(admin_client):
    category = Category.objects.get(slug="camisetas-tops")
    product = Product.objects.create(
        name="Camiseta Draft",
        slug="camiseta-draft",
        description="Descripción",
        price=Decimal("45000"),
        material="Algodón",
        category=category,
        status=ProductStatus.DRAFT,
    )

    detail_url = f"{URL}/{product.id}"
    response = admin_client.patch(
        detail_url,
        data={"name": "Camiseta Publicada Nueva", "status": "published"},
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Camiseta Publicada Nueva"
    assert data["slug"] == "camiseta-publicada-nueva"
    assert data["status"] == "published"


@pytest.mark.django_db
def test_admin_delete_product_archives_without_removing_row(admin_client):
    category = Category.objects.get(slug="camisetas-tops")
    product = Product.objects.create(
        name="Prenda a Borrar",
        slug="prenda-a-borrar",
        description="Descripción",
        price=Decimal("45000"),
        material="Algodón",
        category=category,
        status=ProductStatus.PUBLISHED,
    )

    detail_url = f"{URL}/{product.id}"
    response = admin_client.delete(detail_url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    # Comprobar que sigue existiendo en BD para preservar pedidos/carritos (AC-HU-34-3)
    product.refresh_from_db()
    assert product.status == ProductStatus.ARCHIVED


@pytest.mark.django_db
def test_admin_get_product_detail(admin_client):
    category = Category.objects.get(slug="camisetas-tops")
    product = Product.objects.create(
        name="Prenda Detalle",
        slug="prenda-detalle",
        description="Descripción detalle",
        price=Decimal("70000"),
        material="Lino",
        category=category,
    )

    detail_url = f"{URL}/{product.id}"
    response = admin_client.get(detail_url)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == product.id
    assert data["name"] == "Prenda Detalle"


@pytest.mark.django_db
def test_product_detail_not_found(admin_client):
    detail_url = f"{URL}/999999"
    assert admin_client.get(detail_url).status_code == status.HTTP_404_NOT_FOUND
    assert (
        admin_client.patch(detail_url, data={"price": 10000}).status_code
        == status.HTTP_404_NOT_FOUND
    )
    assert admin_client.delete(detail_url).status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_admin_list_all_products(admin_client):
    category = Category.objects.get(slug="camisetas-tops")
    Product.objects.create(
        name="Prenda Borrador",
        slug="prenda-borrador",
        description="Desc",
        price=Decimal("50000"),
        material="Algodón",
        category=category,
        status=ProductStatus.DRAFT,
    )
    Product.objects.create(
        name="Prenda Publicada",
        slug="prenda-publicada",
        description="Desc",
        price=Decimal("70000"),
        material="Algodón",
        category=category,
        status=ProductStatus.PUBLISHED,
    )

    response = admin_client.get(URL)
    assert response.status_code == status.HTTP_200_OK
    items = response.json()
    assert len(items) == 2
    assert {item["slug"] for item in items} == {"prenda-borrador", "prenda-publicada"}


@pytest.mark.django_db
def test_customer_cannot_update_or_delete_product(customer_client):
    category = Category.objects.get(slug="camisetas-tops")
    product = Product.objects.create(
        name="Prenda Protegida",
        slug="prenda-protegida",
        description="Desc",
        price=Decimal("50000"),
        material="Algodón",
        category=category,
    )
    detail_url = f"{URL}/{product.id}"

    assert customer_client.get(detail_url).status_code == status.HTTP_403_FORBIDDEN
    assert (
        customer_client.patch(detail_url, data={"price": 20000}).status_code
        == status.HTTP_403_FORBIDDEN
    )
    assert customer_client.delete(detail_url).status_code == status.HTTP_403_FORBIDDEN
