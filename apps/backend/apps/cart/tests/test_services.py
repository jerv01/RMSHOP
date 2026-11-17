from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.utils import timezone

from apps.cart.models import Cart, CartItem, StockReservation
from apps.cart.services import (
    RESERVATION_DURATION_MINUTES,
    add_to_cart,
    convert_cart_to_sale,
    convert_reservation_to_sale,
    get_available_variant_stock,
    re_reserve_cart_item,
    release_expired_reservations,
    remove_from_cart,
    update_cart_item_quantity,
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


@pytest.fixture
def variant2(db, product):
    return ProductVariant.objects.create(
        product=product,
        color="Blanco",
        size="L",
        stock_quantity=8,
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


@pytest.mark.django_db
@pytest.mark.parametrize("status_value", [ProductStatus.DRAFT, ProductStatus.ARCHIVED])
def test_add_to_cart_non_published_statuses_raise_validation_error(
    user, product, variant, status_value
):
    """Tanto DRAFT como ARCHIVED deben ser rechazados."""
    product.status = status_value
    product.save(update_fields=["status"])

    with pytest.raises(ValidationError) as exc_info:
        add_to_cart(user=user, variant_id=variant.id, quantity=1)

    assert "variant_id" in exc_info.value.message_dict


@pytest.mark.django_db(transaction=True)
def test_add_to_cart_concurrent_threads_race_condition(product, category):
    """Argon Recommendation: Prueba de concurrencia real multi-hilo en PostgreSQL.

    Dos clientes concurrentes intentan tomar la última unidad en stock al mismo tiempo.
    select_for_update() asegura que exactamente 1 cliente tiene éxito y el otro recibe out_of_stock.
    """
    from concurrent.futures import ThreadPoolExecutor

    from django.db import connection

    # Crear variante con stock 1
    variant_single = ProductVariant.objects.create(
        product=product,
        color="Rojo",
        size="XL",
        stock_quantity=1,
    )

    user_a = User.objects.create(
        clerk_user_id="race_user_a",
        email="race_a@rmshop.co",
        first_name="Race",
        last_name="A",
    )
    user_b = User.objects.create(
        clerk_user_id="race_user_b",
        email="race_b@rmshop.co",
        first_name="Race",
        last_name="B",
    )

    results = []

    def attempt_add(u):
        try:
            item, res = add_to_cart(user=u, variant_id=variant_single.id, quantity=1)
            results.append(("SUCCESS", u.id, item.id, res.id))
        except ApiError as e:
            results.append(("OUT_OF_STOCK", u.id, getattr(e.detail, "code", str(e))))
        except Exception as e:
            results.append(("ERROR", u.id, str(e)))
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(attempt_add, user_a), executor.submit(attempt_add, user_b)]
        for f in futures:
            f.result()

    successes = [r for r in results if r[0] == "SUCCESS"]
    out_of_stocks = [r for r in results if r[0] == "OUT_OF_STOCK"]

    assert len(successes) == 1, f"Exactamente 1 intento debe tener éxito, obtenido: {results}"
    assert len(out_of_stocks) == 1, (
        f"Exactamente 1 intento debe ser rechazado por stock, obtenido: {results}"
    )
    assert out_of_stocks[0][2] == "out_of_stock"

    # Verificar que solo hay 1 reserva registrada en base de datos
    assert StockReservation.objects.filter(variant=variant_single).count() == 1


# ============================================================================
# HU-14: Pruebas unitarias de remove_from_cart
# ============================================================================


@pytest.mark.django_db
def test_remove_from_cart_success(user, variant, variant2):
    """Eliminar un ítem de dos deja 1 ítem y libera el stock del ítem eliminado inmediatamente."""
    item1, res1 = add_to_cart(user=user, variant_id=variant.id, quantity=3)
    item2, res2 = add_to_cart(user=user, variant_id=variant2.id, quantity=2)

    assert get_available_variant_stock(variant) == 7
    assert get_available_variant_stock(variant2) == 6

    cart = remove_from_cart(user=user, item_id=item1.id)

    assert cart.items.count() == 1
    assert cart.items.first().id == item2.id
    assert not CartItem.objects.filter(id=item1.id).exists()
    assert not StockReservation.objects.filter(id=res1.id).exists()

    # El stock del ítem eliminado se libera inmediatamente
    assert get_available_variant_stock(variant) == 10
    # El stock del otro ítem permanece reservado
    assert get_available_variant_stock(variant2) == 6


@pytest.mark.django_db
def test_remove_from_cart_expired_reservation(user, variant):
    """Eliminar un ítem con reserva ya expirada procede sin errores (AC-HU-14-2)."""
    item, res = add_to_cart(user=user, variant_id=variant.id, quantity=2)
    res.expires_at = timezone.now() - timedelta(minutes=5)
    res.save(update_fields=["expires_at"])

    assert res.is_active() is False

    cart = remove_from_cart(user=user, item_id=item.id)

    assert cart.items.count() == 0
    assert not CartItem.objects.filter(id=item.id).exists()
    assert not StockReservation.objects.filter(id=res.id).exists()
    assert get_available_variant_stock(variant) == 10


@pytest.mark.django_db
def test_remove_from_cart_last_item(user, variant):
    """Eliminar el único ítem deja el carrito vacío y totales en cero."""
    item, _ = add_to_cart(user=user, variant_id=variant.id, quantity=4)

    cart = remove_from_cart(user=user, item_id=item.id)

    assert cart.items.count() == 0
    assert cart.total_items == 0
    assert cart.total_price == Decimal("0")


@pytest.mark.django_db
def test_remove_from_cart_nonexistent_item_raises_does_not_exist(user):
    """Intentar eliminar un ítem inexistente lanza CartItem.DoesNotExist."""
    with pytest.raises(CartItem.DoesNotExist) as exc_info:
        remove_from_cart(user=user, item_id=999999)

    assert "999999" in str(exc_info.value)


@pytest.mark.django_db
def test_remove_from_cart_item_of_other_user_raises_does_not_exist(user, other_user, variant):
    """Un usuario no puede eliminar ítems de otro usuario (lanza DoesNotExist)."""
    item, res = add_to_cart(user=other_user, variant_id=variant.id, quantity=2)

    with pytest.raises(CartItem.DoesNotExist):
        remove_from_cart(user=user, item_id=item.id)

    # El ítem y reserva del otro usuario permanecen intactos
    assert CartItem.objects.filter(id=item.id).exists()
    assert StockReservation.objects.filter(id=res.id).exists()


@pytest.mark.django_db
def test_remove_from_cart_when_reservation_already_purged(user, variant):
    """Argon Edge Case: Si una tarea de limpieza previa ya purgó la StockReservation,

    remove_from_cart aún debe eliminar el CartItem limpiamente sin fallar.
    """
    item, res = add_to_cart(user=user, variant_id=variant.id, quantity=1)
    res.delete()  # Simular purga física previa

    cart = remove_from_cart(user=user, item_id=item.id)
    assert not CartItem.objects.filter(id=item.id).exists()
    assert cart.items.count() == 0


# ============================================================================
# HU-15: Pruebas unitarias de update_cart_item_quantity
# ============================================================================


@pytest.mark.django_db
def test_update_cart_item_quantity_happy_path(user, variant):
    """AC-HU-15-1: Aumentar cantidad dentro del stock disponible.

    Actualiza ítem, reserva y totales.
    """
    variant.stock_quantity = 5
    variant.save(update_fields=["stock_quantity"])

    item, res = add_to_cart(user=user, variant_id=variant.id, quantity=1)
    old_expires_at = res.expires_at

    updated_item, updated_res = update_cart_item_quantity(user=user, item_id=item.id, quantity=3)

    assert updated_item.id == item.id
    assert updated_item.quantity == 3
    assert updated_res.id == res.id
    assert updated_res.quantity == 3
    assert updated_res.expires_at >= old_expires_at

    expected_expiry = timezone.now() + timedelta(minutes=RESERVATION_DURATION_MINUTES)
    assert abs((updated_res.expires_at - expected_expiry).total_seconds()) < 5

    # Stock disponible ahora debe ser 5 - 3 = 2
    assert get_available_variant_stock(variant) == 2

    # Verificar totales del carrito
    cart = Cart.objects.get(user=user)
    assert cart.total_items == 3
    assert cart.total_price == Decimal("50000") * 3


@pytest.mark.django_db
def test_update_cart_item_quantity_decrease(user, variant):
    """Disminuir cantidad actualiza ítem y reserva, liberando el stock excedente."""
    variant.stock_quantity = 5
    variant.save(update_fields=["stock_quantity"])

    item, _ = add_to_cart(user=user, variant_id=variant.id, quantity=3)
    assert get_available_variant_stock(variant) == 2

    updated_item, updated_res = update_cart_item_quantity(user=user, item_id=item.id, quantity=1)

    assert updated_item.quantity == 1
    assert updated_res.quantity == 1
    # Stock disponible ahora es 5 - 1 = 4 (se liberaron 2 unidades)
    assert get_available_variant_stock(variant) == 4

    cart = Cart.objects.get(user=user)
    assert cart.total_items == 1
    assert cart.total_price == Decimal("50000")


@pytest.mark.django_db
def test_update_cart_item_quantity_exceeds_stock(user, variant):
    """AC-HU-15-2: Cantidad mayor a disponible lanza ApiError.

    Debe tener code='out_of_stock' y fields['max_available'].
    """
    variant.stock_quantity = 3
    variant.save(update_fields=["stock_quantity"])

    item, _ = add_to_cart(user=user, variant_id=variant.id, quantity=1)

    with pytest.raises(ApiError) as exc_info:
        update_cart_item_quantity(user=user, item_id=item.id, quantity=4)

    err = exc_info.value
    assert err.get_codes() == "out_of_stock"
    assert "stock máximo disponible es 3" in str(err.detail)
    assert err.fields.get("max_available") == 3

    # La cantidad en BD permanece intacta (1)
    item.refresh_from_db()
    assert item.quantity == 1
    assert get_available_variant_stock(variant) == 2


@pytest.mark.django_db
def test_update_cart_item_quantity_invalid_quantity(user, variant):
    """AC-HU-15-3: Cantidad 0 o negativa lanza ValidationError y no muta el ítem."""
    item, _ = add_to_cart(user=user, variant_id=variant.id, quantity=2)

    with pytest.raises(ValidationError) as exc_info:
        update_cart_item_quantity(user=user, item_id=item.id, quantity=0)
    assert "quantity" in exc_info.value.message_dict
    assert exc_info.value.message_dict["quantity"] == ["La cantidad debe ser mayor a cero."]

    with pytest.raises(ValidationError) as exc_info:
        update_cart_item_quantity(user=user, item_id=item.id, quantity=-2)
    assert "quantity" in exc_info.value.message_dict

    item.refresh_from_db()
    assert item.quantity == 2


@pytest.mark.django_db
def test_update_cart_item_quantity_nonexistent_item(user):
    """ID inexistente lanza CartItem.DoesNotExist."""
    with pytest.raises(CartItem.DoesNotExist) as exc_info:
        update_cart_item_quantity(user=user, item_id=999999, quantity=2)

    assert "999999" in str(exc_info.value)


@pytest.mark.django_db
def test_update_cart_item_quantity_item_of_other_user(user, other_user, variant):
    """Ítem de otro usuario lanza CartItem.DoesNotExist y no se muta."""
    item, res = add_to_cart(user=other_user, variant_id=variant.id, quantity=2)

    with pytest.raises(CartItem.DoesNotExist):
        update_cart_item_quantity(user=user, item_id=item.id, quantity=5)

    item.refresh_from_db()
    res.refresh_from_db()
    assert item.quantity == 2
    assert res.quantity == 2


@pytest.mark.django_db
def test_update_cart_item_quantity_when_reservation_was_deleted_or_expired(user, variant):
    """Argon Edge Case: Si la reserva previa fue eliminada o expiró,

    update_cart_item_quantity no lanza DoesNotExist, recrea la reserva y renueva expires_at.
    """
    item, res = add_to_cart(user=user, variant_id=variant.id, quantity=1)
    res.delete()  # Simular purga física previa

    updated_item, new_res = update_cart_item_quantity(user=user, item_id=item.id, quantity=2)
    assert updated_item.quantity == 2
    assert new_res.quantity == 2
    assert new_res.is_active() is True


@pytest.mark.django_db
def test_update_cart_item_quantity_accounts_for_other_users_active_reservations(
    user, other_user, variant
):
    """Argon Edge Case: Stock = 5. Usuario A tiene 2, Usuario B tiene 2.

    Usuario A intenta subir a 4: debe fallar porque el stock disponible para A es 3 (5 - 2 de B).
    """
    variant.stock_quantity = 5
    variant.save(update_fields=["stock_quantity"])

    item_a, _ = add_to_cart(user=user, variant_id=variant.id, quantity=2)
    add_to_cart(user=other_user, variant_id=variant.id, quantity=2)

    with pytest.raises(ApiError) as exc_info:
        update_cart_item_quantity(user=user, item_id=item_a.id, quantity=4)

    err = exc_info.value
    assert err.get_codes() == "out_of_stock"
    assert err.fields.get("max_available") == 3
    assert "stock máximo disponible es 3" in str(err.detail)


@pytest.mark.django_db
def test_update_cart_item_quantity_same_value_renews_expiration(user, variant):
    """Argon Edge Case: Si se envía la misma cantidad, es idempotente y renueva expires_at."""
    item, res = add_to_cart(user=user, variant_id=variant.id, quantity=2)
    original_expires = res.expires_at

    # Adelantar el tiempo 5 minutos
    future_now = timezone.now() + timedelta(minutes=5)
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(timezone, "now", lambda: future_now)
        updated_item, updated_res = update_cart_item_quantity(
            user=user, item_id=item.id, quantity=2
        )

        assert updated_item.quantity == 2
        assert updated_res.quantity == 2
        assert updated_res.expires_at > original_expires


# ============================================================================
# HU-17: Pruebas unitarias de convert_reservation_to_sale y convert_cart_to_sale
# ============================================================================


@pytest.mark.django_db
def test_convert_reservation_to_sale_by_id(user, variant):
    """Conversión pasando reservation_id."""
    item, res = add_to_cart(user=user, variant_id=variant.id, quantity=2)
    initial_stock = variant.stock_quantity

    movement = convert_reservation_to_sale(reservation_id=res.id, order_reference="REF-001")

    assert movement.delta == -2
    assert movement.resulting_stock == initial_stock - 2
    assert "REF-001" in movement.reason
    variant.refresh_from_db()
    assert variant.stock_quantity == initial_stock - 2
    assert not StockReservation.objects.filter(id=res.id).exists()
    assert not CartItem.objects.filter(id=item.id).exists()


@pytest.mark.django_db
def test_convert_reservation_to_sale_missing_args():
    """Llamar sin reservation ni reservation_id lanza ValueError."""
    with pytest.raises(ValueError) as exc:
        convert_reservation_to_sale()
    assert "Se debe proporcionar reservation o reservation_id" in str(exc.value)


@pytest.mark.django_db
def test_convert_reservation_to_sale_nonexistent():
    """ID de reserva inexistente lanza StockReservation.DoesNotExist."""
    with pytest.raises(StockReservation.DoesNotExist):
        convert_reservation_to_sale(reservation_id=999999)


@pytest.mark.django_db
def test_convert_cart_to_sale_empty_cart(user):
    """Convertir un carrito vacío retorna lista vacía sin error."""
    cart, _ = Cart.objects.get_or_create(user=user)
    movements = convert_cart_to_sale(cart=cart)
    assert movements == []


@pytest.mark.django_db
def test_convert_cart_to_sale_item_missing_reservation_raises_api_error(user, variant):
    """Si un ítem del carrito no posee reserva asociada, se detecta y lanza reservation_missing."""
    cart, _ = Cart.objects.get_or_create(user=user)
    CartItem.objects.create(cart=cart, variant=variant, quantity=1)

    with pytest.raises(ApiError) as exc_info:
        convert_cart_to_sale(cart=cart)

    assert exc_info.value.get_codes() == "reservation_missing"


# ============================================================================
# HU-18: Pruebas unitarias de release_expired_reservations y re_reserve_cart_item
# ============================================================================


@pytest.mark.django_db
def test_release_expired_reservations_keeps_cart_items_by_default(user, variant):
    """Por defecto, release_expired_reservations elimina la reserva y preserva el CartItem."""
    item, res = add_to_cart(user=user, variant_id=variant.id, quantity=2)
    # Forzar expiración
    res.expires_at = timezone.now() - timedelta(seconds=1)
    res.save()

    count = release_expired_reservations(delete_cart_items=False)

    assert count == 1
    assert not StockReservation.objects.filter(id=res.id).exists()
    assert CartItem.objects.filter(id=item.id).exists()


@pytest.mark.django_db
def test_release_expired_reservations_removes_cart_items_when_requested(user, variant):
    """Con delete_cart_items=True, se eliminan también los CartItems asociados."""
    item, res = add_to_cart(user=user, variant_id=variant.id, quantity=1)
    res.expires_at = timezone.now() - timedelta(seconds=1)
    res.save()

    count = release_expired_reservations(delete_cart_items=True)

    assert count == 1
    assert not StockReservation.objects.filter(id=res.id).exists()
    assert not CartItem.objects.filter(id=item.id).exists()


@pytest.mark.django_db
def test_release_expired_reservations_ignores_active(user, variant):
    """Las reservas activas no son afectadas por la liberación."""
    item, res = add_to_cart(user=user, variant_id=variant.id, quantity=1)

    count = release_expired_reservations(delete_cart_items=False)

    assert count == 0
    assert StockReservation.objects.filter(id=res.id).exists()


@pytest.mark.django_db
def test_re_reserve_cart_item_success(user, variant):
    """Re-reservar un ítem cuya reserva expiró renueva expires_at y recupera vigencia."""
    item, res = add_to_cart(user=user, variant_id=variant.id, quantity=2)
    res.expires_at = timezone.now() - timedelta(minutes=1)
    res.save()

    updated_item, new_res = re_reserve_cart_item(user=user, item_id=item.id)

    assert updated_item.id == item.id
    assert new_res.is_active() is True
    assert new_res.quantity == 2


@pytest.mark.django_db
def test_re_reserve_cart_item_out_of_stock_fails(user, other_user, variant):
    """Si el stock fue tomado por otro cliente mientras expiraba, re-reservar falla con out_of_stock."""
    variant.stock_quantity = 2
    variant.save()

    item_a, res_a = add_to_cart(user=user, variant_id=variant.id, quantity=2)
    # A expira
    res_a.expires_at = timezone.now() - timedelta(minutes=1)
    res_a.save()

    # B toma las 2 unidades disponibles
    add_to_cart(user=other_user, variant_id=variant.id, quantity=2)

    # A intenta re-reservar
    with pytest.raises(ApiError) as exc_info:
        re_reserve_cart_item(user=user, item_id=item_a.id)

    assert exc_info.value.get_codes() == "out_of_stock"
    assert exc_info.value.fields.get("max_available") == 0


@pytest.mark.django_db
def test_cleanup_expired_reservations_management_command(user, variant):
    """El comando de management cleanup_expired_reservations ejecuta la limpieza."""
    from io import StringIO

    item, res = add_to_cart(user=user, variant_id=variant.id, quantity=1)
    res.expires_at = timezone.now() - timedelta(seconds=1)
    res.save()

    out = StringIO()
    call_command("cleanup_expired_reservations", stdout=out)

    assert "Se liberaron 1 reservas expiradas." in out.getvalue()
    assert not StockReservation.objects.filter(id=res.id).exists()

