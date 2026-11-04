"""El adaptador contra la API HTTP de Clerk simulada con respx."""

import json

import httpx
import pytest
import respx

from apps.users import clerk_admin
from apps.users.exceptions import ClerkUnavailable

API = "https://api.clerk.com/v1"


@pytest.fixture(autouse=True)
def secret_key(settings):
    settings.CLERK_SECRET_KEY = "sk_test_x"


def clerk_user(user_id, email, role=None, **extra):
    """Usuario con todos los campos obligatorios del esquema del SDK."""
    return {
        "id": user_id,
        "object": "user",
        "external_id": None,
        "primary_email_address_id": "idn_1",
        "primary_phone_number_id": None,
        "primary_web3_wallet_id": None,
        "username": None,
        "first_name": "Ana",
        "last_name": "Pérez",
        "has_image": False,
        "public_metadata": {"role": role} if role else {},
        "email_addresses": [
            {
                "id": "idn_1",
                "object": "email_address",
                "email_address": email,
                "reserved": False,
                "verification": None,
                "linked_to": [],
                "created_at": 1,
                "updated_at": 1,
            }
        ],
        "phone_numbers": [],
        "web3_wallets": [],
        "passkeys": [],
        "password_enabled": True,
        "two_factor_enabled": False,
        "totp_enabled": False,
        "backup_code_enabled": False,
        "mfa_enabled_at": None,
        "mfa_disabled_at": None,
        "external_accounts": [],
        "saml_accounts": [],
        "enterprise_accounts": [],
        "last_sign_in_at": None,
        "banned": False,
        "locked": False,
        "lockout_expires_in_seconds": None,
        "verification_attempts_remaining": None,
        "updated_at": 1,
        "created_at": 1,
        "delete_self_enabled": True,
        "create_organization_enabled": True,
        "last_active_at": None,
        "legal_accepted_at": None,
    } | extra


@respx.mock
def test_find_accounts_filters_by_any_email_of_the_account():
    route = respx.get(f"{API}/users").mock(
        return_value=httpx.Response(200, json=[clerk_user("user_1", "Ana@Example.com", "admin")])
    )

    accounts = clerk_admin.find_accounts_by_email("ana@example.com")

    assert route.calls.last.request.url.params.get_list("email_address") == ["ana@example.com"]
    assert [(a.clerk_user_id, a.email, a.is_admin) for a in accounts] == [
        ("user_1", "ana@example.com", True)
    ]


@respx.mock
def test_list_administrators_paginates_and_filters_by_role(monkeypatch):
    monkeypatch.setattr(clerk_admin, "PAGE_SIZE", 2)
    pages = {
        "0": [clerk_user("u1", "a@x.com", "admin"), clerk_user("u2", "b@x.com")],
        "2": [clerk_user("u3", "c@x.com", "admin")],
    }
    respx.get(f"{API}/users").mock(
        side_effect=lambda request: httpx.Response(200, json=pages[request.url.params["offset"]])
    )

    admins = clerk_admin.list_administrator_accounts()

    assert [a.clerk_user_id for a in admins] == ["u1", "u3"]


@respx.mock
def test_create_invitation_sends_admin_metadata_and_redirect():
    route = respx.post(f"{API}/invitations").mock(
        return_value=httpx.Response(
            200,
            json={
                "object": "invitation",
                "id": "inv_1",
                "email_address": "n@x.com",
                "public_metadata": {"role": "admin"},
                "status": "pending",
                "created_at": 1,
                "updated_at": 1,
            },
        )
    )

    clerk_admin.create_admin_invitation("n@x.com", "http://localhost:5173/admin/registro")

    body = json.loads(route.calls.last.request.content)
    assert body["email_address"] == "n@x.com"
    assert body["public_metadata"] == {"role": "admin"}
    assert body["redirect_url"] == "http://localhost:5173/admin/registro"
    assert body["ignore_existing"] is False


@respx.mock
def test_duplicate_invitation_is_reported_as_already_existing():
    respx.post(f"{API}/invitations").mock(
        return_value=httpx.Response(
            422, json={"errors": [{"code": "duplicate_record", "message": "duplicate"}]}
        )
    )

    with pytest.raises(clerk_admin.InvitationAlreadyExists):
        clerk_admin.create_admin_invitation("n@x.com", "http://x/admin/registro")


@respx.mock
def test_pending_invitation_lookup_matches_the_exact_email():
    respx.get(f"{API}/invitations").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "object": "invitation",
                    "id": "inv_1",
                    "email_address": "otro-n@x.com",
                    "public_metadata": {"role": "admin"},
                    "status": "pending",
                    "created_at": 1,
                    "updated_at": 1,
                }
            ],
        )
    )

    assert clerk_admin.has_pending_invitation("n@x.com") is False


@respx.mock
def test_delete_user_maps_404_and_server_errors():
    respx.delete(f"{API}/users/gone").mock(
        return_value=httpx.Response(404, json={"errors": [{"code": "resource_not_found"}]})
    )
    respx.delete(f"{API}/users/broken").mock(return_value=httpx.Response(500, text="boom"))

    with pytest.raises(clerk_admin.ClerkUserNotFound):
        clerk_admin.delete_user("gone")
    with pytest.raises(ClerkUnavailable):
        clerk_admin.delete_user("broken")


@respx.mock
def test_network_failure_becomes_clerk_unavailable():
    respx.get(f"{API}/users").mock(side_effect=httpx.ConnectError("sin red"))

    with pytest.raises(ClerkUnavailable):
        clerk_admin.list_administrator_accounts()


def test_missing_secret_key_explains_the_configuration(settings):
    settings.CLERK_SECRET_KEY = ""

    with pytest.raises(Exception) as exc:
        clerk_admin.list_administrator_accounts()

    assert "CLERK_SECRET_KEY" in str(exc.value.detail)
