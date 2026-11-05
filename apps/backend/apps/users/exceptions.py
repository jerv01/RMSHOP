"""Errores de la gestión de administradores (HU-12), en el formato único de la API."""

from rest_framework import status

from apps.core.exceptions import ApiError


class InvalidEmail(ApiError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "invalid_email"
    default_detail = "Ingresa un correo válido."

    def __init__(self, detail=None, code=None):
        super().__init__(detail, code, fields={"email": [str(self.default_detail)]})


class EmailBelongsToCustomer(ApiError):
    status_code = status.HTTP_409_CONFLICT
    default_code = "email_belongs_to_customer"
    default_detail = "Este correo pertenece a una cuenta de cliente."


class AlreadyAdmin(ApiError):
    status_code = status.HTTP_409_CONFLICT
    default_code = "already_admin"
    default_detail = "Este correo ya es de un administrador."


class InvitationPending(ApiError):
    status_code = status.HTTP_409_CONFLICT
    default_code = "invitation_pending"
    default_detail = "Ya hay una invitación pendiente para este correo."


class CannotDeleteSelf(ApiError):
    status_code = status.HTTP_409_CONFLICT
    default_code = "cannot_delete_self"
    default_detail = "No puedes eliminar tu propia cuenta."


class CannotDeleteLastAdmin(ApiError):
    status_code = status.HTTP_409_CONFLICT
    default_code = "cannot_delete_last_admin"
    default_detail = "No se puede eliminar la última cuenta de administrador."


class AdminNotFound(ApiError):
    status_code = status.HTTP_404_NOT_FOUND
    default_code = "admin_not_found"
    default_detail = "No encontramos a ese administrador."


class ClerkUnavailable(ApiError):
    status_code = status.HTTP_502_BAD_GATEWAY
    default_code = "clerk_unavailable"
    default_detail = "No pudimos completar la operación, intenta de nuevo."
