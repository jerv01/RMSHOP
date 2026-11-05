import threading
from unittest.mock import patch

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.users import services
from apps.users.clerk import ClerkClaims
from apps.users.models import AdminAuditLog, User
from apps.users.tests.factories import UserFactory
from apps.users.tests.fake_clerk import FakeClerk

URL = "/api/v1/admin/administrators"
AUTH = {"HTTP_AUTHORIZATION": "Bearer token-simulado"}


@pytest.fixture
def clerk(monkeypatch):
    fake = FakeClerk()
    fake.add("user_me", "yo@rmshop.test", role="admin", first_name="Yo", last_name="Admin")
    fake.add("user_other", "otra@rmshop.test", role="admin", first_name="Otra", last_name="Admin")
    fake.add("user_customer", "cliente@example.com", first_name="Cli", last_name="Ente")
    fake.install(monkeypatch)
    return fake


@pytest.fixture
def login():
    """Autentica la petición como `user_me` con el rol indicado, sin llamar a Clerk."""
    with patch("apps.users.authentication.verify_session_token") as mock:

        def _login(role="admin", sub="user_me", email="yo@rmshop.test"):
            mock.return_value = ClerkClaims(sub=sub, email=email, role=role)

        yield _login


@pytest.fixture
def admin_client(api_client, login, clerk):
    login()
    return api_client


# --- AC-HU-12-1 -----------------------------------------------------------------------


@pytest.mark.django_db
def test_invite_creates_invitation_with_admin_role_and_audit_log(admin_client, clerk, settings):
    settings.FRONTEND_BASE_URL = "http://localhost:5173/"

    response = admin_client.post(URL, {"email": "  Nuevo@RMShop.test "}, **AUTH)

    assert response.status_code == 201
    assert response.json() == {"status": "invited", "email": "nuevo@rmshop.test"}
    assert clerk.invitations_created == [
        {
            "email": "nuevo@rmshop.test",
            "redirect_url": "http://localhost:5173/admin/registro",
            "public_metadata": {"role": "admin"},
        }
    ]
    log = AdminAuditLog.objects.get()
    assert (log.action, log.actor_email, log.target_email) == (
        "admin_invited",
        "yo@rmshop.test",
        "nuevo@rmshop.test",
    )
    assert log.actor == User.objects.get(clerk_user_id="user_me")
    assert log.target_clerk_user_id is None


@pytest.mark.django_db
@pytest.mark.parametrize("email", ["", "no-es-correo", "a@", None, 123])
def test_invite_rejects_invalid_email(admin_client, clerk, email):
    response = admin_client.post(URL, {"email": email}, **AUTH)

    assert response.status_code == 400
    body = response.json()
    assert body["code"] == "invalid_email"
    assert body["fields"]["email"]
    assert clerk.invitations_created == []
    assert AdminAuditLog.objects.count() == 0


# --- AC-HU-12-2 -----------------------------------------------------------------------


@pytest.mark.django_db
def test_invite_customer_email_is_rejected(admin_client, clerk):
    response = admin_client.post(URL, {"email": "Cliente@example.com"}, **AUTH)

    assert response.status_code == 409
    assert response.json()["code"] == "email_belongs_to_customer"
    assert "cliente" in response.json()["message"]
    assert clerk.invitations_created == []
    assert clerk.accounts["user_customer"].role is None
    assert AdminAuditLog.objects.count() == 0


@pytest.mark.django_db
def test_invite_secondary_email_of_a_customer_is_rejected(admin_client, clerk):
    clerk.accounts["user_customer"] = clerk.accounts["user_customer"].__class__(
        clerk_user_id="user_customer",
        email="cliente@example.com",
        emails=("cliente@example.com", "segundo@example.com"),
    )

    response = admin_client.post(URL, {"email": "segundo@example.com"}, **AUTH)

    assert response.json()["code"] == "email_belongs_to_customer"
    assert clerk.invitations_created == []


@pytest.mark.django_db
def test_invite_existing_admin_is_rejected(admin_client, clerk):
    response = admin_client.post(URL, {"email": "otra@rmshop.test"}, **AUTH)

    assert response.status_code == 409
    assert response.json()["code"] == "already_admin"
    assert clerk.invitations_created == []
    assert AdminAuditLog.objects.count() == 0


@pytest.mark.django_db
def test_invite_with_pending_invitation_is_rejected_and_idempotent(admin_client, clerk):
    first = admin_client.post(URL, {"email": "nuevo@rmshop.test"}, **AUTH)
    second = admin_client.post(URL, {"email": "NUEVO@rmshop.test"}, **AUTH)

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["code"] == "invitation_pending"
    assert len(clerk.invitations_created) == 1
    assert AdminAuditLog.objects.count() == 1


@pytest.mark.django_db
def test_invite_race_on_duplicate_invitation_maps_to_pending(admin_client, clerk, monkeypatch):
    def duplicate(email, redirect_url):
        raise services.clerk_admin.InvitationAlreadyExists()

    monkeypatch.setattr(services.clerk_admin, "create_admin_invitation", duplicate)

    response = admin_client.post(URL, {"email": "nuevo@rmshop.test"}, **AUTH)

    assert response.json()["code"] == "invitation_pending"
    assert AdminAuditLog.objects.count() == 0


@pytest.mark.django_db
def test_invite_clerk_failure_returns_502_without_audit(admin_client, clerk, monkeypatch):
    from apps.users.exceptions import ClerkUnavailable

    def boom(email, redirect_url):
        raise ClerkUnavailable()

    monkeypatch.setattr(services.clerk_admin, "create_admin_invitation", boom)

    response = admin_client.post(URL, {"email": "nuevo@rmshop.test"}, **AUTH)

    assert response.status_code == 502
    assert response.json() == {
        "code": "clerk_unavailable",
        "message": "No pudimos completar la operación, intenta de nuevo.",
        "fields": {},
    }
    assert AdminAuditLog.objects.count() == 0


# --- Listado --------------------------------------------------------------------------


@pytest.mark.django_db
def test_list_returns_only_administrators_and_marks_me(admin_client, clerk):
    response = admin_client.get(URL, **AUTH)

    assert response.status_code == 200
    # Ordenados por nombre.
    assert response.json() == [
        {
            "clerk_user_id": "user_other",
            "email": "otra@rmshop.test",
            "first_name": "Otra",
            "last_name": "Admin",
            "is_me": False,
        },
        {
            "clerk_user_id": "user_me",
            "email": "yo@rmshop.test",
            "first_name": "Yo",
            "last_name": "Admin",
            "is_me": True,
        },
    ]


# --- AC-HU-12-3 -----------------------------------------------------------------------


@pytest.mark.django_db
def test_delete_other_admin_calls_clerk_and_writes_audit(admin_client, clerk):
    response = admin_client.delete(f"{URL}/user_other", **AUTH)

    assert response.status_code == 204
    assert clerk.deleted == ["user_other"]
    assert "user_other" not in clerk.accounts
    log = AdminAuditLog.objects.get()
    assert (log.action, log.actor_email, log.target_email, log.target_clerk_user_id) == (
        "admin_removed",
        "yo@rmshop.test",
        "otra@rmshop.test",
        "user_other",
    )


@pytest.mark.django_db
@pytest.mark.parametrize("target", ["user_customer", "user_inexistente"])
def test_delete_non_admin_returns_404_and_never_deletes(admin_client, clerk, target):
    response = admin_client.delete(f"{URL}/{target}", **AUTH)

    assert response.status_code == 404
    assert response.json()["code"] == "admin_not_found"
    assert clerk.deleted == []
    assert AdminAuditLog.objects.count() == 0


@pytest.mark.django_db
def test_delete_clerk_failure_leaves_no_audit_log(admin_client, clerk):
    clerk.fail_delete = True

    response = admin_client.delete(f"{URL}/user_other", **AUTH)

    assert response.status_code == 502
    assert response.json()["code"] == "clerk_unavailable"
    assert AdminAuditLog.objects.count() == 0
    assert "user_other" in clerk.accounts


# --- AC-HU-12-4 -----------------------------------------------------------------------


@pytest.mark.django_db
def test_delete_self_is_rejected(admin_client, clerk):
    response = admin_client.delete(f"{URL}/user_me", **AUTH)

    assert response.status_code == 409
    assert response.json()["code"] == "cannot_delete_self"
    assert clerk.deleted == []


@pytest.mark.django_db
def test_only_admin_cannot_delete_their_own_account(admin_client, clerk):
    """La "última cuenta" solo se alcanza borrándose a sí mismo: el solicitante es admin."""
    del clerk.accounts["user_other"]

    response = admin_client.delete(f"{URL}/user_me", **AUTH)

    assert response.json()["code"] == "cannot_delete_self"


# --- AC-HU-12-5 -----------------------------------------------------------------------


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("method", "path"),
    [("get", URL), ("post", URL), ("delete", f"{URL}/user_other")],
)
def test_customer_gets_403_and_anonymous_gets_401(api_client, login, clerk, method, path):
    body = {"email": "x@y.com"} if method == "post" else None
    send = getattr(api_client, method)

    assert send(path, body).status_code == 401

    for role in (None, "customer"):
        login(role=role, sub="user_customer", email="cliente@example.com")
        assert send(path, body, **AUTH).status_code == 403
    assert clerk.deleted == []
    assert clerk.invitations_created == []


@pytest.mark.django_db
def test_token_of_a_removed_admin_cannot_remove_others(api_client, login, clerk):
    """El token puede seguir válido ~60 s tras la baja; Clerk manda."""
    login(sub="user_removed", email="baja@rmshop.test")

    response = api_client.delete(f"{URL}/user_other", **AUTH)

    assert response.status_code == 403
    assert clerk.deleted == []


# --- Concurrencia ---------------------------------------------------------------------


@pytest.mark.django_db
def test_removal_acquires_the_advisory_lock(clerk):
    actor = UserFactory(clerk_user_id="user_me", email="yo@rmshop.test")

    with CaptureQueriesContext(connection) as queries:
        services.remove_administrator(actor=actor, target_clerk_user_id="user_other")

    statements = [q["sql"] for q in queries.captured_queries]
    assert any("pg_advisory_xact_lock" in sql for sql in statements)


@pytest.mark.django_db(transaction=True)
def test_crossed_removals_never_leave_zero_administrators(monkeypatch):
    fake = FakeClerk(delete_delay=0.3)
    fake.add("user_a", "a@rmshop.test", role="admin")
    fake.add("user_b", "b@rmshop.test", role="admin")
    fake.install(monkeypatch)
    actor_a = UserFactory(clerk_user_id="user_a", email="a@rmshop.test")
    actor_b = UserFactory(clerk_user_id="user_b", email="b@rmshop.test")

    results = {}
    barrier = threading.Barrier(2)

    def run(name, actor, target):
        try:
            barrier.wait()
            services.remove_administrator(actor=actor, target_clerk_user_id=target)
            results[name] = "ok"
        except Exception as exc:
            results[name] = getattr(exc, "default_code", repr(exc))
        finally:
            connection.close()

    threads = [
        threading.Thread(target=run, args=("a", actor_a, "user_b")),
        threading.Thread(target=run, args=("b", actor_b, "user_a")),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(fake.list_administrator_accounts()) == 1
    assert list(results.values()).count("ok") == 1
    assert AdminAuditLog.objects.filter(action="admin_removed").count() == 1
