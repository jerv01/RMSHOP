"""Clerk en memoria para las pruebas de HU-12: reemplaza al adaptador `clerk_admin`."""

import threading
import time

from apps.users import clerk_admin
from apps.users.clerk_admin import ClerkAccount
from apps.users.exceptions import ClerkUnavailable


class FakeClerk:
    def __init__(self, *, delete_delay: float = 0.0):
        self.accounts: dict[str, ClerkAccount] = {}
        self.pending_invitations: set[str] = set()
        self.invitations_created: list[dict] = []
        self.deleted: list[str] = []
        self.fail_delete = False
        self.delete_delay = delete_delay
        self._lock = threading.Lock()

    def add(self, clerk_user_id, email, *, role=None, first_name="Ana", last_name="Pérez"):
        self.accounts[clerk_user_id] = ClerkAccount(
            clerk_user_id=clerk_user_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role,
            emails=(email,),
        )

    # Interfaz del adaptador -------------------------------------------------------------
    def find_accounts_by_email(self, email):
        return [a for a in list(self.accounts.values()) if email in a.emails]

    def list_administrator_accounts(self):
        return [a for a in list(self.accounts.values()) if a.is_admin]

    def has_pending_invitation(self, email):
        return email in self.pending_invitations

    def create_admin_invitation(self, email, redirect_url):
        self.invitations_created.append(
            {"email": email, "redirect_url": redirect_url, "public_metadata": {"role": "admin"}}
        )
        self.pending_invitations.add(email)

    def delete_user(self, clerk_user_id):
        if self.fail_delete:
            raise ClerkUnavailable()
        time.sleep(self.delete_delay)  # Ensancha la ventana de la condición de carrera.
        with self._lock:
            self.accounts.pop(clerk_user_id, None)
            self.deleted.append(clerk_user_id)

    def install(self, monkeypatch):
        for name in (
            "find_accounts_by_email",
            "list_administrator_accounts",
            "has_pending_invitation",
            "create_admin_invitation",
            "delete_user",
        ):
            monkeypatch.setattr(clerk_admin, name, getattr(self, name))
