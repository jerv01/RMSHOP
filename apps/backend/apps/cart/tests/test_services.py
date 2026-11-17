from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.cart.models import Cart, CartItem, StockReservation
from apps.cart.services import (
    RESERVATION_DURATION_MINUTES,
    add_to_cart,
    get_available_variant_stock,
)
from apps.catalog.models import Category, Product, ProductStatus, ProductVariant
from apps.core.exceptions import ApiError
from apps.users.models import User


@pytest.fixture
def user(db):
    return User.objects.create(
        clerk_user_id="user_cart_service_1",
        email="customer1@rmshop.co",
        first_name="Cliente",
        last_name="Uno",
    )


@pytest.fixture
def other_user(db):
    return User.objects.create(
        clerk_user_id="user_cart_service_2",
        email="customer2@rmshop.co",
        first_name="Cliente",
        last_name="Dos",
    )


@pytest.fixture
def category(db):
    cat = Category.objects.filter(slug="camisetas-tops").first()
    if not cat:
        cat = Category.objects.create(
            name="Camisetas y Tops",
            slug="camisetas-tops",
        )
    return cat


@pytest.fixture
def product(db, category):
    return Product.objects.create(
        name="Camiseta Minimalista",
        slug="camiseta-minimalista",
        description="Camiseta básica",
        price=Decimal("50000"),
        material="100% Algodón",
        category=category,
        status=ProductStatus.PUBLISHED,
    )


@pytest.fixture
def variant(db, product):
    return ProductVariant.objects.create(
        product=product,
        color="Negro",
        size="M",
        stock_quantity=10,
    )


@pytest.mark.django_db
def test_get_available_variant_stock_no_reservations(variant):
    assert get_available_variant_stock(variant) == 10


@pytest.mark.django_db
def test_get_available_variant_stock_with_active_reservation(user, variant):
    cart = Cart.objects.create(user=user)
    item = CartItem.objects.create(cart=cart, variant=variant, quantity=3)
    StockReservation.objects.create(
        cart_item=item,
        variant=variant,
        quantity=3,
        expires_at=timezone.now() + timedelta(minutes=15),
    )
    assert get_available_variant_stock(variant) == 7


@pytest.mark.django_db
def test_get_available_variant_stock_with_expired_reservation(user, variant):
    cart = Cart.objects.create(user=user)
    item = CartItem.objects.create(cart=cart, variant=variant, quantity=3)
    StockReservation.objects.create(
        cart_item=item,
        variant=variant,
        quantity=3,
        expires_at=timezone.now() - timedelta(minutes=1),
    )
    assert get_available_variant_stock(variant) == 10


@pytest.mark.django_db
def test_get_available_variant_stock_exclude_reservation(user, variant):
    cart = Cart.objects.create(user=user)
    item = CartItem.objects.create(cart=cart, variant=variant, quantity=4)
    res = StockReservation.objects.create(
        cart_item=item,
        variant=variant,
        quantity=4,
        expires_at=timezone.now() + timedelta(minutes=15),
    )
    assert get_available_variant_stock(variant, exclude_reservation_id=res.id) == 10


@pytest.mark.django_db
def test_get_available_variant_stock_clamped_to_zero(user, variant):
    variant.stock_quantity = 2
    variant.save(update_fields=["stock_quantity"])

    cart = Cart.objects.create(user=user)
    item = CartItem.objects.create(cart=cart, variant=variant, quantity=5)
    StockReservation.objects.create(
        cart_item=item,
        variant=variant,
        quantity=5,
        expires_at=timezone.now() + timedelta(minutes=15),
    )
    assert get_available_variant_stock(variant) == 0


@pytest.mark.django_db
def test_add_to_cart_happy_path(user, variant):
    cart_item, reservation = add_to_cart(user=user, variant_id=variant.id, quantity=2)

    assert cart_item.cart.user == user
    assert cart_item.variant == variant
    assert cart_item.quantity == 2

    assert reservation.cart_item == cart_item
    assert reservation.variant == variant
    assert reservation.quantity == 2
    assert reservation.is_active() is True

    expected_expiry = timezone.now() + timedelta(minutes=RESERVATION_DURATION_MINUTES)
    assert abs((reservation.expires_at - expected_expiry).total_seconds()) < 5


@pytest.mark.django_db
def test_add_to_cart_quantity_increment_refreshes_reservation(user, variant):
    item1, res1 = add_to_cart(user=user, variant_id=variant.id, quantity=2)
    old_expires_at = res1.expires_at

    item2, res2 = add_to_cart(user=user, variant_id=variant.id, quantity=3)

    assert item2.id == item1.id
    assert item2.quantity == 5
    assert res2.id == res1.id
    assert res2.quantity == 5
    assert res2.expires_at >= old_expires_at

    assert CartItem.objects.filter(cart__user=user).count() == 1
    assert StockReservation.objects.count() == 1


@pytest.mark.django_db
def test_add_to_cart_out_of_stock_zero_stock(user, variant):
    variant.stock_quantity = 0
    variant.save(update_fields=["stock_quantity"])

    with pytest.raises(ApiError) as exc_info:
        add_to_cart(user=user, variant_id=variant.id, quantity=1)

    assert exc_info.value.get_codes() == "out_of_stock"
    assert "No hay disponibilidad suficiente para esta variante." in str(exc_info.value.detail)


@pytest.mark.django_db
def test_add_to_cart_out_of_stock_due_to_other_user_reservation(user, other_user, variant):
    variant.stock_quantity = 5
    variant.save(update_fields=["stock_quantity"])

    add_to_cart(user=user, variant_id=variant.id, quantity=4)

    with pytest.raises(ApiError) as exc_info:
        add_to_cart(user=other_user, variant_id=variant.id, quantity=2)

    assert exc_info.value.get_codes() == "out_of_stock"
    assert not CartItem.objects.filter(cart__user=other_user).exists()


@pytest.mark.django_db
def test_add_to_cart_expired_reservation_does_not_block_stock(user, other_user, variant):
    variant.stock_quantity = 2
    variant.save(update_fields=["stock_quantity"])

    item, res = add_to_cart(user=user, variant_id=variant.id, quantity=2)
    res.expires_at = timezone.now() - timedelta(minutes=5)
    res.save(update_fields=["expires_at"])

    item2, res2 = add_to_cart(user=other_user, variant_id=variant.id, quantity=2)
    assert item2.quantity == 2
    assert res2.quantity == 2


@pytest.mark.django_db
def test_add_to_cart_self_reservation_not_counted_against_user(user, variant):
    variant.stock_quantity = 5
    variant.save(update_fields=["stock_quantity"])

    add_to_cart(user=user, variant_id=variant.id, quantity=3)
    item, res = add_to_cart(user=user, variant_id=variant.id, quantity=2)

    assert item.quantity == 5
    assert res.quantity == 5


@pytest.mark.django_db
def test_add_to_cart_self_reservation_exceeding_total_stock_fails(user, variant):
    variant.stock_quantity = 5
    variant.save(update_fields=["stock_quantity"])

    add_to_cart(user=user, variant_id=variant.id, quantity=3)

    with pytest.raises(ApiError) as exc_info:
        add_to_cart(user=user, variant_id=variant.id, quantity=3)

    assert exc_info.value.get_codes() == "out_of_stock"

    item = CartItem.objects.get(cart__user=user, variant=variant)
    assert item.quantity == 3


@pytest.mark.django_db
def test_add_to_cart_missing_variant_raises_validation_error(user):
    with pytest.raises(ValidationError) as exc_info:
        add_to_cart(user=user, variant_id=999999, quantity=1)

    assert "variant_id" in exc_info.value.message_dict
    assert exc_info.value.message_dict["variant_id"] == [
        "La variante de producto especificada no existe."
    ]


@pytest.mark.django_db
def test_add_to_cart_unpublished_product_raises_validation_error(user, product, variant):
    product.status = ProductStatus.DRAFT
    product.save(update_fields=["status"])

    with pytest.raises(ValidationError) as exc_info:
        add_to_cart(user=user, variant_id=variant.id, quantity=1)

    assert "variant_id" in exc_info.value.message_dict
    assert exc_info.value.message_dict["variant_id"] == [
        "El producto no se encuentra disponible para la venta."
    ]


@pytest.mark.django_db
def test_add_to_cart_invalid_quantity_raises_validation_error(user, variant):
    with pytest.raises(ValidationError) as exc_info:
        add_to_cart(user=user, variant_id=variant.id, quantity=0)

    assert "quantity" in exc_info.value.message_dict
    assert exc_info.value.message_dict["quantity"] == ["La cantidad debe ser mayor a cero."]

    with pytest.raises(ValidationError) as exc_info:
        add_to_cart(user=user, variant_id=variant.id, quantity=-3)

    assert "quantity" in exc_info.value.message_dict
