import base64
import json
from datetime import UTC, datetime

import pytest
from svix.webhooks import Webhook

from apps.users.models import User
from apps.users.tests.factories import UserFactory

URL = "/api/v1/webhooks/clerk"
SECRET = "whsec_" + base64.b64encode(b"secreto-de-prueba-0123456789").decode()
OTHER_SECRET = "whsec_" + base64.b64encode(b"otro-secreto-de-prueba-9876").decode()


def user_data(**overrides):
    return {
        "id": "user_1",
        "first_name": "Ana",
        "last_name": "Pérez",
        "primary_email_address_id": "idn_2",
        "email_addresses": [
            {"id": "idn_1", "email_address": "secundario@example.com"},
            {"id": "idn_2", "email_address": "ana@example.com"},
        ],
    } | overrides


def post_event(client, event_type, data, *, secret=SECRET):
    """Envía el evento firmado con Svix sobre el cuerpo exacto que recibe el servidor."""
    body = json.dumps({"type": event_type, "data": data, "object": "event"})
    timestamp = datetime.now(UTC)
    signature = Webhook(secret).sign("msg_1", timestamp, body)
    return client.generic(
        "POST",
        URL,
        body,
        content_type="application/json",
        HTTP_SVIX_ID="msg_1",
        HTTP_SVIX_TIMESTAMP=str(int(timestamp.timestamp())),
        HTTP_SVIX_SIGNATURE=signature,
    )


@pytest.fixture(autouse=True)
def webhook_secret(settings):
    settings.CLERK_WEBHOOK_SECRET = SECRET


@pytest.mark.django_db
def test_user_created_creates_the_user_with_the_primary_email(api_client):
    response = post_event(api_client, "user.created", user_data())

    assert response.status_code == 200
    user = User.objects.get()
    assert (user.clerk_user_id, user.email) == ("user_1", "ana@example.com")
    assert (user.first_name, user.last_name) == ("Ana", "Pérez")


@pytest.mark.django_db
def test_user_created_is_idempotent(api_client):
    post_event(api_client, "user.created", user_data())
    post_event(api_client, "user.created", user_data(first_name="Otro"))

    user = User.objects.get()
    assert user.first_name == "Ana"


@pytest.mark.django_db
def test_user_updated_changes_email_and_names(api_client):
    UserFactory(clerk_user_id="user_1", email="viejo@example.com", first_name="Viejo")

    response = post_event(api_client, "user.updated", user_data(first_name="María", last_name=""))

    assert response.status_code == 200
    user = User.objects.get()
    assert (user.email, user.first_name, user.last_name) == ("ana@example.com", "María", "")


@pytest.mark.django_db
def test_user_updated_creates_the_user_if_it_does_not_exist(api_client):
    post_event(api_client, "user.updated", user_data())

    assert User.objects.filter(clerk_user_id="user_1", email="ana@example.com").exists()


@pytest.mark.django_db
def test_user_deleted_removes_the_user_and_is_idempotent(api_client):
    UserFactory(clerk_user_id="user_1")
    UserFactory(clerk_user_id="user_2")

    first = post_event(api_client, "user.deleted", {"id": "user_1", "deleted": True})
    second = post_event(api_client, "user.deleted", {"id": "user_1", "deleted": True})

    assert first.status_code == second.status_code == 200
    assert list(User.objects.values_list("clerk_user_id", flat=True)) == ["user_2"]


@pytest.mark.django_db
def test_invalid_signature_returns_400_and_changes_nothing(api_client):
    response = post_event(api_client, "user.created", user_data(), secret=OTHER_SECRET)

    assert response.status_code == 400
    assert response.json()["code"] == "invalid_signature"
    assert set(response.json()) == {"code", "message", "fields"}
    assert User.objects.count() == 0


@pytest.mark.django_db
def test_missing_signature_headers_return_400(api_client):
    response = api_client.generic("POST", URL, "{}", content_type="application/json")

    assert response.status_code == 400
    assert response.json()["code"] == "invalid_signature"


@pytest.mark.django_db
def test_unknown_event_is_ignored(api_client):
    response = post_event(api_client, "session.created", {"id": "sess_1"})

    assert response.status_code == 200
    assert User.objects.count() == 0


@pytest.mark.django_db
def test_missing_webhook_secret_explains_the_configuration(api_client, settings):
    settings.CLERK_WEBHOOK_SECRET = ""

    response = api_client.generic("POST", URL, "{}", content_type="application/json")

    assert response.status_code == 503
    assert "CLERK_WEBHOOK_SECRET" in response.json()["message"]
