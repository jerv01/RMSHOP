"""Pruebas de `verify_session_token` con tokens firmados localmente (verificación sin red)."""

import time

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.test import RequestFactory

from apps.users.clerk import ClerkClaims, ClerkNotConfigured, TokenVerificationFailed
from apps.users.clerk import verify_session_token as verify

ORIGIN = "http://localhost:5173"


def make_key():
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    public_pem = private.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return private_pem, public_pem.decode()


PRIVATE_PEM, PUBLIC_PEM = make_key()
OTHER_PRIVATE_PEM, _ = make_key()


def make_token(private_pem=PRIVATE_PEM, **overrides):
    now = int(time.time())
    payload = {
        "sub": "user_1",
        "azp": ORIGIN,
        "iat": now,
        "nbf": now,
        "exp": now + 60,
        "email": "ana@example.com",
        "first_name": "Ana",
        "last_name": None,
        "role": "admin",
    } | overrides
    return jwt.encode(payload, private_pem, algorithm="RS256", headers={"kid": "ins_test"})


def request_with(token):
    return RequestFactory().get("/", HTTP_AUTHORIZATION=f"Bearer {token}")


@pytest.fixture(autouse=True)
def clerk_settings(settings):
    settings.CLERK_SECRET_KEY = ""
    settings.CLERK_JWT_KEY = PUBLIC_PEM
    settings.CLERK_AUTHORIZED_PARTIES = [ORIGIN]


def test_valid_token_returns_claims():
    claims = verify(request_with(make_token()))

    assert claims == ClerkClaims(
        sub="user_1", email="ana@example.com", first_name="Ana", last_name="", role="admin"
    )


def test_role_is_none_when_claim_is_missing():
    claims = verify(request_with(make_token(role=None)))

    assert claims.role is None


@pytest.mark.parametrize(
    "token",
    [
        make_token(exp=int(time.time()) - 3600, iat=int(time.time()) - 7200),
        make_token(azp="https://otro-sitio.example"),
        make_token(OTHER_PRIVATE_PEM),
        "esto-no-es-un-jwt",
        make_token().replace("e", "E", 3),
    ],
    ids=["expirado", "azp-no-autorizado", "firma-ajena", "no-es-jwt", "alterado"],
)
def test_invalid_token_is_rejected(token):
    with pytest.raises(TokenVerificationFailed):
        verify(request_with(token))


def test_machine_tokens_are_not_accepted():
    with pytest.raises(TokenVerificationFailed):
        verify(request_with("ak_token_de_maquina"))


def test_missing_authorization_header_is_rejected():
    with pytest.raises(TokenVerificationFailed):
        verify(RequestFactory().get("/"))


def test_missing_keys_raise_a_configuration_error(settings):
    settings.CLERK_JWT_KEY = ""

    with pytest.raises(ClerkNotConfigured, match="CLERK_SECRET_KEY"):
        verify(request_with(make_token()))


def test_missing_authorized_parties_raise_a_configuration_error(settings):
    settings.CLERK_AUTHORIZED_PARTIES = []

    with pytest.raises(ClerkNotConfigured, match="CLERK_AUTHORIZED_PARTIES"):
        verify(request_with(make_token()))
