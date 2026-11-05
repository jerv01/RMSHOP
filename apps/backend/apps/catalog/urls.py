from django.urls import path

from apps.catalog.views import (
    AdminProductCreateView,
    AdminProductDetailView,
    AdminProductImageDetailView,
    AdminProductImageListCreateView,
    AdminProductImageReorderView,
    AdminProductVariantBulkCreateView,
    AdminProductVariantDetailView,
    AdminProductVariantListCreateView,
    PublicCategoryListView,
    PublicProductDetailView,
    PublicProductListView,
)

urlpatterns = [
    path("categories", PublicCategoryListView.as_view(), name="public-category-list"),
    path("categories/", PublicCategoryListView.as_view()),
    path("products", PublicProductListView.as_view(), name="public-product-list"),
    path("products/", PublicProductListView.as_view()),
    path("products/<slug:slug>", PublicProductDetailView.as_view(), name="public-product-detail"),
    path("products/<slug:slug>/", PublicProductDetailView.as_view()),
    path("admin/products", AdminProductCreateView.as_view(), name="admin-product-create"),
    path(
        "admin/products/<int:pk>",
        AdminProductDetailView.as_view(),
        name="admin-product-detail",
    ),
    path(
        "admin/products/<int:product_id>/images",
        AdminProductImageListCreateView.as_view(),
        name="admin-product-images-list-create",
    ),
    path(
        "admin/products/<int:product_id>/images/",
        AdminProductImageListCreateView.as_view(),
    ),
    path(
        "admin/products/<int:product_id>/images/<int:image_id>",
        AdminProductImageDetailView.as_view(),
        name="admin-product-image-detail",
    ),
    path(
        "admin/products/<int:product_id>/images/<int:image_id>/",
        AdminProductImageDetailView.as_view(),
    ),
    path(
        "admin/products/<int:product_id>/images/reorder",
        AdminProductImageReorderView.as_view(),
        name="admin-product-images-reorder",
    ),
    path(
        "admin/products/<int:product_id>/images/reorder/",
        AdminProductImageReorderView.as_view(),
    ),
    path(
        "admin/products/<int:product_id>/variants",
        AdminProductVariantListCreateView.as_view(),
        name="admin-product-variants-list-create",
    ),
    path(
        "admin/products/<int:product_id>/variants/",
        AdminProductVariantListCreateView.as_view(),
    ),
    path(
        "admin/products/<int:product_id>/variants/bulk",
        AdminProductVariantBulkCreateView.as_view(),
        name="admin-product-variants-bulk-create",
    ),
    path(
        "admin/products/<int:product_id>/variants/bulk/",
        AdminProductVariantBulkCreateView.as_view(),
    ),
    path(
        "admin/products/<int:product_id>/variants/<int:variant_id>",
        AdminProductVariantDetailView.as_view(),
        name="admin-product-variant-detail",
    ),
    path(
        "admin/products/<int:product_id>/variants/<int:variant_id>/",
        AdminProductVariantDetailView.as_view(),
    ),
]
