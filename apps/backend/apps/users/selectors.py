from . import clerk_admin


def list_administrators(*, current_clerk_user_id: str) -> list[dict]:
    """Administradores según Clerk, por nombre; `is_me` marca la cuenta del solicitante."""
    accounts = clerk_admin.list_administrator_accounts()
    accounts.sort(key=lambda a: (a.first_name.lower(), a.last_name.lower(), a.email))
    return [
        {
            "clerk_user_id": account.clerk_user_id,
            "email": account.email,
            "first_name": account.first_name,
            "last_name": account.last_name,
            "is_me": account.clerk_user_id == current_clerk_user_id,
        }
        for account in accounts
    ]
