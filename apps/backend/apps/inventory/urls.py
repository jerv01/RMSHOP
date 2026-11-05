from django.urls import path

from apps.inventory.views import (
    AdminVariantStockAdjustmentView,
    AdminVariantStockMovementsListView,
)

urlpatterns = [
    # Ajuste de stock por variante
    path(
        "admin/variants/<int:variant_id>/stock",
        AdminVariantStockAdjustmentView.as_view(),
        name="admin-variant-stock-adjust",
    ),
    path(
        "admin/variants/<int:variant_id>/stock/",
        AdminVariantStockAdjustmentView.as_view(),
    ),
    path(
        "admin/products/<int:product_id>/variants/<int:variant_id>/stock",
        AdminVariantStockAdjustmentView.as_view(),
        name="admin-product-variant-stock-adjust",
    ),
    path(
        "admin/products/<int:product_id>/variants/<int:variant_id>/stock/",
        AdminVariantStockAdjustmentView.as_view(),
    ),
    # Historial de movimientos de stock por variante
    path(
        "admin/variants/<int:variant_id>/stock-movements",
        AdminVariantStockMovementsListView.as_view(),
        name="admin-variant-stock-movements-list",
    ),
    path(
        "admin/variants/<int:variant_id>/stock-movements/",
        AdminVariantStockMovementsListView.as_view(),
    ),
    path(
        "admin/products/<int:product_id>/variants/<int:variant_id>/stock-movements",
        AdminVariantStockMovementsListView.as_view(),
        name="admin-product-variant-stock-movements-list",
    ),
    path(
        "admin/products/<int:product_id>/variants/<int:variant_id>/stock-movements/",
        AdminVariantStockMovementsListView.as_view(),
    ),
]
