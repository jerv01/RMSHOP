from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.orders.models import Order, OrderItem, OrderStatusHistory
from apps.orders.serializers import (
    CheckoutInputSerializer,
    OrderListSerializer,
    OrderSerializer,
)
from apps.orders.services import create_order_from_cart
from apps.users.permissions import IsCustomer


def customer_orders(user):
    """Pedidos del cliente con sus ítems e historial; nunca expone pedidos de otros usuarios."""
    return Order.objects.filter(user=user).prefetch_related(
        Prefetch("items", queryset=OrderItem.objects.order_by("id")),
        Prefetch(
            "status_history", queryset=OrderStatusHistory.objects.order_by("created_at", "id")
        ),
    )


def get_customer_order(user, order_number: str) -> Order:
    return get_object_or_404(customer_orders(user), order_number=order_number)


class CheckoutView(APIView):
    """Crea el pedido «Pendiente de Pago» desde el carrito (HU-21, checkout provisional)."""

    permission_classes = [IsCustomer]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "checkout"

    @extend_schema(
        request=CheckoutInputSerializer,
        responses={201: OrderSerializer},
        summary="Crear pedido desde el carrito",
        tags=["Pedidos"],
    )
    def post(self, request):
        serializer = CheckoutInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = create_order_from_cart(user=request.user, **serializer.validated_data)
        order = get_customer_order(request.user, order.order_number)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderListView(APIView):
    """Lista los pedidos del cliente, del más reciente al más antiguo (HU-21)."""

    permission_classes = [IsCustomer]

    @extend_schema(
        responses={200: OrderListSerializer(many=True)},
        summary="Mis pedidos",
        tags=["Pedidos"],
    )
    def get(self, request):
        orders = Order.objects.filter(user=request.user).order_by("-created_at")
        return Response(OrderListSerializer(orders, many=True).data)


class OrderDetailView(APIView):
    """Detalle de un pedido del cliente con su estado en texto (AC-HU-21-1)."""

    permission_classes = [IsCustomer]

    @extend_schema(
        responses={200: OrderSerializer},
        summary="Detalle de mi pedido",
        tags=["Pedidos"],
    )
    def get(self, request, order_number: str):
        order = get_customer_order(request.user, order_number)
        return Response(OrderSerializer(order).data)
