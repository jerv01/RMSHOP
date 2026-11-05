"""Formato de error único de la API: {"code": "...", "message": "...", "fields": {...}}."""

import logging

from django.core.exceptions import (
    PermissionDenied as DjangoPermissionDenied,
)
from django.core.exceptions import (
    ValidationError as DjangoValidationError,
)
from django.http import Http404
from rest_framework import exceptions, status
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class ApiError(exceptions.APIException):
    """Error propio con un mensaje en español apto para mostrar al usuario."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "error"
    default_detail = "Ocurrió un error al procesar la solicitud."

    def __init__(self, detail=None, code=None, fields: dict | None = None):
        super().__init__(detail, code)
        self.fields = fields or {}


class ServiceUnavailable(ApiError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_code = "service_unavailable"
    default_detail = "El servicio no está disponible. Intenta de nuevo más tarde."


# Código y mensaje por excepción de DRF; el orden importa (de lo más específico a lo general).
_DRF_ERRORS = [
    (exceptions.ValidationError, "validation_error", "Los datos enviados no son válidos."),
    (exceptions.ParseError, "parse_error", "No pudimos leer la solicitud."),
    (exceptions.AuthenticationFailed, "authentication_failed", "Tu sesión no es válida o venció."),
    (exceptions.NotAuthenticated, "not_authenticated", "Debes iniciar sesión para continuar."),
    (exceptions.PermissionDenied, "permission_denied", "No tienes permisos para esta acción."),
    (exceptions.NotFound, "not_found", "No encontramos lo que buscas."),
    (exceptions.MethodNotAllowed, "method_not_allowed", "Método no permitido."),
    (exceptions.NotAcceptable, "not_acceptable", "Formato de respuesta no disponible."),
    (exceptions.UnsupportedMediaType, "unsupported_media_type", "Tipo de contenido no admitido."),
    (exceptions.Throttled, "throttled", "Demasiadas solicitudes. Intenta de nuevo más tarde."),
]


def _stringify(detail):
    """Convierte los ErrorDetail de DRF en texto plano, conservando la estructura."""
    if isinstance(detail, dict):
        return {key: _stringify(value) for key, value in detail.items()}
    if isinstance(detail, list):
        return [_stringify(item) for item in detail]
    return str(detail)


def build_error(code: str, message: str, fields: dict | None = None) -> dict:
    return {"code": code, "message": message, "fields": fields or {}}


def api_exception_handler(exc, context):
    if isinstance(exc, Http404):
        exc = exceptions.NotFound()
    elif isinstance(exc, DjangoPermissionDenied):
        exc = exceptions.PermissionDenied()
    elif isinstance(exc, DjangoValidationError):
        detail = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
        exc = exceptions.ValidationError(detail=detail)

    if not isinstance(exc, exceptions.APIException):
        # Error inesperado: se registra con el detalle técnico y al usuario no se le muestra.
        logger.exception("Error no controlado en la API", exc_info=exc)
        return Response(
            build_error("internal_error", "Ocurrió un error inesperado. Intenta de nuevo."),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Importación diferida: rest_framework.views carga la clase de autenticación, que importa
    # este módulo.
    from rest_framework.views import set_rollback

    set_rollback()

    if isinstance(exc, ApiError):
        code, message = exc.get_codes(), str(exc.detail)
    else:
        code, message = next(
            (
                (known_code, known_message)
                for cls, known_code, known_message in _DRF_ERRORS
                if isinstance(exc, cls)
            ),
            ("error", "Ocurrió un error al procesar la solicitud."),
        )

    fields = {}
    if isinstance(exc, ApiError):
        fields = exc.fields
    elif isinstance(exc, exceptions.ValidationError):
        detail = _stringify(exc.detail)
        fields = detail if isinstance(detail, dict) else {"non_field_errors": detail}

    headers = {}
    if auth_header := getattr(exc, "auth_header", None):
        headers["WWW-Authenticate"] = auth_header
    if wait := getattr(exc, "wait", None):
        headers["Retry-After"] = str(int(wait))

    return Response(build_error(code, message, fields), status=exc.status_code, headers=headers)
