from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import ProductVariant
from apps.catalog.serializers import ProductVariantSerializer
from apps.inventory.models import StockMovement
from apps.inventory.serializers import (
    StockAdjustmentInputSerializer,
    StockAdjustmentResponseSerializer,
    StockMovementSerializer,
)
from apps.inventory.services import adjust_variant_stock
from apps.users.models import User
from apps.users.permissions import IsRMAdmin


class AdminVariantStockAdjustmentView(APIView):
    """Ajusta manualmente el stock de una variante de producto (HU-37).

    Permite aumentar o ajustar el stock para reflejar ingresos de mercancía física.
    Cada cambio queda registrado en la tabla `stock_movements` con fecha, hora,
    administrador, delta y motivo.
    """

    permission_classes = [IsRMAdmin]

    @extend_schema(
        summary="Ajustar stock de variante",
        description=(
            "Aumenta o reduce el stock disponible de una combinación (variante) de producto. "
            "El delta no puede ser cero y el stock resultante no puede ser negativo. "
            "Genera un registro inmutable en el historial de movimientos de inventario."
        ),
        request=StockAdjustmentInputSerializer,
        responses={
            200: StockAdjustmentResponseSerializer,
        },
    )
    def post(self, request, variant_id: int, product_id: int | None = None):
        if product_id is not None:
            get_object_or_404(ProductVariant, id=variant_id, product_id=product_id)
        else:
            get_object_or_404(ProductVariant, id=variant_id)

        serializer = StockAdjustmentInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        admin_user = (
            request.user
            if isinstance(request.user, User) and request.user.is_authenticated
            else None
        )

        variant, movement = adjust_variant_stock(
            variant_id=variant_id,
            delta=serializer.validated_data["delta"],
            admin_user=admin_user,
            reason=serializer.validated_data.get("reason", "Ajuste manual"),
            product_id=product_id,
        )

        response_data = {
            "variant": ProductVariantSerializer(variant).data,
            "movement": StockMovementSerializer(movement).data,
        }
        return Response(response_data, status=status.HTTP_200_OK)


class AdminVariantStockMovementsListView(APIView):
    """Consulta el historial de movimientos de stock para una variante (HU-37)."""

    permission_classes = [IsRMAdmin]

    @extend_schema(
        summary="Consultar historial de movimientos de stock de variante",
        description=(
            "Retorna todos los registros de movimientos de stock (ingresos, mermas, ajustes) "
            "de una variante, ordenados descendentemente por fecha."
        ),
        responses={
            200: StockMovementSerializer(many=True),
        },
    )
    def get(self, request, variant_id: int, product_id: int | None = None):
        if product_id is not None:
            get_object_or_404(ProductVariant, id=variant_id, product_id=product_id)
        else:
            get_object_or_404(ProductVariant, id=variant_id)

        movements = (
            StockMovement.objects.filter(variant_id=variant_id)
            .select_related("admin")
            .order_by("-created_at", "-id")
        )
        serializer = StockMovementSerializer(movements, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
