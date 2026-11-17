from datetime import timedelta
from decimal import Decimal

import pytest
from django.db import IntegrityError
from django.utils import timezone

from apps.cart.models import Cart, CartItem, StockReservation
from apps.catalog.models import Category, Product, ProductVariant
from apps.users.models import User


@pytest.fixture
def user(db):
    return User.objects.create(
        clerk_user_id="user_cart_test_123",
        email="shopper@rmshop.co",
        first_name="Comprador",
        last_name="Test",
    )


@pytest.fixture
def product_and_variants(db):
    category = Category.objects.get(slug="camisetas-tops")
    product1 = Product.objects.create(
        name="Camiseta Clásica",
        slug="camiseta-clasica",
        description="Camiseta 100% algodón",
        price=Decimal("45000"),
        material="100% Algodón",
        category=category,
    )
    variant1 = ProductVariant.objects.create(
        product=product1,
        color="Negro",
        size="M",
        stock_quantity=10,
    )
    product2 = Product.objects.create(
        name="Buzo Oversize",
        slug="buzo-oversize",
        description="Buzo cómodo",
        price=Decimal("80000"),
        material="Algodón / Poliéster",
        category=category,
    )
    variant2 = ProductVariant.objects.create(
        product=product2,
        color="Gris",
        size="L",
        stock_quantity=5,
    )
    return (product1, variant1), (product2, variant2)


@pytest.mark.django_db
def test_cart_creation_and_user_relationship(user):
    cart = Cart.objects.create(user=user)
    assert cart.user == user
    assert user.cart == cart
    assert str(cart) == f"Carrito de {user}"

    # OneToOne constraint: second cart for same user must fail
    with pytest.raises(IntegrityError):
        Cart.objects.create(user=user)


@pytest.mark.django_db
def test_cart_cascade_on_user_delete(user):
    cart = Cart.objects.create(user=user)
    cart_id = cart.id
    user.delete()
    assert not Cart.objects.filter(id=cart_id).exists()


@pytest.mark.django_db
def test_cart_item_creation_and_subtotal(user, product_and_variants):
    (_, variant1), _ = product_and_variants
    cart = Cart.objects.create(user=user)

    item = CartItem.objects.create(cart=cart, variant=variant1, quantity=2)
    assert item.cart == cart
    assert item.variant == variant1
    assert item.quantity == 2
    assert item.subtotal == Decimal("90000")
    assert item in cart.items.all()
    assert item in variant1.cart_items.all()


@pytest.mark.django_db
def test_cart_item_unique_cart_variant_constraint(user, product_and_variants):
    (_, variant1), _ = product_and_variants
    cart = Cart.objects.create(user=user)
    CartItem.objects.create(cart=cart, variant=variant1, quantity=1)

    with pytest.raises(IntegrityError):
        CartItem.objects.create(cart=cart, variant=variant1, quantity=2)


@pytest.mark.django_db
def test_cart_item_quantity_must_be_positive(user, product_and_variants):
    (_, variant1), _ = product_and_variants
    cart = Cart.objects.create(user=user)

    with pytest.raises(IntegrityError):
        CartItem.objects.create(cart=cart, variant=variant1, quantity=0)


@pytest.mark.django_db
def test_cart_computed_properties_empty_cart(user):
    cart = Cart.objects.create(user=user)
    assert cart.total_items == 0
    assert cart.total_price == Decimal("0")


@pytest.mark.django_db
def test_cart_computed_properties_with_items(user, product_and_variants):
    (_, variant1), (_, variant2) = product_and_variants
    cart = Cart.objects.create(user=user)

    CartItem.objects.create(cart=cart, variant=variant1, quantity=2)  # 2 * 45000 = 90000
    CartItem.objects.create(cart=cart, variant=variant2, quantity=3)  # 3 * 80000 = 240000

    assert cart.total_items == 5
    assert cart.total_price == Decimal("330000")


@pytest.mark.django_db
def test_stock_reservation_creation_and_relations(user, product_and_variants):
    (_, variant1), _ = product_and_variants
    cart = Cart.objects.create(user=user)
    item = CartItem.objects.create(cart=cart, variant=variant1, quantity=2)

    now = timezone.now()
    expires_at = now + timedelta(minutes=15)
    reservation = StockReservation.objects.create(
        cart_item=item,
        variant=variant1,
        quantity=2,
        expires_at=expires_at,
    )

    assert reservation.cart_item == item
    assert reservation.variant == variant1
    assert reservation.quantity == 2
    assert reservation.expires_at == expires_at
    assert item.reservation == reservation
    assert reservation in variant1.reservations.all()
    assert reservation.is_active() is True


@pytest.mark.django_db
def test_stock_reservation_is_active_expired(user, product_and_variants):
    (_, variant1), _ = product_and_variants
    cart = Cart.objects.create(user=user)
    item = CartItem.objects.create(cart=cart, variant=variant1, quantity=2)

    past = timezone.now() - timedelta(minutes=5)
    reservation = StockReservation.objects.create(
        cart_item=item,
        variant=variant1,
        quantity=2,
        expires_at=past,
    )

    assert reservation.is_active() is False


@pytest.mark.django_db
def test_stock_reservation_quantity_must_be_positive(user, product_and_variants):
    (_, variant1), _ = product_and_variants
    cart = Cart.objects.create(user=user)
    item = CartItem.objects.create(cart=cart, variant=variant1, quantity=1)

    with pytest.raises(IntegrityError):
        StockReservation.objects.create(
            cart_item=item,
            variant=variant1,
            quantity=0,
            expires_at=timezone.now() + timedelta(minutes=15),
        )
