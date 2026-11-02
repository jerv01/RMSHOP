"""Flujo de registro (HU-7) de punta a punta en el backend.

Tras registrarse en Clerk, el cliente llega a la API por dos caminos: el primer `GET /me` con su
token y el webhook `user.created`. Pueden llegar en cualquier orden y la cuenta debe ser una sola.
Clerk se simula (token y firma); ninguna prueba sale a la red.
"""

from unittest.mock import patch

import pytest

from apps.users.clerk import ClerkClaims
from apps.users.models import User
from apps.users.tests.test_webhooks import SECRET, post_event, user_data

ME_URL = "/api/v1/me"
AUTH = {"HTTP_AUTHORIZATION": "Bearer token-simulado"}


@pytest.fixture(autouse=True)
def webhook_secret(settings):
    settings.CLERK_WEBHOOK_SECRET = SECRET


@pytest.fixture
def verify_token():
    with patch("apps.users.authentication.verify_session_token") as mock:
        mock.return_value = ClerkClaims(
            sub="user_1", email="ana@example.com", first_name="Ana", last_name="Pérez"
        )
        yield mock


@pytest.mark.django_db
def test_me_then_webhook_keeps_a_single_account(api_client, verify_token):
    me = api_client.get(ME_URL, **AUTH)
    webhook = post_event(api_client, "user.created", user_data())

    assert me.status_code == 200
    assert webhook.status_code == 200
    assert User.objects.count() == 1
    assert User.objects.get().clerk_user_id == "user_1"


@pytest.mark.django_db
def test_webhook_then_me_reuses_the_account_created_by_the_webhook(api_client, verify_token):
    post_event(api_client, "user.created", user_data())
    created = User.objects.get()

    me = api_client.get(ME_URL, **AUTH)

    assert me.status_code == 200
    assert me.json()["id"] == created.pk
    assert User.objects.count() == 1


@pytest.mark.django_db
def test_new_customer_is_registered_without_a_role(api_client, verify_token):
    response = api_client.get(ME_URL, **AUTH)

    assert response.json()["role"] is None
    assert response.json()["email"] == "ana@example.com"


@pytest.mark.django_db
def test_two_different_customers_get_two_accounts(api_client, verify_token):
    api_client.get(ME_URL, **AUTH)
    verify_token.return_value = ClerkClaims(
        sub="user_2", email="luis@example.com", first_name="Luis", last_name="Gómez"
    )

    api_client.get(ME_URL, **AUTH)

    assert set(User.objects.values_list("email", flat=True)) == {
        "ana@example.com",
        "luis@example.com",
    }
