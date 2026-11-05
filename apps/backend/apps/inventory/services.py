from django.core.exceptions import ValidationError
from django.db import transaction

from apps.catalog.models import ProductVariant
from apps.inventory.models import StockMovement
from apps.users.models import User


@transaction.atomic
def adjust_variant_stock(
    *,
    variant_id: int,
    delta: int,
    admin_user: User | None = None,
    reason: str = "Ajuste manual",
    product_id: int | None = None,
) -> tuple[ProductVariant, StockMovement]:
    """Ajusta manualmente el stock de una variante de producto registrando auditoría.

    Reglas de negocio (HU-37):
    - Concurrencia atómica con select_for_update.
    - delta != 0.
    - El stock resultante (stock_quantity + delta) debe ser mayor o igual a 0.
    - Se registra un StockMovement con fecha/hora, usuario admin, delta, resulting_stock y motivo.
    """
    if delta == 0:
        raise ValidationError({"delta": ["El cambio de stock (delta) no puede ser cero."]})

    qs = ProductVariant.objects.select_for_update()
    if product_id is not None:
        qs = qs.filter(product_id=product_id)

    try:
        variant = qs.get(pk=variant_id)
    except ProductVariant.DoesNotExist:
        raise ValidationError(
            {"variant_id": ["La variante de producto especificada no existe."]}
        ) from None

    new_stock = variant.stock_quantity + delta
    if new_stock < 0:
        raise ValidationError(
            {
                "delta": [
                    "El stock resultante no puede ser negativo "
                    f"(actual: {variant.stock_quantity}, cambio: {delta})."
                ]
            }
        )

    variant.stock_quantity = new_stock
    variant.save(update_fields=["stock_quantity", "updated_at"])

    cleaned_reason = reason.strip() if reason else "Ajuste manual"
    if not cleaned_reason:
        cleaned_reason = "Ajuste manual"

    movement = StockMovement.objects.create(
        variant=variant,
        admin=admin_user,
        delta=delta,
        resulting_stock=new_stock,
        reason=cleaned_reason,
    )

    return variant, movement
