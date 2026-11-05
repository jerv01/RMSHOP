import smtplib
from datetime import timedelta

import pytest
from anymail.exceptions import AnymailRecipientsRefused
from django.core import mail
from django.core.management import call_command
from django.utils import timezone

from apps.notifications import services
from apps.notifications.models import NotificationLog
from apps.users.clerk import ClerkClaims
from apps.users.services import get_or_create_user_from_claims, handle_clerk_event
from apps.users.tests.factories import UserFactory

S = NotificationLog.Status


def created_event(user_id="user_1", email="ana@example.com", **extra):
    return {
        "type": "user.created",
        "data": {
            "id": user_id,
            "first_name": "Ana",
            "last_name": "Pérez",
            "primary_email_address_id": "idn_1",
            "email_addresses": [{"id": "idn_1", "email_address": email}],
        }
        | extra,
    }


def register(callbacks, event):
    with callbacks(execute=True):
        handle_clerk_event(event)


@pytest.fixture
def callbacks(django_capture_on_commit_callbacks):
    return django_capture_on_commit_callbacks


@pytest.mark.django_db
def test_welcome_email_is_sent_in_spanish_without_password(callbacks):
    register(callbacks, created_event())

    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert message.to == ["ana@example.com"]
    assert message.subject == "Tu cuenta en RM Shop fue creada"
    assert "Hola, Ana." in message.body
    assert "ana@example.com" in message.body
    assert "contraseña" not in message.body.lower()
    assert "http://localhost:5173/ingresar" in message.body
    assert message.alternatives[0][1] == "text/html"
    log = NotificationLog.objects.get()
    assert (log.status, log.attempts, log.sent_at is not None) == (S.SENT, 1, True)


@pytest.mark.django_db
def test_html_escapes_the_name(callbacks):
    register(callbacks, created_event(first_name="<b>Ana</b>"))

    html = mail.outbox[0].alternatives[0][0]
    assert "<b>Ana</b>" not in html
    assert "&lt;b&gt;Ana&lt;/b&gt;" in html


@pytest.mark.django_db
def test_duplicate_events_send_a_single_email(callbacks):
    register(callbacks, created_event())
    register(callbacks, created_event())

    assert len(mail.outbox) == 1
    assert NotificationLog.objects.count() == 1


@pytest.mark.django_db
def test_first_request_then_webhook_sends_a_single_email(callbacks):
    claims = ClerkClaims(sub="user_1", email="ana@example.com", first_name="Ana")
    with callbacks(execute=True):
        get_or_create_user_from_claims(claims)
    register(callbacks, created_event())

    assert len(mail.outbox) == 1


@pytest.mark.django_db
def test_admin_accounts_do_not_receive_the_customer_welcome(callbacks):
    register(callbacks, created_event(public_metadata={"role": "admin"}))
    with callbacks(execute=True):
        get_or_create_user_from_claims(
            ClerkClaims(sub="user_2", email="admin@rmshop.test", role="admin")
        )

    assert mail.outbox == []
    assert NotificationLog.objects.count() == 0


@pytest.mark.django_db
def test_user_without_email_is_skipped(callbacks):
    with callbacks(execute=True):
        assert services.send_welcome_email(UserFactory(email="")) is None

    assert NotificationLog.objects.count() == 0


@pytest.fixture
def failing_send(monkeypatch):
    state = {"error": smtplib.SMTPServerDisconnected("sin conexión")}

    def send(self, fail_silently=False):
        if state["error"]:
            raise state["error"]
        mail.outbox.append(self)
        return 1

    monkeypatch.setattr("django.core.mail.EmailMultiAlternatives.send", send)
    return state


@pytest.mark.django_db
def test_temporary_failure_keeps_the_registration_and_is_retried(callbacks, failing_send):
    register(callbacks, created_event())  # No lanza: el registro no se pierde (AC-2).

    log = NotificationLog.objects.get()
    assert (log.status, log.attempts) == (S.FAILED, 1)
    assert "SMTPServerDisconnected" in log.last_error
    assert mail.outbox == []

    # Aún dentro de la espera: no se reintenta.
    assert services.retry_failed_notifications() == 0

    NotificationLog.objects.update(last_attempt_at=timezone.now() - timedelta(minutes=2))
    failing_send["error"] = None
    call_command("retry_failed_emails")

    log.refresh_from_db()
    assert (log.status, log.attempts, log.last_error) == (S.SENT, 2, "")
    assert len(mail.outbox) == 1


@pytest.mark.django_db
def test_attempts_are_capped(callbacks, failing_send):
    register(callbacks, created_event())
    for _ in range(services.MAX_ATTEMPTS):
        NotificationLog.objects.update(last_attempt_at=timezone.now() - timedelta(minutes=2))
        services.retry_failed_notifications()

    log = NotificationLog.objects.get()
    assert (log.status, log.attempts) == (S.UNDELIVERABLE, services.MAX_ATTEMPTS)
    assert services.retry_failed_notifications() == 0


@pytest.mark.django_db
@pytest.mark.parametrize(
    "error",
    [
        smtplib.SMTPRecipientsRefused({"x@no-existe.invalid": (550, b"no such domain")}),
        smtplib.SMTPResponseException(553, b"mailbox name not allowed"),
        AnymailRecipientsRefused("rechazado"),
    ],
    ids=["destinatarios-rechazados", "smtp-5xx", "anymail"],
)
def test_nonexistent_domain_is_logged_without_retries_or_affecting_others(
    callbacks, failing_send, error
):
    failing_send["error"] = error
    register(callbacks, created_event("user_bad", "x@no-existe.invalid"))
    failing_send["error"] = None
    register(callbacks, created_event("user_ok", "ok@example.com"))

    bad = NotificationLog.objects.get(user__clerk_user_id="user_bad")
    good = NotificationLog.objects.get(user__clerk_user_id="user_ok")
    assert (bad.status, bad.attempts) == (S.UNDELIVERABLE, 1)
    assert bad.last_error
    assert good.status == S.SENT
    assert [m.to for m in mail.outbox] == [["ok@example.com"]]
    NotificationLog.objects.update(last_attempt_at=timezone.now() - timedelta(minutes=2))
    assert services.retry_failed_notifications() == 0
