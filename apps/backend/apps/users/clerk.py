"""Único punto de contacto con Clerk (`clerk-backend-api` y `svix`).

El resto del código y las pruebas dependen de `verify_session_token` y `verify_webhook`,
no de los SDK, para poder simularlos.
"""

import json
from dataclasses import dataclass

from clerk_backend_api.security import authenticate_request
from clerk_backend_api.security.types import AuthenticateRequestOptions
from django.conf import settings
from rest_framework import status
from svix.webhooks import Webhook, WebhookVerificationError

from apps.core.exceptions import ApiError


class ClerkNotConfigured(ApiError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_code = "clerk_not_configured"
    default_detail = "Clerk no está configurado."


class TokenVerificationFailed(Exception):
    """El token no existe, es inválido, venció o no pertenece al origen autorizado."""


class InvalidWebhookSignature(ApiError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "invalid_signature"
    default_detail = "La firma del webhook no es válida."


@dataclass(frozen=True)
class ClerkClaims:
    """Claims del token de sesión que usa la API (plantilla de sesión en docs/clerk-setup.md)."""

    sub: str
    email: str = ""
    first_name: str = ""
    last_name: str = ""
    role: str | None = None


class _AuthorizationOnly:
    """Expone solo la cabecera Authorization: el SDK también lee la cookie `__session`."""

    def __init__(self, authorization: str):
        self.headers = {"Authorization": authorization}


def verify_session_token(request) -> ClerkClaims:
    """Valida el token Bearer de la petición y devuelve sus claims.

    Verifica firma, expiración y `azp` contra CLERK_AUTHORIZED_PARTIES. Con CLERK_JWT_KEY
    no hace llamadas de red; si no, el SDK obtiene las claves públicas con CLERK_SECRET_KEY.
    """
    if not settings.CLERK_JWT_KEY and not settings.CLERK_SECRET_KEY:
        raise ClerkNotConfigured(
            "Falta CLERK_SECRET_KEY en apps/backend/.env. Consulta docs/clerk-setup.md."
        )
    if not settings.CLERK_AUTHORIZED_PARTIES:
        raise ClerkNotConfigured(
            "Falta CLERK_AUTHORIZED_PARTIES en apps/backend/.env. Consulta docs/clerk-setup.md."
        )

    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise TokenVerificationFailed("Falta el token Bearer.")

    options = AuthenticateRequestOptions(
        secret_key=settings.CLERK_SECRET_KEY or None,
        jwt_key=settings.CLERK_JWT_KEY or None,
        authorized_parties=settings.CLERK_AUTHORIZED_PARTIES,
        accepts_token=["session_token"],
    )
    state = authenticate_request(_AuthorizationOnly(f"Bearer {token.strip()}"), options)
    if not state.is_signed_in or not state.payload or not state.payload.get("sub"):
        raise TokenVerificationFailed(state.message or "Token inválido.")

    payload = state.payload
    return ClerkClaims(
        sub=payload["sub"],
        email=payload.get("email") or "",
        first_name=payload.get("first_name") or "",
        last_name=payload.get("last_name") or "",
        role=payload.get("role") or None,
    )


def verify_webhook(body: bytes, headers) -> dict:
    """Verifica la firma Svix sobre el cuerpo crudo y devuelve el evento ya decodificado."""
    if not settings.CLERK_WEBHOOK_SECRET:
        raise ClerkNotConfigured(
            "Falta CLERK_WEBHOOK_SECRET en apps/backend/.env. Consulta docs/clerk-setup.md."
        )
    svix_headers = {
        name: headers.get(name, "") for name in ("svix-id", "svix-timestamp", "svix-signature")
    }
    try:
        Webhook(settings.CLERK_WEBHOOK_SECRET).verify(body, svix_headers)
        event = json.loads(body)
    except (WebhookVerificationError, ValueError) as exc:
        raise InvalidWebhookSignature() from exc
    if not isinstance(event, dict):
        raise InvalidWebhookSignature()
    return event
