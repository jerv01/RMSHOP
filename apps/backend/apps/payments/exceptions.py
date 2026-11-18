from rest_framework import status

from apps.core.exceptions import ApiError, ServiceUnavailable


class PaymentGatewayNotConfigured(ServiceUnavailable):
    default_code = "payment_gateway_not_configured"
    default_detail = "Los pagos no están disponibles en este momento. Intenta más tarde."


class PaymentGatewayUnavailable(ServiceUnavailable):
    """MercadoPago no respondió a tiempo o falló (AC-HU-21-2). El pedido sigue pendiente."""

    default_code = "payment_gateway_unavailable"
    default_detail = (
        "No pudimos comunicarnos con el servicio de pagos. Tu pedido sigue pendiente de pago; "
        "intenta de nuevo en unos minutos."
    )


class PaymentRequestRejected(ApiError):
    """MercadoPago rechazó la solicitud por datos inválidos (no es un rechazo del banco)."""

    default_code = "payment_request_invalid"
    default_detail = "No pudimos procesar los datos del pago. Revísalos e intenta de nuevo."


class PaymentAlreadyInProgress(ApiError):
    """Ya hay un pago activo para el pedido; un segundo intento no genera otro cobro."""

    status_code = status.HTTP_409_CONFLICT
    default_code = "payment_already_in_progress"
    default_detail = "Este pedido ya tiene un pago en curso o aprobado."


class OrderNotPayable(ApiError):
    status_code = status.HTTP_409_CONFLICT
    default_code = "order_not_payable"
    default_detail = "Este pedido ya no se puede pagar."
