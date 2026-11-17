from datetime import timedelta

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models, transaction
from django.utils import timezone

from apps.cart.models import Cart, CartItem, StockReservation
from apps.catalog.models import ProductStatus, ProductVariant
from apps.core.exceptions import ApiError
from apps.users.models import User

RESERVATION_DURATION_MINUTES = 15


def get_available_variant_stock(
    variant: ProductVariant,
    exclude_reservation_id: int | None = None,
) -> int:
    """Calcula el stock disponible para una variante restando las reservas activas.

    Las reservas vencidas (expires_at <= now) no se descuentan.
    Si se pasa exclude_reservation_id, esa reserva no se descuenta (útil para actualizar
    la propia reserva del usuario sin contársela como stock ocupado).
    """
    qs = StockReservation.objects.filter(
        variant=variant,
        expires_at__gt=timezone.now(),
    )
    if exclude_reservation_id is not None:
        qs = qs.exclude(id=exclude_reservation_id)

    total_reserved = qs.aggregate(total=models.Sum("quantity"))["total"] or 0
    return max(0, variant.stock_quantity - total_reserved)


@transaction.atomic
def add_to_cart(
    *,
    user: User,
    variant_id: int,
    quantity: int = 1,
) -> tuple[CartItem, StockReservation]:
    """Agrega una cantidad de una variante al carrito del usuario con reserva atómica de stock.

    Reglas de negocio (HU-13):
    - Concurrencia atómica con select_for_update.
    - La cantidad debe ser mayor o igual a 1.
    - La variante debe existir y su producto estar en estado PUBLISHED.
    - Si el ítem ya existe en el carrito, se incrementa la cantidad acumulada.
    - Se verifica que target_qty <= stock disponible (excluyendo la reserva previa del propio ítem).
    - Si no hay disponibilidad suficiente, levanta ApiError con code='out_of_stock'.
    - Crea o actualiza el CartItem y el StockReservation con vigencia de 15 minutos.
    """
    if quantity < 1:
        raise ValidationError({"quantity": ["La cantidad debe ser mayor a cero."]})

    try:
        variant = (
            ProductVariant.objects.select_for_update(of=("self",))
            .select_related("product")
            .get(id=variant_id)
        )
    except ProductVariant.DoesNotExist:
        raise ValidationError(
            {"variant_id": ["La variante de producto especificada no existe."]}
        ) from None

    if variant.product.status != ProductStatus.PUBLISHED:
        raise ValidationError(
            {"variant_id": ["El producto no se encuentra disponible para la venta."]}
        )

    cart, _ = Cart.objects.get_or_create(user=user)

    cart_item = (
        CartItem.objects.select_related("reservation").filter(cart=cart, variant=variant).first()
    )
    current_qty = cart_item.quantity if cart_item else 0
    try:
        existing_res_id = cart_item.reservation.id if cart_item else None
    except ObjectDoesNotExist:
        existing_res_id = None
    target_qty = current_qty + quantity

    available_stock = get_available_variant_stock(variant, exclude_reservation_id=existing_res_id)
    if target_qty > available_stock:
        raise ApiError(
            detail="No hay disponibilidad suficiente para esta variante.",
            code="out_of_stock",
        )

    if cart_item:
        cart_item.quantity = target_qty
        cart_item.save(update_fields=["quantity", "updated_at"])
    else:
        cart_item = CartItem.objects.create(cart=cart, variant=variant, quantity=target_qty)

    expires_at = timezone.now() + timedelta(minutes=RESERVATION_DURATION_MINUTES)
    reservation, _ = StockReservation.objects.update_or_create(
        cart_item=cart_item,
        defaults={
            "variant": variant,
            "quantity": target_qty,
            "expires_at": expires_at,
        },
    )

    return cart_item, reservation


@transaction.atomic
def remove_from_cart(*, user: User, item_id: int) -> Cart:
    """Elimina un ítem del carrito del usuario y libera su reserva de stock.

    Reglas de negocio (HU-14):
    - Busca el CartItem asegurando pertenencia al carrito del usuario (cart__user=user).
    - Si no existe, lanza CartItem.DoesNotExist.
    - Al eliminar el CartItem, la base de datos elimina por CASCADE la StockReservation asociada,
      liberando inmediatamente el stock para otros clientes.
    - Si la reserva ya expiró, la eliminación procede normalmente sin error (AC-HU-14-2).
    - Retorna la instancia de Cart del usuario.
    """
    try:
        item = (
            CartItem.objects.select_for_update(of=("self", "cart"))
            .select_related("cart")
            .get(id=item_id, cart__user=user)
        )
    except CartItem.DoesNotExist:
        raise CartItem.DoesNotExist(
            f"El ítem #{item_id} no existe en el carrito del usuario."
        ) from None

    cart = item.cart
    item.delete()
    return cart


@transaction.atomic
def update_cart_item_quantity(
    *,
    user: User,
    item_id: int,
    quantity: int,
) -> tuple[CartItem, StockReservation]:
    """Modifica la cantidad de un ítem existente en el carrito del usuario.

    Reglas de negocio (HU-15):
    - La cantidad debe ser mayor o igual a 1 (AC-HU-15-3).
    - Busca el CartItem asegurando pertenencia al carrito del usuario (cart__user=user).
      Si no existe, lanza CartItem.DoesNotExist.
    - Adquiere bloqueo a nivel de fila en la variante con select_for_update(of=("self",)).
    - Calcula el stock disponible para este usuario excluyendo la reserva previa de este ítem
      (get_available_variant_stock(variant, exclude_reservation_id=res_id)).
    - Si quantity > available_stock:
      Lanza ApiError con code='out_of_stock', indicando el máximo disponible
      en el mensaje y en fields["max_available"].
    - Actualiza item.quantity = quantity.
    - Actualiza o crea StockReservation con la nueva cantidad y renueva expires_at a now + 15 min.
    - Retorna (item, reservation).
    """
    if quantity < 1:
        raise ValidationError({"quantity": ["La cantidad debe ser mayor a cero."]})

    # 1. Validación de existencia y lectura de variant_id
    try:
        item_meta = CartItem.objects.values("id", "variant_id").get(id=item_id, cart__user=user)
    except CartItem.DoesNotExist:
        raise CartItem.DoesNotExist(
            f"El ítem #{item_id} no existe en el carrito del usuario."
        ) from None

    # 2. Orden canónico de bloqueo: ProductVariant primero (homólogo a add_to_cart)
    variant = (
        ProductVariant.objects.select_for_update(of=("self",))
        .select_related("product")
        .get(id=item_meta["variant_id"])
    )

    # 3. Bloqueo de CartItem y Cart después
    cart_item = (
        CartItem.objects.select_for_update(of=("self", "cart"))
        .select_related("cart", "variant", "reservation")
        .get(id=item_id, cart__user=user)
    )

    try:
        existing_res_id = cart_item.reservation.id
    except ObjectDoesNotExist:
        existing_res_id = None
    available_stock = get_available_variant_stock(variant, exclude_reservation_id=existing_res_id)

    if quantity > available_stock:
        raise ApiError(
            detail=(
                f"No hay disponibilidad suficiente. "
                f"El stock máximo disponible es {available_stock}."
            ),
            code="out_of_stock",
            fields={"max_available": available_stock},
        )

    cart_item.quantity = quantity
    cart_item.save(update_fields=["quantity", "updated_at"])

    expires_at = timezone.now() + timedelta(minutes=RESERVATION_DURATION_MINUTES)
    reservation, _ = StockReservation.objects.update_or_create(
        cart_item=cart_item,
        defaults={
            "variant": variant,
            "quantity": quantity,
            "expires_at": expires_at,
        },
    )

    return cart_item, reservation
