import pytest
from django.core.management import call_command

from apps.catalog.models import Product, ProductStatus, ProductVariant


@pytest.mark.django_db
def test_seed_products_creates_published_tshirts_once(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path

    call_command("seed_products")
    call_command("seed_products")  # idempotente: no duplica

    products = Product.objects.filter(name__startswith="Camiseta Texturizada")
    assert products.count() == 2
    assert all(p.status == ProductStatus.PUBLISHED for p in products)
    assert all(p.images.count() == 1 for p in products)

    variants = ProductVariant.objects.filter(product__in=products)
    assert sorted((v.color, v.size) for v in variants) == [
        ("Blanco", "L"),
        ("Blanco", "M"),
        ("Negro", "L"),
        ("Negro", "M"),
    ]
    assert all(v.stock_quantity == 5 for v in variants)
