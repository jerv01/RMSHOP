from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import Category, Product, ProductStatus
from apps.catalog.services import (
    bulk_create_variants,
    create_product,
    update_product,
    upload_product_image,
)
from apps.inventory.services import adjust_variant_stock

SEED_IMAGES_DIR = Path(__file__).resolve().parents[2] / "seed_images"

PRODUCTS = [
    {
        "name": "Camiseta Texturizada Blanca",
        "color": "Blanco",
        "image": "camiseta-texturizada-blanca.jpeg",
    },
    {
        "name": "Camiseta Texturizada Negra",
        "color": "Negro",
        "image": "camiseta-texturizada-negra.jpeg",
    },
]
SIZES = ["M", "L"]
PRICE = 89900
INITIAL_STOCK = 5


class Command(BaseCommand):
    help = "Crea productos de ejemplo publicados, con imagen, tallas M/L y stock 5 por variante."

    def handle(self, *args, **options):
        category = Category.objects.get(slug="camisetas-tops")
        for data in PRODUCTS:
            if Product.objects.filter(name=data["name"]).exists():
                self.stdout.write(f"Ya existe, se omite: {data['name']}")
                continue
            with transaction.atomic():
                product, _ = create_product(
                    name=data["name"],
                    description=f"{data['name']} en tejido texturizado, corte regular.",
                    price=PRICE,
                    material="Algodón",
                    category=category,
                )
                with open(SEED_IMAGES_DIR / data["image"], "rb") as fh:
                    upload_product_image(
                        product_id=product.id,
                        file=File(fh, name=data["image"]),
                        alt_text=data["name"],
                    )
                variants = bulk_create_variants(
                    product_id=product.id, colors=[data["color"]], sizes=SIZES
                )
                for variant in variants:
                    adjust_variant_stock(
                        variant_id=variant.id, delta=INITIAL_STOCK, reason="Stock inicial (seed)"
                    )
                update_product(product_id=product.id, status=ProductStatus.PUBLISHED)
            self.stdout.write(self.style.SUCCESS(f"Creado: {data['name']}"))
