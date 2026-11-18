from django.urls import path

from apps.orders.views import CheckoutView, OrderDetailView, OrderListView

urlpatterns = [
    path("checkout", CheckoutView.as_view(), name="checkout"),
    path("checkout/", CheckoutView.as_view()),
    path("orders", OrderListView.as_view(), name="order-list"),
    path("orders/", OrderListView.as_view()),
    path("orders/<str:order_number>", OrderDetailView.as_view(), name="order-detail"),
    path("orders/<str:order_number>/", OrderDetailView.as_view()),
]
