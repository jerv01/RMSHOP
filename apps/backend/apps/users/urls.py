from django.urls import path

from .views import (
    AdministratorDetailView,
    AdministratorListCreateView,
    ClerkWebhookView,
    MeView,
)

urlpatterns = [
    path("me", MeView.as_view(), name="me"),
    path("admin/administrators", AdministratorListCreateView.as_view(), name="administrators"),
    path(
        "admin/administrators/<str:clerk_user_id>",
        AdministratorDetailView.as_view(),
        name="administrator-detail",
    ),
    path("webhooks/clerk", ClerkWebhookView.as_view(), name="clerk-webhook"),
]
