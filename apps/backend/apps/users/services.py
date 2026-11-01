from .clerk import ClerkClaims
from .models import User


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
    if created:
        # TODO(HU-43): disparar aquí el correo de bienvenida.
        pass


def _user_updated(data: dict) -> None:
    if not data.get("id"):
        return
    # Si el evento llega antes de la primera petición del usuario, se crea el registro.
    User.objects.update_or_create(clerk_user_id=data["id"], defaults=_profile_from_webhook(data))


def _user_deleted(data: dict) -> None:
    # TODO: cuando existan pedidos, decidir entre eliminar y anonimizar al usuario.
    User.objects.filter(clerk_user_id=data.get("id")).delete()


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
