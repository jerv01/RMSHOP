from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.db import connection, transaction
from rest_framework.exceptions import PermissionDenied

from . import clerk_admin
from .clerk import ClerkClaims
from .exceptions import (
    AdminNotFound,
    AlreadyAdmin,
    CannotDeleteLastAdmin,
    CannotDeleteSelf,
    EmailBelongsToCustomer,
    InvalidEmail,
    InvitationPending,
)
from .models import AdminAuditLog, User

# Identificador del bloqueo consultivo que serializa las bajas de administradores.
ADMIN_REMOVAL_LOCK_ID = 7_201_212


def get_or_create_user_from_claims(claims: ClerkClaims) -> User:
    """Obtiene el usuario local de la sesión; lo crea en la primera petición.

    `get_or_create` es seguro ante peticiones simultáneas: si otra inserta primero,
    captura el IntegrityError y devuelve la fila existente.
    """
    user, _ = User.objects.get_or_create(
        clerk_user_id=claims.sub,
        defaults={
            "email": claims.email,
            "first_name": claims.first_name,
            "last_name": claims.last_name,
        },
    )
    return user


def _profile_from_webhook(data: dict) -> dict:
    """Extrae correo principal y nombres del usuario de un evento de Clerk."""
    profile = {
        "first_name": data.get("first_name") or "",
        "last_name": data.get("last_name") or "",
    }
    primary_id = data.get("primary_email_address_id")
    for address in data.get("email_addresses") or []:
        if address.get("id") == primary_id:
            profile["email"] = address.get("email_address") or ""
    return profile


def _user_created(data: dict) -> None:
    if not data.get("id"):
        return
    _, created = User.objects.get_or_create(
        clerk_user_id=data["id"], defaults=_profile_from_webhook(data)
    )
    is_admin = (data.get("public_metadata") or {}).get("role") == clerk_admin.ADMIN_ROLE
    if created and not is_admin:
        # TODO(HU-43): disparar aquí el correo de bienvenida. HU-12: no se envía a las cuentas
        # con `public_metadata.role == "admin"` (llegan por invitación, no son clientes).
        pass


def _user_updated(data: dict) -> None:
    if not data.get("id"):
        return
    # Si el evento llega antes de la primera petición del usuario, se crea el registro.
    User.objects.update_or_create(clerk_user_id=data["id"], defaults=_profile_from_webhook(data))


def _user_deleted(data: dict) -> None:
    # No se borra la fila: `stock_movements.admin_id`, `order_status_history.changed_by` y los
    # pedidos deben conservar su historial. Se vacían los datos personales y se conserva el
    # `clerk_user_id`, que Clerk no reutiliza.
    User.objects.filter(clerk_user_id=data.get("id")).update(email="", first_name="", last_name="")


_EVENT_HANDLERS = {
    "user.created": _user_created,
    "user.updated": _user_updated,
    "user.deleted": _user_deleted,
}


def handle_clerk_event(event: dict) -> None:
    """Procesa un evento de Clerk ya verificado; los eventos desconocidos se ignoran."""
    handler = _EVENT_HANDLERS.get(event.get("type"))
    if handler:
        handler(event.get("data") or {})


def normalize_email(raw) -> str:
    """Recorta, pasa a minúsculas y valida el formato; lanza `InvalidEmail` si no es válido."""
    email = raw.strip().lower() if isinstance(raw, str) else ""
    try:
        validate_email(email)
    except DjangoValidationError as exc:
        raise InvalidEmail() from exc
    return email


def invite_administrator(*, actor: User, email: str) -> str:
    """Invita a `email` como administrador (HU-12). Devuelve el correo normalizado.

    Solo se invita a un correo sin cuenta en Clerk: nunca se asigna el rol a un usuario
    existente. Clerk copia `public_metadata.role` al usuario cuando acepta la invitación.
    """
    email = normalize_email(email)

    accounts = clerk_admin.find_accounts_by_email(email)
    if any(account.is_admin for account in accounts):
        raise AlreadyAdmin()
    if accounts:
        raise EmailBelongsToCustomer()
    if clerk_admin.has_pending_invitation(email):
        raise InvitationPending()

    redirect_url = f"{settings.FRONTEND_BASE_URL.rstrip('/')}/admin/registro"
    try:
        clerk_admin.create_admin_invitation(email, redirect_url)
    except clerk_admin.InvitationAlreadyExists as exc:
        raise InvitationPending() from exc

    AdminAuditLog.objects.create(
        action=AdminAuditLog.Action.INVITED,
        actor=actor,
        actor_email=actor.email,
        target_email=email,
    )
    return email


def remove_administrator(*, actor: User, target_clerk_user_id: str) -> None:
    """Elimina la cuenta de otro administrador (HU-12).

    Todo ocurre bajo un bloqueo consultivo de transacción: dos administradores que se eliminan
    entre sí a la vez no pueden dejar la tienda sin administradores. El registro de auditoría
    se escribe antes de llamar a Clerk; si Clerk falla, la transacción se revierte.
    """
    with transaction.atomic():
        with connection.cursor() as cursor:
            # De transacción (no de sesión): funciona con el Transaction Pooler de Supabase.
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", [ADMIN_REMOVAL_LOCK_ID])

        administrators = clerk_admin.list_administrator_accounts()
        by_id = {account.clerk_user_id: account for account in administrators}

        # El token puede seguir siendo válido ~60 s tras una baja; Clerk es la fuente de verdad.
        if actor.clerk_user_id not in by_id:
            raise PermissionDenied()
        if target_clerk_user_id == actor.clerk_user_id:
            raise CannotDeleteSelf()
        target = by_id.get(target_clerk_user_id)
        if target is None:
            raise AdminNotFound()
        if len(administrators) <= 1:
            raise CannotDeleteLastAdmin()

        AdminAuditLog.objects.create(
            action=AdminAuditLog.Action.REMOVED,
            actor=actor,
            actor_email=actor.email,
            target_email=target.email,
            target_clerk_user_id=target.clerk_user_id,
        )
        try:
            clerk_admin.delete_user(target.clerk_user_id)
        except clerk_admin.ClerkUserNotFound as exc:
            raise AdminNotFound() from exc
