from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.core.exceptions import ApiError
from apps.orders.views import get_customer_order
from apps.payments.gateways.mercadopago import verify_webhook_signature
from apps.payments.serializers import (
    PaymentResultSerializer,
    PseBankSerializer,
    StartPaymentInputSerializer,
)
from apps.payments.services import (
    handle_mp_webhook,
    list_pse_banks,
    start_payment,
    sync_payment,
)
from apps.users.permissions import IsCustomer


def _client_ip(request) -> str | None:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip() or None
    return request.META.get("REMOTE_ADDR")


def _result(request, order_number: str) -> dict:
    order = get_customer_order(request.user, order_number)
    payment = order.payments.first()
    return PaymentResultSerializer({"order": order, "payment": payment}).data


class OrderPaymentView(APIView):
    """Inicia el pago de un pedido con tarjeta débito o PSE en MercadoPago (HU-19, HU-20)."""

    permission_classes = [IsCustomer]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "payments"

    @extend_schema(
        request=StartPaymentInputSerializer,
        responses={201: PaymentResultSerializer},
        summary="Pagar pedido",
        tags=["Pagos"],
    )
    def post(self, request, order_number: str):
        serializer = StartPaymentInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        method = data.pop("method")
        payer_email = getattr(request.auth, "email", None) or request.user.email
        start_payment(
            user=request.user,
            order_number=order_number,
            method=method,
            data=data,
            payer_email=payer_email,
            ip_address=_client_ip(request),
        )
        return Response(_result(request, order_number), status=status.HTTP_201_CREATED)


class OrderPaymentSyncView(APIView):
    """Consulta en MercadoPago el estado del pago (al volver del banco en PSE)."""

    permission_classes = [IsCustomer]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "payments"

    @extend_schema(
        request=None,
        responses={200: PaymentResultSerializer},
        summary="Actualizar estado del pago",
        tags=["Pagos"],
    )
    def post(self, request, order_number: str):
        sync_payment(user=request.user, order_number=order_number)
        return Response(_result(request, order_number))


class PseBankListView(APIView):
    """Bancos disponibles para pagar con PSE (HU-20)."""

    permission_classes = [IsCustomer]

    @extend_schema(
        responses={200: PseBankSerializer(many=True)},
        summary="Bancos PSE",
        tags=["Pagos"],
    )
    def get(self, request):
        return Response(PseBankSerializer(list_pse_banks(), many=True).data)


class MercadoPagoWebhookView(APIView):
    """Notificaciones de MercadoPago (HU-22, HU-23). Público, protegido por x-signature."""

    authentication_classes: list = []
    permission_classes = [AllowAny]

    @extend_schema(
        request=None, responses={200: None}, summary="Webhook de MercadoPago", tags=["Pagos"]
    )
    def post(self, request):
        data = request.data.get("data") if isinstance(request.data, dict) else None
        data_id = str(request.query_params.get("data.id") or (data or {}).get("id") or "")
        if not verify_webhook_signature(
            signature_header=request.headers.get("x-signature", ""),
            request_id=request.headers.get("x-request-id", ""),
            data_id=data_id,
        ):
            raise ApiError("Firma de notificación inválida.", code="invalid_signature")
        if request.data.get("type") == "order":
            handle_mp_webhook(mp_order_id=data_id)
        return Response({"received": True})
