from decimal import Decimal

import pytest

from apps.catalog.models import Category, Product, ProductVariant
from apps.inventory.models import StockMovement
from apps.users.models import User


@pytest.fixture
def product_and_variant(db):
    category = Category.objects.get(slug="camisetas-tops")
    product = Product.objects.create(
        name="Camiseta Básica Stock",
        slug="camiseta-basica-stock",
        description="Camiseta para pruebas de inventario",
        price=Decimal("45000"),
        material="100% Algodón",
        category=category,
    )
    variant = ProductVariant.objects.create(
        product=product,
        color="Blanco",
        size="M",
        stock_quantity=3,
    )
    return product, variant


@pytest.fixture
def admin_user(db):
    return User.objects.create(
        clerk_user_id="admin_stock_user",
        email="admin_stock@rmshop.co",
        first_name="Admin",
        last_name="Inventario",
    )


@pytest.mark.django_db
def test_create_stock_movement(product_and_variant, admin_user):
    _, variant = product_and_variant

    movement = StockMovement.objects.create(
        variant=variant,
        admin=admin_user,
        delta=2,
        resulting_stock=5,
        reason="Ingreso de lote semanal",
    )

    assert movement.id is not None
    assert movement.variant == variant
    assert movement.admin == admin_user
    assert movement.delta == 2
    assert movement.resulting_stock == 5
    assert movement.reason == "Ingreso de lote semanal"
    assert movement.created_at is not None
    assert str(movement) == f"Variante #{variant.id}: +2 -> stock 5"


@pytest.mark.django_db
def test_stock_movement_admin_set_null_on_delete(product_and_variant, admin_user):
    _, variant = product_and_variant

    movement = StockMovement.objects.create(
        variant=variant,
        admin=admin_user,
        delta=-1,
        resulting_stock=2,
        reason="Merma o ajuste",
    )

    admin_user.delete()
    movement.refresh_from_db()
    assert movement.admin is None
    assert movement.delta == -1
    assert str(movement) == f"Variante #{variant.id}: -1 -> stock 2"


@pytest.mark.django_db
def test_stock_movement_cascade_on_variant_delete(product_and_variant, admin_user):
    _, variant = product_and_variant

    StockMovement.objects.create(
        variant=variant,
        admin=admin_user,
        delta=5,
        resulting_stock=8,
    )

    variant.delete()
    assert StockMovement.objects.count() == 0
