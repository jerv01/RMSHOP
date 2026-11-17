from django.urls import path

from apps.cart.views import CartItemAddView, CartView

urlpatterns = [
    path("cart", CartView.as_view(), name="cart-detail"),
    path("cart/", CartView.as_view()),
    path("cart/items", CartItemAddView.as_view(), name="cart-item-add"),
    path("cart/items/", CartItemAddView.as_view()),
]
