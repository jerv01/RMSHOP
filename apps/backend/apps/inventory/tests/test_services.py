from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.catalog.models import Category, Product, ProductVariant
from apps.inventory.models import StockMovement
from apps.inventory.services import adjust_variant_stock
from apps.users.models import User


@pytest.fixture
def product_and_variant(db):
    category = Category.objects.get(slug="camisetas-tops")
    product = Product.objects.create(
        name="Camiseta Polo Clásica",
        slug="camiseta-polo-clasica",
        description="Camiseta polo en piqué de algodón.",
        price=Decimal("65000"),
        material="100% Algodón Piqué",
        category=category,
    )
    variant = ProductVariant.objects.create(
        product=product,
        color="Azul Marino",
        size="L",
        stock_quantity=3,
    )
    return product, variant


@pytest.fixture
def admin_user(db):
    return User.objects.create(
        clerk_user_id="admin_service_test",
        email="admin_service@rmshop.co",
        first_name="Admin",
        last_name="Test",
    )


@pytest.mark.django_db
def test_adjust_stock_increase_happy_path(product_and_variant, admin_user):
    """AC-HU-37-1: Dada una combinación con stock 3, al sumar 2, el stock pasa a 5."""
    product, variant = product_and_variant

    updated_variant, movement = adjust_variant_stock(
        variant_id=variant.id,
        delta=2,
        admin_user=admin_user,
        reason="Ingreso de lote semanal",
        product_id=product.id,
    )

    assert updated_variant.stock_quantity == 5
    variant.refresh_from_db()
    assert variant.stock_quantity == 5

    assert movement.variant == variant
    assert movement.admin == admin_user
    assert movement.delta == 2
    assert movement.resulting_stock == 5
    assert movement.reason == "Ingreso de lote semanal"


@pytest.mark.django_db
def test_adjust_stock_from_zero_exhausted(product_and_variant, admin_user):
    """AC-HU-37-3: Combinación agotada (stock 0), al incrementarse queda disponible."""
    _, variant = product_and_variant
    variant.stock_quantity = 0
    variant.save(update_fields=["stock_quantity"])

    updated_variant, movement = adjust_variant_stock(
        variant_id=variant.id,
        delta=4,
        admin_user=admin_user,
        reason="Reposición de inventario agotado",
    )

    assert updated_variant.stock_quantity == 4
    assert movement.resulting_stock == 4
    assert movement.delta == 4


@pytest.mark.django_db
def test_adjust_stock_reductive_valid(product_and_variant, admin_user):
    """Permite reducciones válidas de stock si el stock resultante no es negativo."""
    _, variant = product_and_variant

    updated_variant, movement = adjust_variant_stock(
        variant_id=variant.id,
        delta=-2,
        admin_user=admin_user,
        reason="Ajuste por daño en exhibición",
    )

    assert updated_variant.stock_quantity == 1
    assert movement.delta == -2
    assert movement.resulting_stock == 1


@pytest.mark.django_db
def test_adjust_stock_negative_resulting_stock_rejected(product_and_variant, admin_user):
    """AC-HU-37-2: Cantidad que resulte en stock negativo se rechaza con error de validación."""
    _, variant = product_and_variant

    with pytest.raises(ValidationError) as exc_info:
        adjust_variant_stock(
            variant_id=variant.id,
            delta=-5,
            admin_user=admin_user,
        )

    errors = exc_info.value.message_dict
    assert "delta" in errors
    assert "negativo" in errors["delta"][0]

    # Verificar que el stock no cambió
    variant.refresh_from_db()
    assert variant.stock_quantity == 3
    assert StockMovement.objects.count() == 0


@pytest.mark.django_db
def test_adjust_stock_zero_delta_rejected(product_and_variant, admin_user):
    """Delta cero se rechaza."""
    _, variant = product_and_variant

    with pytest.raises(ValidationError) as exc_info:
        adjust_variant_stock(
            variant_id=variant.id,
            delta=0,
            admin_user=admin_user,
        )

    errors = exc_info.value.message_dict
    assert "delta" in errors
    assert "cero" in errors["delta"][0]


@pytest.mark.django_db
def test_adjust_stock_nonexistent_variant_raises_error(admin_user):
    with pytest.raises(ValidationError) as exc_info:
        adjust_variant_stock(
            variant_id=99999,
            delta=3,
            admin_user=admin_user,
        )

    errors = exc_info.value.message_dict
    assert "variant_id" in errors


@pytest.mark.django_db
def test_adjust_stock_mismatched_product_id_raises_error(product_and_variant, admin_user):
    _, variant = product_and_variant

    with pytest.raises(ValidationError) as exc_info:
        adjust_variant_stock(
            variant_id=variant.id,
            delta=3,
            admin_user=admin_user,
            product_id=99999,
        )

    errors = exc_info.value.message_dict
    assert "variant_id" in errors
