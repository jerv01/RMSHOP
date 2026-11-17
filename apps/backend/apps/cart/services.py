from datetime import timedelta

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models, transaction
from django.utils import timezone

from apps.cart.models import Cart, CartItem, StockReservation
from apps.catalog.models import ProductStatus, ProductVariant
from apps.core.exceptions import ApiError
from apps.inventory.models import StockMovement
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
        CartItem.objects.select_for_update(of=("self",))
        .select_related("reservation")
        .filter(cart=cart, variant=variant)
        .first()
    )

    existing_res_id = None
    has_active_reservation = False
    if cart_item is not None:
        try:
            existing_res = cart_item.reservation
            existing_res_id = existing_res.id
            has_active_reservation = existing_res.is_active()
        except ObjectDoesNotExist:
            existing_res_id = None

    # Si el ítem previo en el carrito ya había expirado, no arrastramos su cantidad fantasma
    current_qty = cart_item.quantity if (cart_item and has_active_reservation) else 0
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


@transaction.atomic
def convert_reservation_to_sale(
    *,
    reservation_id: int | None = None,
    reservation: StockReservation | None = None,
    admin_user: User | None = None,
    order_reference: str = "",
) -> StockMovement:
    """Convierte una reserva activa en una venta definitiva descontando stock físico (AC-HU-17-3).

    Reglas de negocio (HU-17 y HU-37):
    - Concurrencia atómica con select_for_update en ProductVariant.
    - Valida que la reserva exista y esté activa (expires_at > now). Si expiró,
      lanza ApiError(code="reservation_expired").
    - Descuenta reservation.quantity del stock_quantity físico de la variante.
    - Crea un StockMovement de auditoría con delta negativo y motivo de venta (HU-37).
    - Elimina la reserva de stock y el CartItem asociado (el stock no se libera, se consolida).
    - Retorna la instancia de StockMovement creada.
    """
    if reservation is None and reservation_id is None:
        raise ValueError("Se debe proporcionar reservation o reservation_id.")

    res_id = reservation.id if reservation is not None else reservation_id

    # 1. Obtener variant_id de la reserva
    try:
        res_meta = StockReservation.objects.values("id", "variant_id").get(id=res_id)
    except StockReservation.DoesNotExist:
        raise StockReservation.DoesNotExist(f"La reserva #{res_id} no existe.") from None

    # 2. Bloqueo canónico de fila en ProductVariant
    variant = ProductVariant.objects.select_for_update(of=("self",)).get(id=res_meta["variant_id"])

    # 3. Bloqueo de la reserva y CartItem
    active_res = (
        StockReservation.objects.select_for_update(of=("self", "cart_item"))
        .select_related("cart_item")
        .get(id=res_id)
    )

    if not active_res.is_active():
        raise ApiError(
            detail="La reserva de stock ha expirado y no puede convertirse en venta.",
            code="reservation_expired",
        )

    if variant.stock_quantity < active_res.quantity:
        raise ApiError(
            detail="Inconsistencia de stock al procesar la venta.",
            code="insufficient_stock",
        )

    new_stock = variant.stock_quantity - active_res.quantity
    variant.stock_quantity = new_stock
    variant.save(update_fields=["stock_quantity", "updated_at"])

    reason_str = (
        f"Venta checkout {order_reference}".strip() if order_reference else "Venta checkout pedido"
    )
    movement = StockMovement.objects.create(
        variant=variant,
        admin=admin_user,
        delta=-active_res.quantity,
        resulting_stock=new_stock,
        reason=reason_str,
    )

    cart_item = active_res.cart_item
    active_res.delete()
    if cart_item:
        cart_item.delete()

    return movement


@transaction.atomic
def convert_cart_to_sale(
    *,
    cart: Cart,
    admin_user: User | None = None,
    order_reference: str = "",
) -> list[StockMovement]:
    """Convierte todas las reservas activas de un carrito en ventas definitivas (AC-HU-17-3).

    Reglas de negocio (HU-17 y HU-37):
    - Bloqueo en orden canónico por variant_id ascendente para prevenir deadlocks.
    - Re-consulta y bloqueo de CartItem y StockReservation DESPUÉS de bloquear ProductVariant
      para prevenir race conditions / double-spend ante checkouts concurrentes.
    - Valida que todas las reservas del carrito sigan activas. Si alguna expiró,
      lanza ApiError(code="reservation_expired").
    - Descuenta el stock físico de cada variante y genera su correspondiente StockMovement.
    - Elimina reservas y vacía los ítems correspondientes del carrito.
    - Retorna la lista de StockMovement creados.
    """
    # 1. Identificar las variantes del carrito en orden determinista para el bloqueo canónico
    initial_variant_ids = sorted(
        set(CartItem.objects.filter(cart=cart).values_list("variant_id", flat=True))
    )
    if not initial_variant_ids:
        return []

    # 2. Bloquear primero ProductVariant en orden ascendente de ID (previene deadlocks AB-BA)
    variants = {
        v.id: v
        for v in ProductVariant.objects.select_for_update(of=("self",))
        .filter(id__in=initial_variant_ids)
        .order_by("id")
    }

    # 3. CRÍTICO: Re-consultar y bloquear CartItem + StockReservation
    # DESPUÉS de bloquear las variantes para evitar snapshots obsoletos en memoria.
    items = list(
        CartItem.objects.select_for_update(of=("self",))
        .filter(cart=cart)
        .select_related("reservation", "variant")
        .order_by("variant_id")
    )
    if not items:
        return []

    # Si se agregó una variante nueva al carrito entre el paso 1 y el paso 3, adquirir su lock
    missing_variant_ids = sorted(
        {item.variant_id for item in items if item.variant_id not in variants}
    )
    if missing_variant_ids:
        for v in (
            ProductVariant.objects.select_for_update(of=("self",))
            .filter(id__in=missing_variant_ids)
            .order_by("id")
        ):
            variants[v.id] = v

    now = timezone.now()
    for item in items:
        try:
            res = item.reservation
        except ObjectDoesNotExist:
            raise ApiError(
                detail=f"El ítem #{item.id} no posee una reserva activa.",
                code="reservation_missing",
            ) from None
        if res.expires_at <= now:
            raise ApiError(
                detail=f"La reserva para la variante {item.variant} ha expirado.",
                code="reservation_expired",
            )
        variant = variants[item.variant_id]
        if variant.stock_quantity < res.quantity:
            raise ApiError(
                detail=f"Inconsistencia de stock al procesar la variante {variant}.",
                code="insufficient_stock",
            )

    movements = []
    reason_str = (
        f"Venta checkout {order_reference}".strip() if order_reference else "Venta checkout pedido"
    )

    for item in items:
        res = item.reservation
        variant = variants[item.variant_id]
        new_stock = variant.stock_quantity - res.quantity
        variant.stock_quantity = new_stock
        variant.save(update_fields=["stock_quantity", "updated_at"])

        movement = StockMovement.objects.create(
            variant=variant,
            admin=admin_user,
            delta=-res.quantity,
            resulting_stock=new_stock,
            reason=reason_str,
        )
        movements.append(movement)

        # item.delete() elimina en cascada StockReservation por OneToOneField(on_delete=CASCADE)
        item.delete()

    return movements
