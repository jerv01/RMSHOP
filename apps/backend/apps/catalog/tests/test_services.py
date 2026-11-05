import io
from decimal import Decimal

import pytest
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.catalog.models import Category, Product, ProductStatus
from apps.catalog.services import (
    bulk_create_variants,
    create_product,
    create_product_variant,
    delete_product,
    delete_product_image,
    delete_product_variant,
    reorder_product_images,
    update_product,
    upload_product_image,
)


def _create_test_image(name: str = "test.jpg", format: str = "JPEG"):
    buf = io.BytesIO()
    img = Image.new("RGB", (400, 300), color="red")
    img.save(buf, format=format)
    buf.seek(0)
    return SimpleUploadedFile(name, buf.getvalue(), content_type=f"image/{format.lower()}")


@pytest.mark.django_db
def test_create_product_success():
    category = Category.objects.get(slug="camisetas-tops")
    product, warning = create_product(
        name="Camiseta RM Minimalista",
        description="Camiseta oversize de algodón peinado.",
        price=Decimal("65000"),
        previous_price=Decimal("80000"),
        material="100% Algodón Peinado",
        category=category,
    )

    assert product.id is not None
    assert product.name == "Camiseta RM Minimalista"
    assert product.slug == "camiseta-rm-minimalista"
    assert product.price == Decimal("65000")
    assert product.previous_price == Decimal("80000")
    assert product.status == ProductStatus.DRAFT
    assert product.category == category
    assert warning is None


@pytest.mark.django_db
def test_create_product_rejects_negative_or_zero_price():
    category = Category.objects.get(slug="camisetas-tops")

    with pytest.raises(ValidationError) as exc:
        create_product(
            name="Camiseta Gratis",
            description="Descripción",
            price=Decimal("0"),
            material="Algodón",
            category=category,
        )
    assert "price" in exc.value.message_dict

    with pytest.raises(ValidationError) as exc:
        create_product(
            name="Camiseta Negativa",
            description="Descripción",
            price=Decimal("-10000"),
            material="Algodón",
            category=category,
        )
    assert "price" in exc.value.message_dict


@pytest.mark.django_db
def test_create_product_rejects_invalid_previous_price():
    category = Category.objects.get(slug="camisetas-tops")

    with pytest.raises(ValidationError) as exc:
        create_product(
            name="Camiseta",
            description="Descripción",
            price=Decimal("50000"),
            previous_price=Decimal("-5000"),
            material="Algodón",
            category=category,
        )
    assert "previous_price" in exc.value.message_dict


@pytest.mark.django_db
def test_create_product_generates_unique_slug_on_collision():
    category = Category.objects.get(slug="buzos-sacos")
    p1, _ = create_product(
        name="Buzo RM Hoodie",
        description="Buzo con capota",
        price=Decimal("110000"),
        material="Frisa de algodón",
        category=category,
    )
    p2, _ = create_product(
        name="Buzo RM Hoodie",
        description="Otro buzo igual nombre",
        price=Decimal("115000"),
        material="Frisa de algodón",
        category=category,
    )

    assert p1.slug == "buzo-rm-hoodie"
    assert p2.slug == "buzo-rm-hoodie-1"


@pytest.mark.django_db
def test_create_product_warns_when_catalog_reaches_or_exceeds_30_products():
    category = Category.objects.get(slug="camisetas-tops")

    Product.objects.bulk_create(
        [
            Product(
                name=f"Prenda {i}",
                slug=f"prenda-{i}",
                description="Descripción",
                price=Decimal("50000"),
                material="Algodón",
                category=category,
                status=ProductStatus.DRAFT,
            )
            for i in range(30)
        ]
    )

    product, warning = create_product(
        name="Prenda 31",
        description="Descripción prenda 31",
        price=Decimal("70000"),
        material="Lino",
        category=category,
    )

    assert product.id is not None
    assert warning is not None
    assert "30 productos" in warning


@pytest.mark.django_db
def test_update_product_price_and_fields():
    category = Category.objects.get(slug="camisetas-tops")
    new_category = Category.objects.get(slug="buzos-sacos")
    product, _ = create_product(
        name="Camiseta Regular",
        description="Descripción inicial",
        price=Decimal("50000"),
        material="Algodón",
        category=category,
    )

    updated = update_product(
        product_id=product.id,
        price=Decimal("60000"),
        previous_price=Decimal("50000"),
        description="Descripción editada",
        category=new_category,
        status=ProductStatus.PUBLISHED,
    )

    assert updated.price == Decimal("60000")
    assert updated.previous_price == Decimal("50000")
    assert updated.description == "Descripción editada"
    assert updated.category == new_category
    assert updated.status == ProductStatus.PUBLISHED
    assert updated.name == "Camiseta Regular"
    assert updated.slug == "camiseta-regular"


@pytest.mark.django_db
def test_update_product_renames_and_updates_slug():
    category = Category.objects.get(slug="camisetas-tops")
    product, _ = create_product(
        name="Nombre Original",
        description="Desc",
        price=Decimal("40000"),
        material="Lino",
        category=category,
    )

    updated = update_product(product_id=product.id, name="Nombre Renovado")
    assert updated.name == "Nombre Renovado"
    assert updated.slug == "nombre-renovado"


@pytest.mark.django_db
def test_update_product_rejects_negative_or_zero_price():
    category = Category.objects.get(slug="camisetas-tops")
    product, _ = create_product(
        name="Camiseta Válida",
        description="Desc",
        price=Decimal("50000"),
        material="Algodón",
        category=category,
    )

    with pytest.raises(ValidationError) as exc:
        update_product(product_id=product.id, price=Decimal("-100"))
    assert "price" in exc.value.message_dict


@pytest.mark.django_db
def test_update_product_non_existent_raises():
    with pytest.raises(ObjectDoesNotExist):
        update_product(product_id=999999, price=Decimal("10000"))


@pytest.mark.django_db
def test_delete_product_archives_without_removing_from_db():
    category = Category.objects.get(slug="camisetas-tops")
    product, _ = create_product(
        name="Prenda a Eliminar",
        description="Desc",
        price=Decimal("50000"),
        material="Algodón",
        category=category,
    )

    deleted = delete_product(product_id=product.id)

    assert deleted.status == ProductStatus.ARCHIVED
    # La fila persiste en la BD para no romper carritos ni pedidos existentes
    db_product = Product.objects.get(id=product.id)
    assert db_product.status == ProductStatus.ARCHIVED


@pytest.mark.django_db
def test_delete_product_non_existent_raises():
    with pytest.raises(ObjectDoesNotExist):
        delete_product(product_id=999999)


@pytest.mark.django_db
def test_upload_product_image_happy_path():
    category = Category.objects.get(slug="camisetas-tops")
    product, _ = create_product(
        name="Camiseta Seda",
        description="Desc",
        price=Decimal("120000"),
        material="Seda",
        category=category,
    )
    img_file = _create_test_image("foto.png", format="PNG")
    img = upload_product_image(
        product_id=product.id,
        file=img_file,
        alt_text="Camiseta de seda vista frontal",
    )
    assert img.id is not None
    assert img.position == 1
    assert img.alt_text == "Camiseta de seda vista frontal"
    assert img.image.name.endswith(".webp")
    assert img.image.storage.exists(img.image.name)
    # Cleanup file
    img.image.delete(save=False)


@pytest.mark.django_db
def test_upload_product_image_fallback_alt_text():
    category = Category.objects.get(slug="camisetas-tops")
    product, _ = create_product(
        name="Pantalón Casual",
        description="Desc",
        price=Decimal("90000"),
        material="Lino",
        category=category,
    )
    img = upload_product_image(
        product_id=product.id,
        file=_create_test_image("p.jpg"),
        alt_text="",
    )
    assert img.alt_text == product.name
    img.image.delete(save=False)


@pytest.mark.django_db
def test_upload_product_image_limit_3_exceeded():
    category = Category.objects.get(slug="camisetas-tops")
    product, _ = create_product(
        name="Top Corto",
        description="Desc",
        price=Decimal("45000"),
        material="Algodón",
        category=category,
    )
    created_imgs = []
    for i in range(3):
        img = upload_product_image(
            product_id=product.id,
            file=_create_test_image(f"f{i}.jpg"),
        )
        created_imgs.append(img)

    with pytest.raises(ValidationError) as exc:
        upload_product_image(
            product_id=product.id,
            file=_create_test_image("f4.jpg"),
        )
    assert "image" in exc.value.message_dict

    for img in created_imgs:
        img.image.delete(save=False)


@pytest.mark.django_db
def test_delete_product_image_recompacts_positions():
    category = Category.objects.get(slug="camisetas-tops")
    product, _ = create_product(
        name="Falda Larga",
        description="Desc",
        price=Decimal("80000"),
        material="Algodón",
        category=category,
    )
    img1 = upload_product_image(product_id=product.id, file=_create_test_image("f1.jpg"))
    img2 = upload_product_image(product_id=product.id, file=_create_test_image("f2.jpg"))
    img3 = upload_product_image(product_id=product.id, file=_create_test_image("f3.jpg"))

    storage = img2.image.storage
    img2_name = img2.image.name

    delete_product_image(product_id=product.id, image_id=img2.id)

    # El archivo físico fue eliminado
    assert not storage.exists(img2_name)

    remaining = list(product.images.order_by("position"))
    assert len(remaining) == 2
    assert remaining[0].id == img1.id and remaining[0].position == 1
    assert remaining[1].id == img3.id and remaining[1].position == 2

    for img in remaining:
        img.image.delete(save=False)


@pytest.mark.django_db
def test_reorder_product_images():
    category = Category.objects.get(slug="camisetas-tops")
    product, _ = create_product(
        name="Buzo Urbano",
        description="Desc",
        price=Decimal("95000"),
        material="Algodón",
        category=category,
    )
    img1 = upload_product_image(product_id=product.id, file=_create_test_image("f1.jpg"))
    img2 = upload_product_image(product_id=product.id, file=_create_test_image("f2.jpg"))

    reordered = reorder_product_images(product_id=product.id, image_ids=[img2.id, img1.id])
    assert reordered[0].id == img2.id and reordered[0].position == 1
    assert reordered[1].id == img1.id and reordered[1].position == 2

    # Intentar reordenar con IDs que no corresponden al producto falla
    with pytest.raises(ValidationError):
        reorder_product_images(product_id=product.id, image_ids=[img1.id, 999999])

    for img in reordered:
        img.image.delete(save=False)


@pytest.mark.django_db
def test_create_product_variant_happy_path():
    category = Category.objects.get(slug="camisetas-tops")
    product, _ = create_product(
        name="Camiseta Polo",
        description="Polo piqué",
        price=Decimal("85000"),
        material="Algodón",
        category=category,
    )
    variant = create_product_variant(
        product_id=product.id,
        color="negro",
        size="m",
        stock_quantity=3,
    )
    assert variant.id is not None
    assert variant.color == "Negro"
    assert variant.size == "M"
    assert variant.stock_quantity == 3
    assert variant.product == product


@pytest.mark.django_db
def test_create_product_variant_rejects_duplicate():
    category = Category.objects.get(slug="camisetas-tops")
    product, _ = create_product(
        name="Chaqueta RM",
        description="Chaqueta ligera",
        price=Decimal("180000"),
        material="Dril",
        category=category,
    )
    create_product_variant(
        product_id=product.id,
        color="Azul",
        size="L",
    )
    # Intento de duplicado con distinta capitalización
    with pytest.raises(ValidationError) as exc:
        create_product_variant(
            product_id=product.id,
            color="azul",
            size="l",
        )
    assert "non_field_errors" in exc.value.message_dict


@pytest.mark.django_db
def test_create_product_variant_rejects_negative_stock():
    category = Category.objects.get(slug="camisetas-tops")
    product, _ = create_product(
        name="Top Deportivo",
        description="Top elástico",
        price=Decimal("40000"),
        material="Spandex",
        category=category,
    )
    with pytest.raises(ValidationError) as exc:
        create_product_variant(
            product_id=product.id,
            color="Rojo",
            size="S",
            stock_quantity=-5,
        )
    assert "stock_quantity" in exc.value.message_dict


@pytest.mark.django_db
def test_bulk_create_variants():
    category = Category.objects.get(slug="camisetas-tops")
    product, _ = create_product(
        name="Buzo Básico",
        description="Buzo cerrado",
        price=Decimal("95000"),
        material="Algodón",
        category=category,
    )
    # Crear una previa
    create_product_variant(product_id=product.id, color="Negro", size="S")

    # Bulk con 2 colores y 2 tallas (total 4 combinaciones, 3 nuevas)
    variants = bulk_create_variants(
        product_id=product.id,
        colors=["Negro", "Blanco"],
        sizes=["S", "M"],
    )
    assert len(variants) == 4
    assert product.variants.count() == 4


@pytest.mark.django_db
def test_delete_product_variant_when_zero_stock():
    category = Category.objects.get(slug="camisetas-tops")
    product, _ = create_product(
        name="Short RM",
        description="Short playero",
        price=Decimal("50000"),
        material="Lino",
        category=category,
    )
    variant = create_product_variant(
        product_id=product.id,
        color="Beige",
        size="32",
        stock_quantity=0,
    )
    delete_product_variant(product_id=product.id, variant_id=variant.id)
    assert not product.variants.filter(id=variant.id).exists()


@pytest.mark.django_db
def test_delete_product_variant_blocks_when_has_stock():
    category = Category.objects.get(slug="camisetas-tops")
    product, _ = create_product(
        name="Vestido Noche",
        description="Elegante",
        price=Decimal("220000"),
        material="Seda",
        category=category,
    )
    variant = create_product_variant(
        product_id=product.id,
        color="Vino",
        size="M",
        stock_quantity=4,
    )
    with pytest.raises(ValidationError) as exc:
        delete_product_variant(product_id=product.id, variant_id=variant.id)
    assert "stock_quantity" in exc.value.message_dict
    assert product.variants.filter(id=variant.id).exists()
