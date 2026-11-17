import threading
from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.cart.models import Cart, StockReservation
from apps.cart.services import (
    add_to_cart,
    convert_cart_to_sale,
    convert_reservation_to_sale,
    get_available_variant_stock,
)
from apps.catalog.models import Category, Product, ProductStatus, ProductVariant
from apps.core.exceptions import ApiError
from apps.inventory.models import StockMovement
from apps.users.clerk import ClerkClaims
from apps.users.models import User

CART_ITEMS_URL = "/api/v1/cart/items/"
PUBLIC_PRODUCTS_URL = "/api/v1/products"


@pytest.fixture
def client_a_user(db):
    return User.objects.create(
        clerk_user_id="clerk_client_a",
        email="client_a@rmshop.co",
        first_name="Cliente",
        last_name="A",
    )


@pytest.fixture
def client_b_user(db):
    return User.objects.create(
        clerk_user_id="clerk_client_b",
        email="client_b@rmshop.co",
        first_name="Cliente",
        last_name="B",
    )


@pytest.fixture
def client_a_api(client_a_user):
    client = APIClient()
    claims = ClerkClaims(
        sub=client_a_user.clerk_user_id,
        email=client_a_user.email,
        role=None,
    )
    client.force_authenticate(user=client_a_user, token=claims)
    return client


@pytest.fixture
def client_b_api(client_b_user):
    client = APIClient()
    claims = ClerkClaims(
        sub=client_b_user.clerk_user_id,
        email=client_b_user.email,
        role=None,
    )
    client.force_authenticate(user=client_b_user, token=claims)
    return client


@pytest.fixture
def single_stock_product(db):
    category = Category.objects.filter(slug="camisetas-tops").first()
    if not category:
        category = Category.objects.create(
            name="Camisetas y Tops",
            slug="camisetas-tops",
        )
    prod = Product.objects.create(
        name="Camiseta Exclusiva RM",
        slug="camiseta-exclusiva-rm",
        description="Prenda única de colección.",
        price=Decimal("120000"),
        material="100% Algodón Pima",
        category=category,
        status=ProductStatus.PUBLISHED,
    )
    variant = ProductVariant.objects.create(
        product=prod,
        color="Negro",
        size="M",
        stock_quantity=1,
    )
    return prod, variant


# ---------------------------------------------------------------------------
# AC-HU-17-1: Camino Feliz
# Dada una variante con stock 1, cuando el cliente A la agrega,
# entonces queda reservada y el cliente B la ve agotada.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_ac_hu_17_1_variant_with_stock_1_reserved_by_client_a_is_sold_out_for_client_b(
    client_a_api, client_b_api, single_stock_product
):
    product, variant = single_stock_product

    # Estado inicial: catálogo público muestra stock 1 y producto disponible
    init_res = client_b_api.get(f"{PUBLIC_PRODUCTS_URL}/{product.slug}")
    assert init_res.status_code == status.HTTP_200_OK
    assert init_res.json()["in_stock"] is True
    assert init_res.json()["variants"][0]["stock_quantity"] == 1
    assert init_res.json()["variants"][0]["is_available"] is True

    # Cliente A agrega la única unidad a su carrito
    add_res = client_a_api.post(
        CART_ITEMS_URL,
        data={"variant_id": variant.id, "quantity": 1},
        format="json",
    )
    assert add_res.status_code == status.HTTP_200_OK

    # Verificación en catálogo para Cliente B: la variante se ve AGOTADA
    detail_res = client_b_api.get(f"{PUBLIC_PRODUCTS_URL}/{product.slug}")
    assert detail_res.status_code == status.HTTP_200_OK
    data = detail_res.json()
    assert data["in_stock"] is False
    assert len(data["variants"]) == 1
    b_variant = data["variants"][0]
    assert b_variant["stock_quantity"] == 0
    assert b_variant["available_quantity"] == 0
    assert b_variant["is_available"] is False

    # También en el listado general de productos
    list_res = client_b_api.get(PUBLIC_PRODUCTS_URL)
    assert list_res.status_code == status.HTTP_200_OK
    prod_in_list = next(p for p in list_res.json() if p["id"] == product.id)
    assert prod_in_list["in_stock"] is False
    assert prod_in_list["variants"][0]["stock_quantity"] == 0

    # Si la reserva expira (+15 min), el cliente B la vuelve a ver disponible
    reservation = StockReservation.objects.get(variant=variant)
    reservation.expires_at = timezone.now() - timedelta(seconds=1)
    reservation.save()

    detail_after_expiry = client_b_api.get(f"{PUBLIC_PRODUCTS_URL}/{product.slug}")
    assert detail_after_expiry.status_code == status.HTTP_200_OK
    assert detail_after_expiry.json()["in_stock"] is True
    assert detail_after_expiry.json()["variants"][0]["stock_quantity"] == 1
    assert detail_after_expiry.json()["variants"][0]["is_available"] is True


# ---------------------------------------------------------------------------
# AC-HU-17-2: Alternativo / Error
# Dada una reserva vigente de A, cuando B intenta agregar la misma unidad,
# entonces se informa que no hay disponibilidad.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_ac_hu_17_2_client_b_cannot_add_reserved_variant(
    client_a_api, client_b_api, single_stock_product
):
    product, variant = single_stock_product

    # Cliente A reserva la unidad disponible
    add_a = client_a_api.post(
        CART_ITEMS_URL,
        data={"variant_id": variant.id, "quantity": 1},
        format="json",
    )
    assert add_a.status_code == status.HTTP_200_OK

    # Cliente B intenta agregar la misma unidad
    add_b = client_b_api.post(
        CART_ITEMS_URL,
        data={"variant_id": variant.id, "quantity": 1},
        format="json",
    )
    assert add_b.status_code == status.HTTP_400_BAD_REQUEST
    error_data = add_b.json()
    assert error_data["code"] == "out_of_stock"
    assert "No hay disponibilidad suficiente" in error_data["message"]

    # Carrito de B debe permanecer vacío
    cart_b = Cart.objects.filter(user__clerk_user_id="clerk_client_b").first()
    assert cart_b is None or cart_b.items.count() == 0


@pytest.mark.django_db(transaction=True)
def test_ac_hu_17_2_concurrency_two_clients_zero_overselling(single_stock_product):
    """Prueba de concurrencia: dos clientes intentan reservar la única unidad en paralelo."""
    from django.db import connection

    product, variant = single_stock_product
    user_1 = User.objects.create(clerk_user_id="conc_user_1", email="u1@test.co")
    user_2 = User.objects.create(clerk_user_id="conc_user_2", email="u2@test.co")

    results = []

    def attempt_reservation(user):
        try:
            item, res = add_to_cart(user=user, variant_id=variant.id, quantity=1)
            results.append(("success", user.id))
        except ApiError as exc:
            results.append(("error", exc.get_codes()))
        finally:
            connection.close()

    t1 = threading.Thread(target=attempt_reservation, args=(user_1,))
    t2 = threading.Thread(target=attempt_reservation, args=(user_2,))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Exactamente una reserva exitosa y un rechazo out_of_stock
    successes = [r for r in results if r[0] == "success"]
    errors = [r for r in results if r[0] == "error"]

    assert len(successes) == 1
    assert len(errors) == 1
    assert errors[0][1] == "out_of_stock"

    # Verificación estricta en base de datos: 0 sobreventas
    assert StockReservation.objects.filter(variant=variant).count() == 1
    assert get_available_variant_stock(variant) == 0


# ---------------------------------------------------------------------------
# AC-HU-17-3: Caso Límite
# Dado un pedido pagado antes de los 15 minutos, cuando termina el checkout,
# entonces la reserva se convierte en venta y no se libera. [SUPUESTO]
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_ac_hu_17_3_checkout_converts_reservation_to_sale_and_does_not_release(
    client_a_user, single_stock_product
):
    product, variant = single_stock_product
    # Configuramos stock inicial = 3
    variant.stock_quantity = 3
    variant.save()

    # Cliente A reserva 2 unidades
    cart_item, reservation = add_to_cart(user=client_a_user, variant_id=variant.id, quantity=2)

    assert reservation.quantity == 2
    assert reservation.is_active() is True
    # Stock disponible antes de checkout = 3 - 2 = 1
    assert get_available_variant_stock(variant) == 1

    # Termina el checkout antes de los 15 minutos -> se convierte en venta
    movement = convert_reservation_to_sale(
        reservation=reservation,
        order_reference="ORD-2026-001",
    )

    # 1. Movimiento de auditoría registrado (HU-37)
    assert isinstance(movement, StockMovement)
    assert movement.delta == -2
    assert movement.resulting_stock == 1
    assert "ORD-2026-001" in movement.reason

    # 2. Stock físico descontado permanentemente
    variant.refresh_from_db()
    assert variant.stock_quantity == 1

    # 3. La reserva fue consumida y eliminada
    assert not StockReservation.objects.filter(id=reservation.id).exists()

    # 4. El stock NO se liberó: el disponible sigue siendo exactamente 1
    assert get_available_variant_stock(variant) == 1


@pytest.mark.django_db
def test_ac_hu_17_3_convert_cart_to_sale_multiple_items(client_a_user, single_stock_product):
    product, variant1 = single_stock_product
    variant2 = ProductVariant.objects.create(
        product=product,
        color="Blanco",
        size="L",
        stock_quantity=5,
    )

    cart_item1, res1 = add_to_cart(user=client_a_user, variant_id=variant1.id, quantity=1)
    cart_item2, res2 = add_to_cart(user=client_a_user, variant_id=variant2.id, quantity=2)

    cart = Cart.objects.get(user=client_a_user)
    movements = convert_cart_to_sale(cart=cart, order_reference="ORD-MULTI-01")

    assert len(movements) == 2
    variant1.refresh_from_db()
    variant2.refresh_from_db()
    assert variant1.stock_quantity == 0
    assert variant2.stock_quantity == 3
    assert get_available_variant_stock(variant1) == 0
    assert get_available_variant_stock(variant2) == 3

    # El carrito y sus reservas quedan limpios
    assert cart.items.count() == 0
    assert StockReservation.objects.filter(variant__in=[variant1, variant2]).count() == 0


@pytest.mark.django_db
def test_ac_hu_17_3_cannot_convert_expired_reservation_to_sale(client_a_user, single_stock_product):
    product, variant = single_stock_product
    cart_item, reservation = add_to_cart(user=client_a_user, variant_id=variant.id, quantity=1)

    # Expirar la reserva
    reservation.expires_at = timezone.now() - timedelta(seconds=1)
    reservation.save()

    with pytest.raises(ApiError) as exc_info:
        convert_reservation_to_sale(reservation=reservation)

    assert exc_info.value.get_codes() == "reservation_expired"
    # El stock físico no se modificó
    variant.refresh_from_db()
    assert variant.stock_quantity == 1


# ---------------------------------------------------------------------------
# Casos límite y Concurrencia de Auditoría Argon
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_concurrent_convert_cart_to_sale_prevents_double_stock_deduction(
    client_a_user, single_stock_product
):
    """Argon Finding: Prevenir doble descuento (Double-Spend) en checkout simultáneo.

    Si dos hilos disparan checkout sobre el mismo carrito al mismo tiempo,
    únicamente se descuenta la reserva una sola vez (stock 5 -> 4, no 3).
    """
    from concurrent.futures import ThreadPoolExecutor

    from django.db import connection

    product, variant = single_stock_product
    variant.stock_quantity = 5
    variant.save(update_fields=["stock_quantity"])

    add_to_cart(user=client_a_user, variant_id=variant.id, quantity=1)
    cart = Cart.objects.get(user=client_a_user)

    def attempt_checkout():
        try:
            return ("success", convert_cart_to_sale(cart=cart, order_reference="ORD-RACE"))
        except Exception as exc:
            return ("error", str(exc))
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(attempt_checkout)
        f2 = executor.submit(attempt_checkout)
        results = [f1.result(), f2.result()]

    # Exactamente una ejecución generó la venta (descuento de stock)
    movements_generated = [r[1] for r in results if r[0] == "success" and len(r[1]) > 0]
    assert len(movements_generated) == 1
    assert len(movements_generated[0]) == 1

    variant.refresh_from_db()
    # El stock físico debe ser exactamente 4 (5 - 1)
    assert variant.stock_quantity == 4
    # Solo debe existir 1 movimiento de stock registrado
    assert StockMovement.objects.filter(variant=variant).count() == 1


@pytest.mark.django_db
def test_re_adding_same_variant_after_own_reservation_expired_succeeds(
    client_a_user, single_stock_product
):
    """Argon Finding: Cantidad fantasma tras expiración.

    Cliente A reserva la única unidad disponible (stock=1), deja pasar >15 min (expira)
    y luego intenta agregar nuevamente 1 unidad. No debe fallar con out_of_stock.
    """
    product, variant = single_stock_product
    assert variant.stock_quantity == 1

    cart_item, res = add_to_cart(user=client_a_user, variant_id=variant.id, quantity=1)
    # Forzar expiración
    StockReservation.objects.filter(id=res.id).update(
        expires_at=timezone.now() - timedelta(seconds=10)
    )

    # El cliente vuelve a agregar 1 unidad de la variante ahora liberada
    updated_item, new_res = add_to_cart(user=client_a_user, variant_id=variant.id, quantity=1)
    assert updated_item.quantity == 1
    assert new_res.is_active() is True
    assert get_available_variant_stock(variant) == 0
