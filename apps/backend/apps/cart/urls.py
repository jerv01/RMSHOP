from django.urls import path

from apps.cart.views import (
    CartItemAddView,
    CartItemDetailView,
    CartItemReReserveView,
    CartView,
)

urlpatterns = [
    path("cart", CartView.as_view(), name="cart-detail"),
    path("cart/", CartView.as_view()),
    path("cart/items", CartItemAddView.as_view(), name="cart-item-add"),
    path("cart/items/", CartItemAddView.as_view()),
    path("cart/items/<int:item_id>", CartItemDetailView.as_view(), name="cart-item-detail"),
    path("cart/items/<int:item_id>/", CartItemDetailView.as_view()),
    path(
        "cart/items/<int:item_id>/re-reserve",
        CartItemReReserveView.as_view(),
        name="cart-item-re-reserve",
    ),
    path(
        "cart/items/<int:item_id>/re-reserve/",
        CartItemReReserveView.as_view(),
    ),
]
