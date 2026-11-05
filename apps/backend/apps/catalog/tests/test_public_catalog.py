from decimal import Decimal

import pytest
from rest_framework import status

from apps.catalog.models import Category, Product, ProductStatus, ProductVariant


@pytest.mark.django_db
def test_public_categories_list(api_client):
    response = api_client.get("/api/v1/categories")

    assert response.status_code == status.HTTP_200_OK
    slugs = [item["slug"] for item in response.json()]
    assert slugs == [
        "camisetas-tops",
        "buzos-sacos",
        "pantalones-jeans",
        "conjuntos",
    ]


@pytest.mark.django_db
def test_public_products_list_only_published_with_variants(api_client):
    camisetas = Category.objects.get(slug="camisetas-tops")
    buzos = Category.objects.get(slug="buzos-sacos")

    published_with_variant = Product.objects.create(
        name="Camiseta RM Urban",
        slug="camiseta-rm-urban",
        description="Camiseta pesada de algodón.",
        price=Decimal("75000"),
        previous_price=Decimal("90000"),
        material="100% Algodón",
        category=camisetas,
        status=ProductStatus.PUBLISHED,
    )
    ProductVariant.objects.create(
        product=published_with_variant,
        color="Negro",
        size="M",
        stock_quantity=4,
    )

    # Publicado sin variantes: no se lista (HU-1)
    Product.objects.create(
        name="Camiseta Sin Variantes",
        slug="camiseta-sin-variantes",
        description="Sin variantes",
        price=Decimal("60000"),
        material="Algodón",
        category=camisetas,
        status=ProductStatus.PUBLISHED,
    )

    # Borrador con variante: no se lista
    draft_product = Product.objects.create(
        name="Buzo Borrador",
        slug="buzo-borrador",
        description="En borrador",
        price=Decimal("120000"),
        material="Algodón perchado",
        category=buzos,
        status=ProductStatus.DRAFT,
    )
    ProductVariant.objects.create(
        product=draft_product,
        color="Gris",
        size="L",
        stock_quantity=2,
    )

    response = api_client.get("/api/v1/products")
    assert response.status_code == status.HTTP_200_OK
    items = response.json()
    assert len(items) == 1
    assert items[0]["slug"] == "camiseta-rm-urban"
    assert items[0]["in_stock"] is True
    assert items[0]["category"]["slug"] == "camisetas-tops"

    # Filtrado por categoría sin resultados
    empty_cat_res = api_client.get("/api/v1/products?category=buzos-sacos")
    assert empty_cat_res.status_code == status.HTTP_200_OK
    assert empty_cat_res.json() == []


@pytest.mark.django_db
def test_public_product_detail_by_slug(api_client):
    category = Category.objects.get(slug="camisetas-tops")
    product = Product.objects.create(
        name="Camiseta Detalle",
        slug="camiseta-detalle",
        description="Corte boxy.",
        price=Decimal("80000"),
        material="Algodón 260g",
        category=category,
        status=ProductStatus.PUBLISHED,
    )
    ProductVariant.objects.create(
        product=product,
        color="Blanco",
        size="S",
        stock_quantity=0,
    )

    res = api_client.get("/api/v1/products/camiseta-detalle")
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["name"] == "Camiseta Detalle"
    assert data["in_stock"] is False
    assert len(data["variants"]) == 1

    # Producto inexistente o archivado devuelve 404
    product.status = ProductStatus.ARCHIVED
    product.save()
    assert (
        api_client.get("/api/v1/products/camiseta-detalle").status_code == status.HTTP_404_NOT_FOUND
    )
