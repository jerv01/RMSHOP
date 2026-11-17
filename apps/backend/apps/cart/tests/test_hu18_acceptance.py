import threading
from datetime import timedelta
from decimal import Decimal

import pytest
from django.db import connection
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.cart.models import Cart, StockReservation
from apps.cart.services import (
    add_to_cart,
    convert_cart_to_sale,
    release_expired_reservations,
)
from apps.catalog.models import Category, Product, ProductStatus, ProductVariant
from apps.core.exceptions import ApiError
from apps.inventory.models import StockMovement
from apps.users.clerk import ClerkClaims
from apps.users.models import User

CART_URL = "/api/v1/cart/"
CART_ITEMS_URL = "/api/v1/cart/items/"
PUBLIC_PRODUCTS_URL = "/api/v1/products"


@pytest.fixture
def client_a_user(db):
    return User.objects.create(
        clerk_user_id="clerk_hu18_a",
        email="hu18_a@rmshop.co",
        first_name="Cliente",
        last_name="A",
    )


@pytest.fixture
def client_b_user(db):
    return User.objects.create(
        clerk_user_id="clerk_hu18_b",
        email="hu18_b@rmshop.co",
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
        name="Camiseta Colección HU18",
        slug="camiseta-coleccion-hu18",
        description="Prenda exclusiva de edición limitada.",
        price=Decimal("110000"),
        material="100% Algodón",
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
# AC-HU-18-1: Camino Feliz
# Dada una reserva de 15 minutos sin checkout, cuando vence,
# entonces el stock queda disponible para otros.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_ac_hu_18_1_expired_reservation_automatically_frees_stock_for_others(
    client_a_api, client_b_api, single_stock_product
):
    product, variant = single_stock_product

    # 1. Cliente A agrega la única unidad a su carrito
    res_a = client_a_api.post(
        CART_ITEMS_URL,
        data={"variant_id": variant.id, "quantity": 1},
        format="json",
    )
    assert res_a.status_code == status.HTTP_200_OK

    # 2. Cliente B la ve agotada y no puede agregarla
    cat_b = client_b_api.get(f"{PUBLIC_PRODUCTS_URL}/{product.slug}")
    assert cat_b.json()["in_stock"] is False
    assert cat_b.json()["variants"][0]["is_available"] is False

    add_b_fail = client_b_api.post(
        CART_ITEMS_URL,
        data={"variant_id": variant.id, "quantity": 1},
        format="json",
    )
    assert add_b_fail.status_code == status.HTTP_400_BAD_REQUEST
    assert add_b_fail.json()["code"] == "out_of_stock"

    # 3. Transcurren los 15 minutos sin que A avance al checkout (vence la reserva)
    reservation = StockReservation.objects.get(variant=variant)
    reservation.expires_at = timezone.now() - timedelta(seconds=1)
    reservation.save()

    # 4. Inmediatamente el stock queda disponible para Cliente B (latencia < 60s, exactamente 0s)
    cat_b_after = client_b_api.get(f"{PUBLIC_PRODUCTS_URL}/{product.slug}")
    assert cat_b_after.json()["in_stock"] is True
    assert cat_b_after.json()["variants"][0]["stock_quantity"] == 1
    assert cat_b_after.json()["variants"][0]["is_available"] is True

    # 5. Cliente B puede agregarla exitosamente a su carrito
    add_b_success = client_b_api.post(
        CART_ITEMS_URL,
        data={"variant_id": variant.id, "quantity": 1},
        format="json",
    )
    assert add_b_success.status_code == status.HTTP_200_OK

    # 6. En el carrito de Cliente A, el ítem se muestra como expirado con mensaje descriptivo
    cart_a_res = client_a_api.get(CART_URL)
    assert cart_a_res.status_code == status.HTTP_200_OK
    item_a = cart_a_res.json()["items"][0]
    assert item_a["reservation_status"] == "expired"
    assert item_a["is_reservation_active"] is False
    assert item_a["time_remaining_seconds"] == 0
    assert item_a["reservation_message"] == "Tu reserva expiró"


# ---------------------------------------------------------------------------
# AC-HU-18-2: Alternativo / Error
# Dado un cliente que intenta pagar un ítem expirado, cuando avanza al checkout,
# entonces se le informa y se verifica de nuevo el stock.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_ac_hu_18_2_checkout_with_expired_item_aborts_and_reports_status(
    client_a_user, single_stock_product
):
    product, variant = single_stock_product

    # Cliente A reserva la unidad
    cart_item, reservation = add_to_cart(user=client_a_user, variant_id=variant.id, quantity=1)
    cart = Cart.objects.get(user=client_a_user)

    # La reserva vence
    reservation.expires_at = timezone.now() - timedelta(minutes=2)
    reservation.save()

    # Cliente A intenta procesar checkout con el ítem expirado
    with pytest.raises(ApiError) as exc_info:
        convert_cart_to_sale(cart=cart, order_reference="ORD-EXPIRED-TEST")

    err = exc_info.value
    assert err.get_codes() == "reservation_expired"
    assert "ha expirado" in str(err.detail)

    # El stock físico no se descontó y no se crearon movimientos de venta
    variant.refresh_from_db()
    assert variant.stock_quantity == 1
    assert StockMovement.objects.filter(variant=variant).count() == 0


# ---------------------------------------------------------------------------
# AC-HU-18-3: Caso Límite
# Dado un cliente que paga justo al vencer la reserva, cuando coinciden
# ambos eventos, entonces prevalece uno solo y el sistema no genera sobreventa. [SUPUESTO]
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
def test_ac_hu_18_3_checkout_and_expiration_race_condition_zero_overselling(
    client_a_user, client_b_user, single_stock_product
):
    """Prueba de concurrencia límite: coincidencia simultánea entre checkout de A

    y reserva/liberación de la misma variante por B al filo de la expiración.
    Exactamente uno prevalece y 0 sobreventas.
    """
    product, variant = single_stock_product
    assert variant.stock_quantity == 1

    add_to_cart(user=client_a_user, variant_id=variant.id, quantity=1)
    cart_a = Cart.objects.get(user=client_a_user)

    # Sincronización mediante barrera para disparo simultáneo
    barrier = threading.Barrier(2)
    results = {}

    def attempt_checkout_a():
        try:
            barrier.wait()
            movements = convert_cart_to_sale(cart=cart_a, order_reference="ORD-LIMIT-RACE")
            results["checkout_a"] = ("success", len(movements))
        except Exception as exc:
            err_code = exc.get_codes() if hasattr(exc, "get_codes") else str(exc)
            results["checkout_a"] = ("error", err_code)
        finally:
            connection.close()

    def attempt_reserve_b():
        try:
            barrier.wait()
            item, res = add_to_cart(user=client_b_user, variant_id=variant.id, quantity=1)
            results["reserve_b"] = ("success", res.quantity)
        except Exception as exc:
            err_code = exc.get_codes() if hasattr(exc, "get_codes") else str(exc)
            results["reserve_b"] = ("error", err_code)
        finally:
            connection.close()

    t1 = threading.Thread(target=attempt_checkout_a)
    t2 = threading.Thread(target=attempt_reserve_b)

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Exclusión mutua estricta: nunca pueden tener éxito ambos simultáneamente
    a_success = results["checkout_a"][0] == "success"
    b_success = results["reserve_b"][0] == "success"

    # Prevalece exactamente uno solo
    assert a_success != b_success, f"Resultados ambiguos: {results}"

    variant.refresh_from_db()
    if a_success:
        # A completó la compra: el stock físico pasó a 0 y B fue rechazado con out_of_stock
        assert variant.stock_quantity == 0
        assert results["reserve_b"] == ("error", "out_of_stock")
        assert StockMovement.objects.filter(variant=variant).count() == 1
    else:
        # B reservó la unidad liberada o A fue rechazado por expiración
        assert results["checkout_a"][0] == "error"
        assert variant.stock_quantity == 1
        assert StockReservation.objects.filter(variant=variant).count() == 1


# ---------------------------------------------------------------------------
# Requerimiento No Funcional: Cero duplicados en liberación
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_nfr_zero_duplicate_releases(client_a_user, single_stock_product):
    """El stock liberado no puede ser liberado dos veces (idempotencia estricta)."""
    product, variant = single_stock_product
    item, res = add_to_cart(user=client_a_user, variant_id=variant.id, quantity=1)

    res.expires_at = timezone.now() - timedelta(seconds=5)
    res.save()

    # Primera ejecución de liberación
    count_1 = release_expired_reservations()
    assert count_1 == 1

    # Segunda ejecución inmediata
    count_2 = release_expired_reservations()
    assert count_2 == 0

    # Tercera ejecución
    count_3 = release_expired_reservations()
    assert count_3 == 0
