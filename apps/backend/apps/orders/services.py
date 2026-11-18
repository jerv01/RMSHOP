from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.cart.models import Cart, CartItem
from apps.cart.services import convert_cart_to_sale
from apps.core.exceptions import ApiError
from apps.inventory.services import adjust_variant_stock
from apps.orders.models import Order, OrderItem, OrderStatus, OrderStatusHistory
from apps.shipping.services import get_zone_for_municipality
from apps.users.models import User

# Tiempo que el pedido espera la respuesta del pago con el stock retenido (HU-21, HU-24).
PAYMENT_WINDOW_MINUTES = 30

# Transiciones permitidas. Cualquier otra se rechaza (arquitectura §5, regla de estados).
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    OrderStatus.PENDING_PAYMENT: {
        OrderStatus.PAYMENT_APPROVED,
        OrderStatus.PAYMENT_REJECTED,
        OrderStatus.CANCELLED,
    },
    OrderStatus.PAYMENT_REJECTED: {OrderStatus.CANCELLED},
    OrderStatus.PAYMENT_APPROVED: {OrderStatus.IN_PREPARATION},
    OrderStatus.IN_PREPARATION: {OrderStatus.SHIPPED},
    OrderStatus.SHIPPED: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.CANCELLED: set(),
}

# Estados desde los que se puede cancelar devolviendo el stock retenido.
_CANCELLABLE_STATUSES = {OrderStatus.PENDING_PAYMENT, OrderStatus.PAYMENT_REJECTED}


def lock_order(order: Order) -> Order:
    """Vuelve a leer el pedido con bloqueo de fila; debe llamarse dentro de una transacción."""
    return Order.objects.select_for_update(of=("self",)).get(pk=order.pk)


@transaction.atomic
def change_order_status(
    *,
    order: Order,
    to_status: str,
    changed_by: User | None = None,
    note: str = "",
) -> Order:
    """Único punto de cambio de estado de un pedido.

    Reglas de negocio (arquitectura §5):
    - Bloquea la fila del pedido para serializar cambios concurrentes (pasarela, cliente, cron).
    - Solo permite las transiciones de ALLOWED_TRANSITIONS; si no, lanza
      ApiError(invalid_status_transition).
    - Registra el cambio en OrderStatusHistory (changed_by nulo = sistema).
    """
    order = lock_order(order)
    from_status = order.status
    if to_status not in ALLOWED_TRANSITIONS.get(from_status, set()):
        raise ApiError(
            detail=(
                f"El pedido {order.order_number} no puede pasar de "
                f"«{OrderStatus(from_status).label}» a «{OrderStatus(to_status).label}»."
            ),
            code="invalid_status_transition",
        )

    order.status = to_status
    order.save(update_fields=["status", "updated_at"])
    OrderStatusHistory.objects.create(
        order=order,
        from_status=from_status,
        to_status=to_status,
        changed_by=changed_by,
        note=note[:255],
    )
    return order


@transaction.atomic
def create_order_from_cart(
    *,
    user: User,
    municipality: str,
    address_line: str,
    recipient_name: str,
    phone: str,
) -> Order:
    """Crea el pedido a partir del carrito del cliente al iniciar el pago (HU-21).

    Checkout mínimo provisional mientras no existan la HU de checkout ni HU-25/HU-26.

    Reglas de negocio:
    - El carrito no puede estar vacío: ApiError(empty_cart).
    - El municipio debe tener cobertura: ApiError(municipality_not_covered).
    - Los ítems se copian con el precio actual del producto (HU-16) y total = subtotal + envío.
    - El pedido nace en «Pendiente de Pago» con su primera entrada de historial.
    - Las reservas del carrito se convierten en venta (descuento de stock con StockMovement), así
      el stock queda retenido mientras se espera el pago. Si alguna reserva expiró,
      convert_cart_to_sale lanza ApiError y toda la transacción se revierte.
    """
    zone = get_zone_for_municipality(municipality=municipality)

    cart = Cart.objects.select_for_update(of=("self",)).filter(user=user).first()
    items = (
        list(
            CartItem.objects.filter(cart=cart)
            .select_related("variant__product")
            .order_by("variant_id")
        )
        if cart
        else []
    )
    if not items:
        raise ApiError(
            detail="Tu carrito está vacío. Agrega productos antes de pagar.",
            code="empty_cart",
        )

    subtotal = sum((item.variant.product.price * item.quantity for item in items), Decimal("0"))
    shipping_cost = zone.fee
    order = Order.objects.create(
        user=user,
        status=OrderStatus.PENDING_PAYMENT,
        subtotal=subtotal,
        shipping_cost=shipping_cost,
        total=subtotal + shipping_cost,
        municipality=zone.municipality,
        address_line=address_line.strip(),
        recipient_name=recipient_name.strip(),
        phone=phone.strip(),
        payment_expires_at=timezone.now() + timedelta(minutes=PAYMENT_WINDOW_MINUTES),
    )
    order.order_number = f"RM-{order.pk:06d}"
    order.save(update_fields=["order_number"])

    OrderItem.objects.bulk_create(
        [
            OrderItem(
                order=order,
                variant=item.variant,
                product_name=item.variant.product.name,
                color=item.variant.color,
                size=item.variant.size,
                unit_price=item.variant.product.price,
                quantity=item.quantity,
                subtotal=item.variant.product.price * item.quantity,
            )
            for item in items
        ]
    )
    OrderStatusHistory.objects.create(
        order=order,
        from_status="",
        to_status=OrderStatus.PENDING_PAYMENT,
        changed_by=user,
        note="Pedido creado al iniciar el pago.",
    )

    convert_cart_to_sale(cart=cart, order_reference=order.order_number)
    return order


@transaction.atomic
def cancel_order(*, order: Order, changed_by: User | None = None, note: str = "") -> Order:
    """Cancela un pedido sin pago aprobado y devuelve su stock retenido exactamente una vez.

    Reglas de negocio (HU-20 AC-2, base para HU-23/HU-24):
    - Solo desde «Pendiente de Pago» o «Pago rechazado»; si el pedido ya está cancelado no hace
      nada (idempotente), y desde otros estados lanza ApiError(order_not_cancellable).
    - La transición se hace con el pedido bloqueado, así dos cancelaciones simultáneas no
      devuelven el stock dos veces.
    """
    order = lock_order(order)
    if order.status == OrderStatus.CANCELLED:
        return order
    if order.status not in _CANCELLABLE_STATUSES:
        raise ApiError(
            detail=f"El pedido {order.order_number} ya no se puede cancelar.",
            code="order_not_cancellable",
        )

    order = change_order_status(
        order=order, to_status=OrderStatus.CANCELLED, changed_by=changed_by, note=note
    )
    for item in order.items.filter(variant__isnull=False).order_by("variant_id"):
        adjust_variant_stock(
            variant_id=item.variant_id,
            delta=item.quantity,
            admin_user=None,
            reason=f"Devolución pedido {order.order_number}",
        )
    return order


@transaction.atomic
def approve_order_payment(*, order: Order, note: str = "") -> Order:
    """Marca el pedido como «Pago aprobado» (HU-19 AC-1, HU-20 AC-1).

    Idempotente: si el pedido ya está aprobado no hace nada. El stock ya se descontó al crear
    el pedido, así que no hay movimiento de inventario aquí.
    """
    order = lock_order(order)
    if order.status == OrderStatus.PAYMENT_APPROVED:
        return order
    return change_order_status(order=order, to_status=OrderStatus.PAYMENT_APPROVED, note=note)


@transaction.atomic
def reject_order_payment(*, order: Order, note: str = "") -> Order:
    """Registra el rechazo del pago y cancela el pedido devolviendo el stock (HU-20 AC-2).

    Queda «Pago rechazado» y luego «Cancelado» en el historial. Idempotente: si el pedido ya
    está rechazado o cancelado no se repite nada.
    """
    order = lock_order(order)
    if order.status == OrderStatus.PENDING_PAYMENT:
        order = change_order_status(order=order, to_status=OrderStatus.PAYMENT_REJECTED, note=note)
    if order.status == OrderStatus.PAYMENT_REJECTED:
        order = cancel_order(order=order, note="Cancelado por pago rechazado.")
    return order
