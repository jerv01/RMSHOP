from django.urls import path

from apps.payments.views import (
    MercadoPagoWebhookView,
    OrderPaymentSyncView,
    OrderPaymentView,
    PseBankListView,
)

urlpatterns = [
    path(
        "orders/<str:order_number>/payments",
        OrderPaymentView.as_view(),
        name="order-payment",
    ),
    path("orders/<str:order_number>/payments/", OrderPaymentView.as_view()),
    path(
        "orders/<str:order_number>/payments/sync",
        OrderPaymentSyncView.as_view(),
        name="order-payment-sync",
    ),
    path("orders/<str:order_number>/payments/sync/", OrderPaymentSyncView.as_view()),
    path("payments/pse-banks", PseBankListView.as_view(), name="pse-banks"),
    path("payments/pse-banks/", PseBankListView.as_view()),
    path(
        "webhooks/payments/mercadopago",
        MercadoPagoWebhookView.as_view(),
        name="mercadopago-webhook",
    ),
    path("webhooks/payments/mercadopago/", MercadoPagoWebhookView.as_view()),
]
