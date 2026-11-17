from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.cart.models import Cart, CartItem, StockReservation
from apps.cart.services import get_available_variant_stock
from apps.catalog.models import Category, Product, ProductStatus, ProductVariant
from apps.users.clerk import ClerkClaims
from apps.users.models import User

CART_URL = "/api/v1/cart/"
CART_ITEMS_URL = "/api/v1/cart/items/"


@pytest.fixture
def customer_user(db):
    return User.objects.create(
        clerk_user_id="customer_user_1",
        email="customer1@rmshop.co",
        first_name="Cliente",
        last_name="Uno",
    )


@pytest.fixture
def other_customer_user(db):
    return User.objects.create(
        clerk_user_id="customer_user_2",
        email="customer2@rmshop.co",
        first_name="Cliente",
        last_name="Dos",
    )


@pytest.fixture
def auth_client(customer_user):
    client = APIClient()
    claims = ClerkClaims(
        sub=customer_user.clerk_user_id,
        email=customer_user.email,
        role=None,
    )
    client.force_authenticate(user=customer_user, token=claims)
    return client


@pytest.fixture
def other_auth_client(other_customer_user):
    client = APIClient()
    claims = ClerkClaims(
        sub=other_customer_user.clerk_user_id,
        email=other_customer_user.email,
        role=None,
    )
    client.force_authenticate(user=other_customer_user, token=claims)
    return client


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
        name="Camiseta RM Minimalista",
        slug="camiseta-rm-minimalista",
        description="Camiseta clásica de algodón 100%.",
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
        stock_quantity=5,
    )


@pytest.fixture
def variant_blue(db, product):
    return ProductVariant.objects.create(
        product=product,
        color="Azul",
        size="L",
        stock_quantity=3,
    )


# ---------------------------------------------------------------------------
# AC-HU-13-1: Happy path
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_add_variant_to_cart_happy_path(auth_client, customer_user, variant):
    """AC-HU-13-1: Cliente autenticado agrega variante con stock disponible.

    Retorna 200 con el carrito actualizado, totales calculados y reserva activa de 15 min.
    """
    payload = {"variant_id": variant.id, "quantity": 2}

    response = auth_client.post(CART_ITEMS_URL, data=payload, format="json")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["total_items"] == 2
    assert data["total_price"] == "100000"
    assert len(data["items"]) == 1

    item = data["items"][0]
    assert item["variant_id"] == variant.id
    assert item["product_id"] == variant.product.id
    assert item["product_name"] == "Camiseta RM Minimalista"
    assert item["product_slug"] == "camiseta-rm-minimalista"
    assert item["color"] == "Negro"
    assert item["size"] == "M"
    assert item["unit_price"] == "50000"
    assert item["quantity"] == 2
    assert item["subtotal"] == "100000"
    assert item["is_reservation_active"] is True
    assert item["reservation_expires_at"] is not None

    # Verificar persistencia en base de datos
    cart = Cart.objects.get(user=customer_user)
    assert cart.items.count() == 1
    cart_item = cart.items.first()
    assert cart_item.quantity == 2
    assert hasattr(cart_item, "reservation")
    assert cart_item.reservation.quantity == 2
    assert cart_item.reservation.is_active() is True


@pytest.mark.django_db
def test_add_variant_default_quantity_is_one(auth_client, customer_user, variant):
    """Si no se especifica quantity, el serializer asigna por defecto 1."""
    payload = {"variant_id": variant.id}

    response = auth_client.post(CART_ITEMS_URL, data=payload, format="json")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_items"] == 1
    assert data["total_price"] == "50000"
    assert data["items"][0]["quantity"] == 1


@pytest.mark.django_db
def test_add_variant_accumulates_quantity_and_extends_reservation(
    auth_client, customer_user, variant
):
    """Agregar la misma variante acumula la cantidad y actualiza la reserva."""
    auth_client.post(CART_ITEMS_URL, data={"variant_id": variant.id, "quantity": 1})
    response = auth_client.post(CART_ITEMS_URL, data={"variant_id": variant.id, "quantity": 2})

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_items"] == 3
    assert data["total_price"] == "150000"
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 3
    assert data["items"][0]["subtotal"] == "150000"


@pytest.mark.django_db
def test_add_multiple_distinct_variants_to_cart(auth_client, customer_user, variant, variant_blue):
    """Agregar variantes distintas crea múltiples ítems en el carrito."""
    auth_client.post(CART_ITEMS_URL, data={"variant_id": variant.id, "quantity": 1})
    response = auth_client.post(CART_ITEMS_URL, data={"variant_id": variant_blue.id, "quantity": 2})

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_items"] == 3
    assert data["total_price"] == "150000"
    assert len(data["items"]) == 2


@pytest.mark.django_db
def test_get_cart_detail_authenticated(auth_client, customer_user, variant):
    """GET /api/v1/cart/ retorna el detalle del carrito con sus ítems."""
    auth_client.post(CART_ITEMS_URL, data={"variant_id": variant.id, "quantity": 1})

    response = auth_client.get(CART_URL)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_items"] == 1
    assert data["total_price"] == "50000"
    assert len(data["items"]) == 1
    assert data["items"][0]["variant_id"] == variant.id


@pytest.mark.django_db
def test_get_empty_cart_creates_cart_lazily(auth_client, customer_user):
    """GET /api/v1/cart/ en un usuario sin carrito retorna carrito vacío con 200."""
    response = auth_client.get(CART_URL)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_items"] == 0
    assert data["total_price"] == "0"
    assert data["items"] == []
    assert Cart.objects.filter(user=customer_user).exists()


@pytest.mark.django_db
def test_cart_endpoints_support_without_trailing_slash(auth_client, variant):
    """Verifica que /cart y /cart/items sin slash final también funcionen."""
    res_post = auth_client.post(
        "/api/v1/cart/items", data={"variant_id": variant.id, "quantity": 1}
    )
    assert res_post.status_code == status.HTTP_200_OK

    res_get = auth_client.get("/api/v1/cart")
    assert res_get.status_code == status.HTTP_200_OK


# ---------------------------------------------------------------------------
# AC-HU-13-2: Unauthenticated
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_unauthenticated_cannot_add_item(api_client, variant):
    """AC-HU-13-2: Petición sin autenticación retorna 401 y no modifica la base de datos."""
    response = api_client.post(CART_ITEMS_URL, data={"variant_id": variant.id, "quantity": 1})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["code"] == "not_authenticated"
    assert data["message"] == "Debes iniciar sesión para continuar."
    assert Cart.objects.count() == 0
    assert CartItem.objects.count() == 0
    assert StockReservation.objects.count() == 0


@pytest.mark.django_db
def test_unauthenticated_cannot_get_cart(api_client):
    """AC-HU-13-2: GET a /api/v1/cart/ sin autenticación retorna 401."""
    response = api_client.get(CART_URL)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["code"] == "not_authenticated"


# ---------------------------------------------------------------------------
# AC-HU-13-3: Out of stock
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_add_variant_out_of_stock_variant_zero_stock(auth_client, product):
    """AC-HU-13-3: Variante con stock 0 retorna 400 con code='out_of_stock'."""
    zero_variant = ProductVariant.objects.create(
        product=product,
        color="Blanco",
        size="S",
        stock_quantity=0,
    )

    response = auth_client.post(CART_ITEMS_URL, data={"variant_id": zero_variant.id, "quantity": 1})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["code"] == "out_of_stock"
    assert data["message"] == "No hay disponibilidad suficiente para esta variante."
    assert CartItem.objects.count() == 0


@pytest.mark.django_db
def test_add_variant_out_of_stock_due_to_active_reservations(
    auth_client, other_customer_user, variant
):
    """AC-HU-13-3: Si otra sesión reservó el stock disponible, retorna out_of_stock."""
    other_cart = Cart.objects.create(user=other_customer_user)
    other_item = CartItem.objects.create(
        cart=other_cart, variant=variant, quantity=variant.stock_quantity
    )
    StockReservation.objects.create(
        cart_item=other_item,
        variant=variant,
        quantity=variant.stock_quantity,
        expires_at=timezone.now() + timedelta(minutes=15),
    )

    response = auth_client.post(CART_ITEMS_URL, data={"variant_id": variant.id, "quantity": 1})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["code"] == "out_of_stock"


# ---------------------------------------------------------------------------
# Input validation errors
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_add_variant_missing_variant_id(auth_client):
    """Falta variant_id en el payload -> 400 validation_error."""
    response = auth_client.post(CART_ITEMS_URL, data={"quantity": 1})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["code"] == "validation_error"
    assert "variant_id" in data["fields"]


@pytest.mark.django_db
def test_add_variant_invalid_quantity(auth_client, variant):
    """Cantidad menor o igual a cero -> 400 validation_error."""
    for invalid_qty in [0, -1, -5]:
        response = auth_client.post(
            CART_ITEMS_URL,
            data={"variant_id": variant.id, "quantity": invalid_qty},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["code"] == "validation_error"
        assert "quantity" in data["fields"]


@pytest.mark.django_db
def test_add_variant_nonexistent_variant(auth_client):
    """ID de variante que no existe en base de datos -> 400 validation_error."""
    response = auth_client.post(CART_ITEMS_URL, data={"variant_id": 999999, "quantity": 1})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["code"] == "validation_error"
    assert "variant_id" in data["fields"]


@pytest.mark.django_db
def test_add_variant_product_not_published(auth_client, category):
    """Variante de producto no publicado (DRAFT o ARCHIVED) -> 400 validation_error."""
    draft_product = Product.objects.create(
        name="Camiseta Borrador",
        slug="camiseta-borrador",
        description="Aún no publicada",
        price=Decimal("40000"),
        material="Algodón",
        category=category,
        status=ProductStatus.DRAFT,
    )
    draft_variant = ProductVariant.objects.create(
        product=draft_product,
        color="Rojo",
        size="M",
        stock_quantity=10,
    )

    response = auth_client.post(
        CART_ITEMS_URL, data={"variant_id": draft_variant.id, "quantity": 1}
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["code"] == "validation_error"
    assert "variant_id" in data["fields"]


# ---------------------------------------------------------------------------
# Isolation and privacy
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_cart_privacy_and_isolation(
    auth_client, other_auth_client, customer_user, other_customer_user, variant, variant_blue
):
    """Cada cliente solo puede ver y modificar su propio carrito."""
    # Cliente 1 agrega variante
    auth_client.post(CART_ITEMS_URL, data={"variant_id": variant.id, "quantity": 2})

    # Cliente 2 consulta su carrito: debe estar vacío
    res_other = other_auth_client.get(CART_URL)
    assert res_other.status_code == status.HTTP_200_OK
    data_other = res_other.json()
    assert data_other["total_items"] == 0
    assert data_other["total_price"] == "0"
    assert data_other["items"] == []

    # Cliente 2 agrega su propio ítem
    other_auth_client.post(CART_ITEMS_URL, data={"variant_id": variant_blue.id, "quantity": 1})

    # Cliente 1 consulta su carrito: solo ve su propio ítem (no el de Cliente 2)
    res_user1 = auth_client.get(CART_URL)
    data_user1 = res_user1.json()
    assert data_user1["total_items"] == 2
    assert len(data_user1["items"]) == 1
    assert data_user1["items"][0]["variant_id"] == variant.id

    # Cliente 2 consulta su carrito: solo ve su propio ítem (no el de Cliente 1)
    res_user2 = other_auth_client.get(CART_URL)
    data_user2 = res_user2.json()
    assert data_user2["total_items"] == 1
    assert len(data_user2["items"]) == 1
    assert data_user2["items"][0]["variant_id"] == variant_blue.id


# ---------------------------------------------------------------------------
# HU-14: DELETE /api/v1/cart/items/<item_id>/
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_delete_cart_item_happy_path(auth_client, customer_user, variant, variant_blue):
    """AC-HU-14-1: Cliente autenticado elimina un ítem de su carrito.

    Retorna 200 con el carrito recalculado y la reserva de stock liberada.
    """
    # Agregar 2 variantes distintas
    auth_client.post(CART_ITEMS_URL, data={"variant_id": variant.id, "quantity": 2})
    auth_client.post(CART_ITEMS_URL, data={"variant_id": variant_blue.id, "quantity": 1})

    item_to_remove = CartItem.objects.get(cart__user=customer_user, variant=variant)
    remaining_item = CartItem.objects.get(cart__user=customer_user, variant=variant_blue)

    # Verificar stock reservado previo
    assert get_available_variant_stock(variant) == variant.stock_quantity - 2

    # Ejecutar DELETE
    response = auth_client.delete(f"/api/v1/cart/items/{item_to_remove.id}/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["total_items"] == 1
    assert data["total_price"] == "50000"
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == remaining_item.id
    assert data["items"][0]["variant_id"] == variant_blue.id

    # Verificar liberación en base de datos
    assert not CartItem.objects.filter(id=item_to_remove.id).exists()
    assert not StockReservation.objects.filter(cart_item_id=item_to_remove.id).exists()
    assert get_available_variant_stock(variant) == variant.stock_quantity


@pytest.mark.django_db
def test_delete_cart_item_expired_reservation(auth_client, customer_user, variant):
    """AC-HU-14-2: Si la reserva asociada ya expiró, el ítem se elimina normalmente sin error."""
    auth_client.post(CART_ITEMS_URL, data={"variant_id": variant.id, "quantity": 1})
    item = CartItem.objects.get(cart__user=customer_user, variant=variant)

    # Vencer la reserva manualmente
    item.reservation.expires_at = timezone.now() - timedelta(minutes=5)
    item.reservation.save(update_fields=["expires_at"])

    response = auth_client.delete(f"/api/v1/cart/items/{item.id}/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_items"] == 0
    assert data["total_price"] == "0"
    assert data["items"] == []
    assert not CartItem.objects.filter(id=item.id).exists()


@pytest.mark.django_db
def test_delete_cart_item_last_item(auth_client, customer_user, variant):
    """AC-HU-14-3: Al eliminar el último ítem, el carrito queda vacío.

    total_items=0 y total_price=0.
    """
    auth_client.post(CART_ITEMS_URL, data={"variant_id": variant.id, "quantity": 3})
    item = CartItem.objects.get(cart__user=customer_user, variant=variant)

    response = auth_client.delete(f"/api/v1/cart/items/{item.id}/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_items"] == 0
    assert data["total_price"] == "0"
    assert data["items"] == []
    assert not CartItem.objects.filter(id=item.id).exists()


@pytest.mark.django_db
def test_delete_cart_item_unauthenticated(api_client, customer_user, variant):
    """Petición anónima retorna 401 Unauthorized y no modifica el carrito."""
    cart = Cart.objects.create(user=customer_user)
    item = CartItem.objects.create(cart=cart, variant=variant, quantity=1)

    response = api_client.delete(f"/api/v1/cart/items/{item.id}/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert data["code"] == "not_authenticated"
    assert CartItem.objects.filter(id=item.id).exists()


@pytest.mark.django_db
def test_delete_cart_item_nonexistent(auth_client):
    """Intentar eliminar un item_id inexistente retorna 404 Not Found."""
    response = auth_client.delete("/api/v1/cart/items/999999/")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["code"] == "not_found"


@pytest.mark.django_db
def test_delete_cart_item_isolation(
    auth_client, other_auth_client, customer_user, other_customer_user, variant
):
    """Cliente A no puede eliminar ítems del carrito de Cliente B (retorna 404 y queda intacto)."""
    # Cliente 2 agrega ítem
    other_auth_client.post(CART_ITEMS_URL, data={"variant_id": variant.id, "quantity": 1})
    item_b = CartItem.objects.get(cart__user=other_customer_user, variant=variant)

    # Cliente 1 intenta eliminar el ítem de Cliente 2
    response = auth_client.delete(f"/api/v1/cart/items/{item_b.id}/")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["code"] == "not_found"
    assert CartItem.objects.filter(id=item_b.id).exists()


@pytest.mark.django_db
def test_delete_cart_item_supports_without_trailing_slash(auth_client, customer_user, variant):
    """Verifica que /api/v1/cart/items/<id> sin slash final funcione correctamente."""
    auth_client.post(CART_ITEMS_URL, data={"variant_id": variant.id, "quantity": 1})
    item = CartItem.objects.get(cart__user=customer_user, variant=variant)

    response = auth_client.delete(f"/api/v1/cart/items/{item.id}")

    assert response.status_code == status.HTTP_200_OK
    assert not CartItem.objects.filter(id=item.id).exists()
