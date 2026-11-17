from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cart.models import Cart, CartItem
from apps.cart.serializers import (
    CartItemAddInputSerializer,
    CartOutputSerializer,
)
from apps.cart.services import add_to_cart
from apps.users.permissions import IsCustomer


class CartView(APIView):
    """Consulta el carrito de compras del cliente autenticado (HU-13)."""

    permission_classes = [IsCustomer]

    @extend_schema(
        summary="Consultar carrito del cliente",
        description=(
            "Retorna el carrito de compras del usuario autenticado con sus ítems, "
            "cantidades, subtotales y estado de reservas activas."
        ),
        responses={200: CartOutputSerializer},
    )
    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart = Cart.objects.prefetch_related(
            Prefetch(
                "items",
                queryset=CartItem.objects.select_related(
                    "variant__product", "reservation"
                ).order_by("-created_at"),
            )
        ).get(id=cart.id)
        return Response(CartOutputSerializer(cart).data, status=status.HTTP_200_OK)


class CartItemAddView(APIView):
    """Agrega una variante de producto al carrito reservando stock (HU-13)."""

    permission_classes = [IsCustomer]

    @extend_schema(
        summary="Agregar variante al carrito",
        description=(
            "Agrega una cantidad de una variante al carrito del cliente autenticado, "
            "reservando el stock correspondiente de forma atómica por 15 minutos."
        ),
        request=CartItemAddInputSerializer,
        responses={200: CartOutputSerializer},
    )
    def post(self, request):
        serializer = CartItemAddInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart_item, _ = add_to_cart(
            user=request.user,
            variant_id=serializer.validated_data["variant_id"],
            quantity=serializer.validated_data["quantity"],
        )

        cart = Cart.objects.prefetch_related(
            Prefetch(
                "items",
                queryset=CartItem.objects.select_related(
                    "variant__product", "reservation"
                ).order_by("-created_at"),
            )
        ).get(id=cart_item.cart_id)
        return Response(CartOutputSerializer(cart).data, status=status.HTTP_200_OK)
