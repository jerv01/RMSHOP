"""Adaptador de Clerk para gestionar cuentas de administrador (HU-12).

Aísla las llamadas a `clerk-backend-api` (usuarios e invitaciones) para que el servicio y las
pruebas dependan de estas funciones y no del SDK, igual que `clerk.py` con la verificación
de tokens. Las pruebas reemplazan este módulo por una versión en memoria.
"""

import logging
from collections.abc import Iterator
from dataclasses import dataclass, field

from clerk_backend_api import Clerk
from clerk_backend_api.models import (
    ClerkBaseError,
    CreateInvitationRequestBody,
    GetUserListRequest,
)
from clerk_backend_api.models.listinvitationsop import ListInvitationsQueryParamStatus
from clerk_backend_api.utils.retries import BackoffStrategy, RetryConfig
from django.conf import settings

from .clerk import ClerkNotConfigured
from .exceptions import ClerkUnavailable

logger = logging.getLogger(__name__)

PAGE_SIZE = 500  # Máximo que admite Clerk por página.
ADMIN_ROLE = "admin"

# El SDK reintenta los 5xx con una espera total de hasta una hora por defecto: con la petición
# (y el bloqueo de la baja) abiertos, se acota a pocos segundos.
REQUEST_TIMEOUT_MS = 8_000
_RETRY = RetryConfig(
    "backoff",
    BackoffStrategy(initial_interval=200, max_interval=1_000, exponent=1.5, max_elapsed_time=3_000),
    retry_connection_errors=True,
)


@dataclass(frozen=True)
class ClerkAccount:
    """Datos de una cuenta de Clerk que necesita la gestión de administradores."""

    clerk_user_id: str
    email: str
    first_name: str = ""
    last_name: str = ""
    role: str | None = None
    emails: tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_admin(self) -> bool:
        return self.role == ADMIN_ROLE


class ClerkUserNotFound(Exception):
    """Clerk no tiene el usuario (por ejemplo, ya se eliminó)."""


class InvitationAlreadyExists(Exception):
    """Clerk rechazó la invitación porque ya hay una para ese correo."""


def _client() -> Clerk:
    if not settings.CLERK_SECRET_KEY:
        raise ClerkNotConfigured(
            "Falta CLERK_SECRET_KEY en apps/backend/.env. Consulta docs/clerk-setup.md."
        )
    return Clerk(
        bearer_auth=settings.CLERK_SECRET_KEY, retry_config=_RETRY, timeout_ms=REQUEST_TIMEOUT_MS
    )


def _account_from_user(user) -> ClerkAccount:
    addresses = user.email_addresses or []
    emails = tuple(a.email_address.lower() for a in addresses)
    primary = next(
        (a.email_address for a in addresses if a.id == user.primary_email_address_id),
        addresses[0].email_address if addresses else "",
    )
    metadata = user.public_metadata or {}
    role = metadata.get("role")
    return ClerkAccount(
        clerk_user_id=user.id,
        email=primary.lower(),
        first_name=user.first_name or "",
        last_name=user.last_name or "",
        role=role if isinstance(role, str) else None,
        emails=emails,
    )


def _unavailable(exc: Exception) -> ClerkUnavailable:
    # El detalle técnico va al registro; al usuario solo le llega un mensaje genérico.
    logger.warning("Falló una llamada a Clerk: %s", exc, exc_info=exc)
    return ClerkUnavailable()


def find_accounts_by_email(email: str) -> list[ClerkAccount]:
    """Cuentas que tienen `email` entre sus correos (no solo el principal)."""
    try:
        with _client() as clerk:
            users = clerk.users.list(
                request=GetUserListRequest(email_address=[email], limit=PAGE_SIZE)
            )
    except ClerkNotConfigured:
        raise
    except Exception as exc:
        raise _unavailable(exc) from exc
    return [_account_from_user(user) for user in users]


def _iter_all_accounts(clerk: Clerk) -> Iterator[ClerkAccount]:
    offset = 0
    while True:
        page = clerk.users.list(
            request=GetUserListRequest(limit=PAGE_SIZE, offset=offset, order_by="created_at")
        )
        yield from (_account_from_user(user) for user in page)
        if len(page) < PAGE_SIZE:
            return
        offset += PAGE_SIZE


def list_administrator_accounts() -> list[ClerkAccount]:
    """Todas las cuentas con `public_metadata.role == "admin"`.

    Clerk no filtra `users.list` por metadata, así que se recorren todos los usuarios y se
    filtra aquí: O(n) sobre los usuarios de la instancia, aceptable con el volumen de la tienda
    (menos de cientos de cuentas). Migrar a una tabla local de administradores (sincronizada
    con los webhooks `user.updated`) si la lista tarda más de ~1 s o la instancia pasa de unos
    pocos miles de usuarios.
    """
    try:
        with _client() as clerk:
            return [account for account in _iter_all_accounts(clerk) if account.is_admin]
    except ClerkNotConfigured:
        raise
    except Exception as exc:
        raise _unavailable(exc) from exc


def has_pending_invitation(email: str) -> bool:
    try:
        with _client() as clerk:
            offset = 0
            while True:
                page = clerk.invitations.list(
                    status=ListInvitationsQueryParamStatus.PENDING,
                    query=email,
                    limit=PAGE_SIZE,
                    offset=offset,
                )
                if any((i.email_address or "").lower() == email for i in page):
                    return True
                if len(page) < PAGE_SIZE:
                    return False
                offset += PAGE_SIZE
    except ClerkNotConfigured:
        raise
    except Exception as exc:
        raise _unavailable(exc) from exc


def create_admin_invitation(email: str, redirect_url: str) -> None:
    """Invita a `email`; Clerk copia `public_metadata.role` al usuario cuando acepta."""
    try:
        with _client() as clerk:
            clerk.invitations.create(
                retries=None,  # Un reintento tras éxito duplicaría la invitación.
                request=CreateInvitationRequestBody(
                    email_address=email,
                    public_metadata={"role": ADMIN_ROLE},
                    redirect_url=redirect_url,
                    ignore_existing=False,
                ),
            )
    except ClerkNotConfigured:
        raise
    except ClerkBaseError as exc:
        if exc.status_code in (409, 422) and "duplicate" in (exc.body or "").lower():
            raise InvitationAlreadyExists() from exc
        raise _unavailable(exc) from exc
    except Exception as exc:
        raise _unavailable(exc) from exc


def delete_user(clerk_user_id: str) -> None:
    """Elimina la cuenta en Clerk; sus sesiones dejan de renovarse."""
    try:
        with _client() as clerk:
            # Sin reintentos: borrar no es idempotente (un reintento tras éxito daría 404).
            clerk.users.delete(user_id=clerk_user_id, retries=None)
    except ClerkNotConfigured:
        raise
    except ClerkBaseError as exc:
        if exc.status_code == 404:
            raise ClerkUserNotFound() from exc
        raise _unavailable(exc) from exc
    except Exception as exc:
        raise _unavailable(exc) from exc
