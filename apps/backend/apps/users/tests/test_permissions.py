import pytest
from django.test import RequestFactory

from apps.users.clerk import ClerkClaims
from apps.users.models import User
from apps.users.permissions import IsCustomer, IsRMAdmin


def make_request(*, authenticated=True, role=None):
    request = RequestFactory().get("/")
    request.user = User(clerk_user_id="user_1") if authenticated else None
    request.auth = ClerkClaims(sub="user_1", role=role) if authenticated else None
    return request


@pytest.mark.parametrize(
    ("authenticated", "role", "allowed"),
    [(True, "admin", True), (True, None, False), (True, "customer", False), (False, None, False)],
    ids=["admin", "sin-rol", "rol-cliente", "sin-sesion"],
)
def test_is_rm_admin(authenticated, role, allowed):
    request = make_request(authenticated=authenticated, role=role)

    assert IsRMAdmin().has_permission(request, view=None) is allowed


@pytest.mark.parametrize(("authenticated", "allowed"), [(True, True), (False, False)])
def test_is_customer(authenticated, allowed):
    request = make_request(authenticated=authenticated)

    assert IsCustomer().has_permission(request, view=None) is allowed
