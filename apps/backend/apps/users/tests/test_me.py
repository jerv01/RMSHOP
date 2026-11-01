from unittest.mock import patch

import pytest

from apps.users.clerk import ClerkClaims, TokenVerificationFailed
from apps.users.models import User

URL = "/api/v1/me"
AUTH = {"HTTP_AUTHORIZATION": "Bearer token-simulado"}


def make_claims(**overrides):
    values = {
        "sub": "user_1",
        "email": "ana@example.com",
        "first_name": "Ana",
        "last_name": "Pérez",
    }
    return ClerkClaims(**(values | overrides))


@pytest.fixture
def verify_token():
    """Simula la verificación del token: ninguna prueba llama a Clerk."""
    with patch("apps.users.authentication.verify_session_token") as mock:
        mock.return_value = make_claims()
        yield mock


@pytest.mark.django_db
def test_me_without_token_returns_401_with_common_format(api_client):
    response = api_client.get(URL)

    assert response.status_code == 401
    assert response.json() == {
        "code": "not_authenticated",
        "message": "Debes iniciar sesión para continuar.",
        "fields": {},
    }
    assert response["WWW-Authenticate"].startswith("Bearer")


@pytest.mark.django_db
def test_me_with_token_creates_user_once(api_client, verify_token):
    first = api_client.get(URL, **AUTH)
    second = api_client.get(URL, **AUTH)

    assert first.status_code == 200
    assert first.json() == {
        "id": User.objects.get().pk,
        "email": "ana@example.com",
        "first_name": "Ana",
        "last_name": "Pérez",
        "role": None,
    }
    assert second.json() == first.json()
    assert User.objects.count() == 1


@pytest.mark.django_db
def test_me_returns_role_from_token(api_client, verify_token):
    verify_token.return_value = make_claims(role="admin")

    response = api_client.get(URL, **AUTH)

    assert response.json()["role"] == "admin"


@pytest.mark.django_db
def test_me_with_invalid_token_returns_401(api_client, verify_token):
    verify_token.side_effect = TokenVerificationFailed("Token has expired")

    response = api_client.get(URL, **AUTH)

    assert response.status_code == 401
    assert response.json()["code"] == "authentication_failed"
    assert User.objects.count() == 0


@pytest.mark.django_db
def test_me_without_clerk_keys_explains_the_configuration(api_client, settings):
    settings.CLERK_SECRET_KEY = ""
    settings.CLERK_JWT_KEY = ""

    response = api_client.get(URL, **AUTH)

    assert response.status_code == 503
    body = response.json()
    assert body["code"] == "clerk_not_configured"
    assert "CLERK_SECRET_KEY" in body["message"]
    assert "docs/clerk-setup.md" in body["message"]
