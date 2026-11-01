from rest_framework.permissions import BasePermission


class IsCustomer(BasePermission):
    """Usuario autenticado.

    Supone que Clerk exige verificar el correo al registrarse (docs/clerk-setup.md), así que
    toda sesión válida ya es de un correo verificado.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class IsRMAdmin(BasePermission):
    """Usuario autenticado cuyo token trae `role == "admin"` (`public_metadata.role` en Clerk).

    El rol se lee del token en cada petición; no se guarda en la base local.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.auth, "role", None) == "admin"
        )
