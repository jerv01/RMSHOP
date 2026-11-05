from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction

from apps.catalog.models import Category, Product, ProductImage, ProductStatus, ProductVariant


@pytest.mark.django_db
def test_initial_categories_seeded():
    categories = list(Category.objects.values_list("name", "slug"))
    assert ("Camisetas / Tops", "camisetas-tops") in categories
    assert ("Buzos / Sacos", "buzos-sacos") in categories
    assert ("Pantalones / Jeans", "pantalones-jeans") in categories
    assert ("Conjuntos", "conjuntos") in categories


@pytest.mark.django_db
def test_create_custom_category():
    category = Category.objects.create(name="Accesorios", slug="accesorios")
    assert str(category) == "Accesorios"
    assert category.slug == "accesorios"


@pytest.mark.django_db
def test_category_slug_must_be_unique():
    with pytest.raises(IntegrityError):
        # "buzos-sacos" already exists from seed migration
        Category.objects.create(name="Otro Buzo", slug="buzos-sacos")


@pytest.mark.django_db
def test_create_product_defaults_to_draft():
    category = Category.objects.get(slug="conjuntos")
    product = Product.objects.create(
        name="Conjunto RM Urbano",
        slug="conjunto-rm-urbano",
        description="Conjunto deportivo de algodón.",
        price=Decimal("120000"),
        previous_price=Decimal("140000"),
        material="100% Algodón",
        category=category,
    )
    assert product.status == ProductStatus.DRAFT
    assert product.price == Decimal("120000")
    assert product.previous_price == Decimal("140000")
    assert str(product) == "Conjunto RM Urbano"


@pytest.mark.django_db
def test_product_slug_must_be_unique():
    category = Category.objects.get(slug="pantalones-jeans")
    Product.objects.create(
        name="Jean RM Classic",
        slug="jean-rm-classic",
        description="Jean clásico de mezclilla.",
        price=Decimal("95000"),
        material="Denim",
        category=category,
    )
    with pytest.raises(IntegrityError):
        Product.objects.create(
            name="Jean RM Classic 2",
            slug="jean-rm-classic",
            description="Otro jean.",
            price=Decimal("99000"),
            material="Denim",
            category=category,
        )


@pytest.mark.django_db
def test_product_image_creation_and_constraints():
    category = Category.objects.get(slug="camisetas-tops")
    product = Product.objects.create(
        name="Top Lino",
        slug="top-lino",
        description="Top fresco.",
        price=Decimal("60000"),
        category=category,
    )
    img1 = ProductImage.objects.create(
        product=product,
        image="products/2026/11/test.webp",
        alt_text="Top lino blanco vista frontal",
        position=1,
    )
    assert img1.id is not None
    assert img1.position == 1
    assert str(img1) == f"Imagen 1 de {product.name}"

    # Unique constraint on (product, position)
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            ProductImage.objects.create(
                product=product,
                image="products/2026/11/test2.webp",
                alt_text="Otra foto",
                position=1,
            )

    # Cascade deletion: deleting product deletes its images
    product.delete()
    assert not ProductImage.objects.filter(id=img1.id).exists()


@pytest.mark.django_db
def test_product_variant_creation_and_constraints():
    category = Category.objects.get(slug="camisetas-tops")
    product = Product.objects.create(
        name="Camiseta Boxy",
        slug="camiseta-boxy",
        description="Desc",
        price=Decimal("70000"),
        category=category,
    )
    v1 = ProductVariant.objects.create(
        product=product,
        color="Negro",
        size="M",
        stock_quantity=5,
    )
    assert v1.id is not None
    assert v1.color == "Negro"
    assert v1.size == "M"
    assert v1.stock_quantity == 5
    assert str(v1) == f"{product.name} - Negro / M"

    # Unique constraint (product, color, size)
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            ProductVariant.objects.create(
                product=product,
                color="Negro",
                size="M",
                stock_quantity=2,
            )

    # Cascade deletion
    product.delete()
    assert not ProductVariant.objects.filter(id=v1.id).exists()
