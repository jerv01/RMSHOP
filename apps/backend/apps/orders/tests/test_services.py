from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.cart.models import CartItem, StockReservation
from apps.core.exceptions import ApiError
from apps.inventory.models import StockMovement
from apps.orders.models import Order, OrderStatus
from apps.orders.services import (
    PAYMENT_WINDOW_MINUTES,
    approve_order_payment,
    cancel_order,
    change_order_status,
    create_order_from_cart,
    reject_order_payment,
)

pytestmark = pytest.mark.django_db


def _create(customer, **overrides):
    data = {
        "municipality": "Cali",
        "address_line": "Calle 10 # 20-30",
        "recipient_name": "Ana Pérez",
        "phone": "3001234567",
    }
    data.update(overrides)
    return create_order_from_cart(user=customer, **data)


def test_create_order_snapshots_items_totals_and_retains_stock(customer, variant, cart_with_item):
    before = timezone.now()
    order = _create(customer)

    assert order.order_number == f"RM-{order.pk:06d}"
    assert order.status == OrderStatus.PENDING_PAYMENT
    assert order.subtotal == Decimal("100000")
    assert order.shipping_cost == Decimal("5000")
    assert order.total == order.subtotal + order.shipping_cost
    assert order.municipality == "Cali"
    expected_expiry = before + timedelta(minutes=PAYMENT_WINDOW_MINUTES)
    assert abs((order.payment_expires_at - expected_expiry).total_seconds()) < 5

    item = order.items.get()
    assert (item.product_name, item.color, item.size) == ("Camiseta Pedido", "Negro", "M")
    assert (item.unit_price, item.quantity, item.subtotal) == (
        Decimal("50000"),
        2,
        Decimal("100000"),
    )

    history = list(order.status_history.all())
    assert [(h.from_status, h.to_status) for h in history] == [("", OrderStatus.PENDING_PAYMENT)]

    # Stock retenido: se descontó del físico y el carrito quedó vacío.
    variant.refresh_from_db()
    assert variant.stock_quantity == 3
    assert not CartItem.objects.filter(cart=cart_with_item).exists()
    assert StockMovement.objects.filter(
        variant=variant, delta=-2, reason=f"Venta checkout {order.order_number}"
    ).exists()


def test_shipping_fee_depends_on_municipality(customer, cart_with_item):
    order = _create(customer, municipality="  JAMUNDI ")
    assert order.shipping_cost == Decimal("10000")
    assert order.municipality == "Jamundí"


def test_empty_cart_is_rejected(customer):
    with pytest.raises(ApiError) as exc:
        _create(customer)
    assert exc.value.get_codes() == "empty_cart"
    assert not Order.objects.exists()


def test_uncovered_municipality_is_rejected(customer, variant, cart_with_item):
    with pytest.raises(ApiError) as exc:
        _create(customer, municipality="Bogotá")
    assert exc.value.get_codes() == "municipality_not_covered"
    assert not Order.objects.exists()
    variant.refresh_from_db()
    assert variant.stock_quantity == 5


def test_expired_reservation_rolls_back_everything(customer, variant, cart_with_item):
    StockReservation.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
    with pytest.raises(ApiError) as exc:
        _create(customer)
    assert exc.value.get_codes() == "reservation_expired"
    assert not Order.objects.exists()
    variant.refresh_from_db()
    assert variant.stock_quantity == 5
    assert CartItem.objects.filter(cart=cart_with_item).exists()


def test_invalid_transition_is_rejected(customer, cart_with_item):
    order = _create(customer)
    with pytest.raises(ApiError) as exc:
        change_order_status(order=order, to_status=OrderStatus.DELIVERED)
    assert exc.value.get_codes() == "invalid_status_transition"
    order.refresh_from_db()
    assert order.status == OrderStatus.PENDING_PAYMENT


def test_cancel_returns_stock_exactly_once(customer, variant, cart_with_item):
    order = _create(customer)
    cancel_order(order=order, note="Prueba")
    cancel_order(order=order, note="Prueba repetida")

    order.refresh_from_db()
    variant.refresh_from_db()
    assert order.status == OrderStatus.CANCELLED
    assert variant.stock_quantity == 5
    assert (
        StockMovement.objects.filter(reason=f"Devolución pedido {order.order_number}").count() == 1
    )


def test_cancel_approved_order_is_not_allowed(customer, cart_with_item):
    order = _create(customer)
    approve_order_payment(order=order)
    with pytest.raises(ApiError) as exc:
        cancel_order(order=order)
    assert exc.value.get_codes() == "order_not_cancellable"


def test_approve_is_idempotent(customer, cart_with_item):
    order = _create(customer)
    approve_order_payment(order=order)
    approve_order_payment(order=order)
    order.refresh_from_db()
    assert order.status == OrderStatus.PAYMENT_APPROVED
    assert order.status_history.filter(to_status=OrderStatus.PAYMENT_APPROVED).count() == 1


def test_reject_records_both_states_and_restocks_once(customer, variant, cart_with_item):
    order = _create(customer)
    reject_order_payment(order=order, note="Rechazado por el banco")
    reject_order_payment(order=order, note="Notificación duplicada")

    order.refresh_from_db()
    variant.refresh_from_db()
    assert order.status == OrderStatus.CANCELLED
    assert [h.to_status for h in order.status_history.all()] == [
        OrderStatus.PENDING_PAYMENT,
        OrderStatus.PAYMENT_REJECTED,
        OrderStatus.CANCELLED,
    ]
    assert variant.stock_quantity == 5
