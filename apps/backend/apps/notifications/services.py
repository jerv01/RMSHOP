"""Envío de correos transaccionales (HU-43)."""

import logging
import smtplib
from datetime import timedelta

from anymail.exceptions import AnymailAPIError, AnymailRecipientsRefused
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.html import escape

from apps.users.models import User

from .models import NotificationLog

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 5
RETRY_AFTER = timedelta(seconds=60)


def _is_permanent(exc: Exception) -> bool:
    """Errores que no se arreglan reintentando: dominio inexistente o destinatario rechazado."""
    if isinstance(exc, smtplib.SMTPRecipientsRefused | AnymailRecipientsRefused):
        return True
    if isinstance(exc, smtplib.SMTPResponseException):
        return 500 <= exc.smtp_code < 600
    if isinstance(exc, AnymailAPIError):
        status = getattr(exc, "status_code", None)
        return status is not None and 400 <= status < 500 and status not in (408, 429)
    return False


def _welcome_message(user: User) -> EmailMultiAlternatives:
    name = user.first_name or "cliente"
    login_url = f"{settings.FRONTEND_BASE_URL.rstrip('/')}/ingresar"
    text = (
        f"Hola, {name}.\n\n"
        f"Tu cuenta en RM Shop fue creada con el correo {user.email}.\n"
        f"Ya puedes iniciar sesión y comprar: {login_url}\n\n"
        "Si no creaste esta cuenta, ignora este mensaje.\n\n"
        "El equipo de RM Shop"
    )
    html = (
        f"<p>Hola, {escape(name)}.</p>"
        f"<p>Tu cuenta en RM Shop fue creada con el correo <strong>{escape(user.email)}</strong>."
        f'</p><p><a href="{escape(login_url)}">Inicia sesión y compra</a></p>'
        "<p>Si no creaste esta cuenta, ignora este mensaje.</p><p>El equipo de RM Shop</p>"
    )
    message = EmailMultiAlternatives(
        subject="Tu cuenta en RM Shop fue creada",
        body=text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    message.attach_alternative(html, "text/html")
    return message


def _deliver(log_id: int) -> None:
    """Envía un correo pendiente o fallido. Nunca lanza: el resultado queda en el registro."""
    with transaction.atomic():
        # El bloqueo de fila evita que dos procesos envíen el mismo correo a la vez.
        log = NotificationLog.objects.select_for_update().select_related("user").get(pk=log_id)
        if log.status not in (NotificationLog.Status.PENDING, NotificationLog.Status.FAILED):
            return
        log.attempts += 1
        log.last_attempt_at = timezone.now()
        try:
            _welcome_message(log.user).send(fail_silently=False)
        except Exception as exc:
            permanent = _is_permanent(exc)
            exhausted = log.attempts >= MAX_ATTEMPTS
            log.status = (
                NotificationLog.Status.UNDELIVERABLE
                if permanent or exhausted
                else NotificationLog.Status.FAILED
            )
            log.last_error = f"{type(exc).__name__}: {exc}"[:1000]
            logger.warning("No se pudo enviar el correo %s: %s", log.pk, log.last_error)
        else:
            log.status = NotificationLog.Status.SENT
            log.sent_at = log.last_attempt_at
            log.last_error = ""
        log.save()


def send_welcome_email(user: User) -> NotificationLog | None:
    """Envía el correo de bienvenida a un cliente una sola vez (HU-43).

    El envío se programa para después de confirmar la transacción. Un fallo no afecta a quien
    llama: queda en `notification_log` y `retry_failed_notifications` lo reintenta.
    """
    if not user.email:
        return None
    log, created = NotificationLog.objects.get_or_create(
        user=user, event=NotificationLog.Event.WELCOME
    )
    if created:
        transaction.on_commit(lambda: _deliver(log.pk))
    return log


def retry_failed_notifications() -> int:
    """Reintenta los correos fallidos con intentos disponibles. Devuelve cuántos reintentó."""
    cutoff = timezone.now() - RETRY_AFTER
    due = NotificationLog.objects.filter(
        Q(
            status=NotificationLog.Status.FAILED,
            attempts__lt=MAX_ATTEMPTS,
            last_attempt_at__lt=cutoff,
        )
        # Pendientes que nunca se intentaron (por ejemplo, el proceso cayó antes de enviar).
        | Q(status=NotificationLog.Status.PENDING, created_at__lt=cutoff)
    )
    ids = list(due.order_by("pk").values_list("pk", flat=True))
    for log_id in ids:
        _deliver(log_id)
    return len(ids)
