import io
import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils.text import slugify
from PIL import Image, ImageOps

from apps.catalog.models import Category, Product, ProductImage, ProductStatus, ProductVariant

MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_IMAGE_DIMENSION = 1600
WEBP_QUALITY = 85
ALLOWED_IMAGE_FORMATS = {"JPEG", "JPG", "PNG", "WEBP"}

CATALOG_RECOMMENDED_LIMIT = 30


def _generate_unique_slug(name: str) -> str:
    base_slug = slugify(name)
    if not base_slug:
        base_slug = "producto"

    slug = base_slug
    counter = 1
    while Product.objects.filter(slug=slug).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1

    return slug


@transaction.atomic
def create_product(
    *,
    name: str,
    description: str,
    price: Decimal | int | str,
    material: str,
    category: Category | int,
    previous_price: Decimal | int | str | None = None,
) -> tuple[Product, str | None]:
    """Crea un producto en estado borrador con validaciones de catálogo de RM Shop.

    Reglas de negocio:
    - Precio en COP positivo y sin centavos.
    - Precio anterior opcional y positivo si se suministra.
    - Slug único generado a partir del nombre.
    - Estado inicial DRAFT.
    - Si el catálogo ya cuenta con >= 30 productos no archivados, se crea el producto
      y se adjunta un mensaje de advertencia.
    """
    errors: dict[str, list[str]] = {}

    try:
        decimal_price = Decimal(str(price))
        if decimal_price <= 0:
            errors.setdefault("price", []).append("El precio debe ser mayor a 0.")
        elif decimal_price % 1 != 0:
            errors.setdefault("price", []).append("El precio en COP no admite centavos.")
    except ValueError, TypeError, ArithmeticError:
        errors.setdefault("price", []).append("El precio debe ser un número válido.")
        decimal_price = Decimal(0)

    decimal_previous_price: Decimal | None = None
    if previous_price is not None and str(previous_price).strip() != "":
        try:
            decimal_previous_price = Decimal(str(previous_price))
            if decimal_previous_price <= 0:
                errors.setdefault("previous_price", []).append(
                    "El precio anterior debe ser mayor a 0."
                )
            elif decimal_previous_price % 1 != 0:
                errors.setdefault("previous_price", []).append(
                    "El precio anterior en COP no admite centavos."
                )
        except ValueError, TypeError, ArithmeticError:
            errors.setdefault("previous_price", []).append(
                "El precio anterior debe ser un número válido."
            )

    category_instance: Category | None
    if not isinstance(category, Category):
        try:
            category_instance = Category.objects.get(pk=category)
        except Category.DoesNotExist, ValueError:
            errors.setdefault("category", []).append("La categoría seleccionada no existe.")
            category_instance = None
    else:
        category_instance = category

    if not name or not str(name).strip():
        errors.setdefault("name", []).append("El nombre es obligatorio.")

    if not description or not str(description).strip():
        errors.setdefault("description", []).append("La descripción es obligatoria.")

    if not material or not str(material).strip():
        errors.setdefault("material", []).append("El material es obligatorio.")

    if errors:
        raise ValidationError(errors)

    active_count = Product.objects.exclude(status=ProductStatus.ARCHIVED).count()
    warning: str | None = None
    if active_count >= CATALOG_RECOMMENDED_LIMIT:
        warning = (
            f"El catálogo ha alcanzado o superado el umbral sugerido de "
            f"{CATALOG_RECOMMENDED_LIMIT} productos ({active_count} prendas activas)."
        )

    slug = _generate_unique_slug(name)

    product = Product.objects.create(
        name=name.strip(),
        slug=slug,
        description=description.strip(),
        price=decimal_price,
        previous_price=decimal_previous_price,
        material=material.strip(),
        category=category_instance,
        status=ProductStatus.DRAFT,
    )

    return product, warning


@transaction.atomic
def update_product(
    *,
    product_id: int,
    name: str | None = None,
    description: str | None = None,
    price: Decimal | int | str | None = None,
    material: str | None = None,
    category: Category | int | None = None,
    previous_price: Decimal | int | str | None = None,
    status: str | None = None,
) -> Product:
    """Actualiza los atributos de un producto existente con validaciones en COP."""
    product = Product.objects.select_for_update().get(pk=product_id)
    errors: dict[str, list[str]] = {}

    if price is not None:
        try:
            decimal_price = Decimal(str(price))
            if decimal_price <= 0:
                errors.setdefault("price", []).append("El precio debe ser mayor a 0.")
            elif decimal_price % 1 != 0:
                errors.setdefault("price", []).append("El precio en COP no admite centavos.")
            else:
                product.price = decimal_price
        except ValueError, TypeError, ArithmeticError:
            errors.setdefault("price", []).append("El precio debe ser un número válido.")

    if previous_price is not None:
        if str(previous_price).strip() == "":
            product.previous_price = None
        else:
            try:
                decimal_prev = Decimal(str(previous_price))
                if decimal_prev <= 0:
                    errors.setdefault("previous_price", []).append(
                        "El precio anterior debe ser mayor a 0."
                    )
                elif decimal_prev % 1 != 0:
                    errors.setdefault("previous_price", []).append(
                        "El precio anterior en COP no admite centavos."
                    )
                else:
                    product.previous_price = decimal_prev
            except ValueError, TypeError, ArithmeticError:
                errors.setdefault("previous_price", []).append(
                    "El precio anterior debe ser un número válido."
                )

    if category is not None:
        if not isinstance(category, Category):
            try:
                product.category = Category.objects.get(pk=category)
            except Category.DoesNotExist, ValueError:
                errors.setdefault("category", []).append("La categoría seleccionada no existe.")
        else:
            product.category = category

    if name is not None:
        stripped_name = str(name).strip()
        if not stripped_name:
            errors.setdefault("name", []).append("El nombre no puede estar vacío.")
        elif stripped_name != product.name:
            product.name = stripped_name
            product.slug = _generate_unique_slug(stripped_name)

    if description is not None:
        stripped_desc = str(description).strip()
        if not stripped_desc:
            errors.setdefault("description", []).append("La descripción no puede estar vacía.")
        else:
            product.description = stripped_desc

    if material is not None:
        stripped_mat = str(material).strip()
        if not stripped_mat:
            errors.setdefault("material", []).append("El material no puede estar vacío.")
        else:
            product.material = stripped_mat

    if status is not None:
        if status not in ProductStatus.values:
            errors.setdefault("status", []).append(
                f"Estado inválido. Opciones válidas: {ProductStatus.values}."
            )
        else:
            product.status = status

    if errors:
        raise ValidationError(errors)

    product.save()
    return product


@transaction.atomic
def delete_product(*, product_id: int) -> Product:
    """Elimina lógicamente un producto archivándolo (AC-HU-34-3)."""
    product = Product.objects.select_for_update().get(pk=product_id)
    product.status = ProductStatus.ARCHIVED
    product.save(update_fields=["status", "updated_at"])
    return product


def process_image(file) -> ContentFile:
    """Valida, redimensiona (máx 1600 px) y optimiza a formato WebP (calidad 85)."""
    size = getattr(file, "size", None)
    if size is None:
        try:
            size = len(file)
        except TypeError:
            pass

    if size is not None and size > MAX_IMAGE_SIZE_BYTES:
        raise ValidationError({"image": ["La imagen no debe superar los 5 MB."]})

    try:
        file.seek(0)
    except AttributeError, io.UnsupportedOperation:
        pass

    try:
        img = Image.open(file)
        img.verify()
        file.seek(0)
        img = Image.open(file)
    except Exception:
        raise ValidationError(
            {"image": ["El archivo debe ser una imagen válida (JPG, PNG o WebP)."]}
        ) from None

    format_name = (img.format or "").upper()
    if format_name not in ALLOWED_IMAGE_FORMATS:
        raise ValidationError(
            {"image": ["Formato no permitido. Solo se aceptan archivos JPG, PNG o WebP."]}
        )

    # Respect EXIF orientation if present
    img = ImageOps.exif_transpose(img)

    # Proportional resize if larger than 1600 px
    w, h = img.size
    if max(w, h) > MAX_IMAGE_DIMENSION:
        if w >= h:
            new_w = MAX_IMAGE_DIMENSION
            new_h = int(round((h * MAX_IMAGE_DIMENSION) / w))
        else:
            new_h = MAX_IMAGE_DIMENSION
            new_w = int(round((w * MAX_IMAGE_DIMENSION) / h))
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # Convert mode for WebP
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        img = img.convert("RGBA")
    else:
        img = img.convert("RGB")

    output = io.BytesIO()
    img.save(output, format="WEBP", quality=WEBP_QUALITY, optimize=True)
    filename = f"{uuid.uuid4().hex}.webp"
    return ContentFile(output.getvalue(), name=filename)


@transaction.atomic
def upload_product_image(
    *,
    product_id: int,
    file,
    alt_text: str = "",
    position: int | None = None,
) -> ProductImage:
    """Carga y optimiza una foto para el producto (límite de 3, AC-HU-35-3)."""
    product = Product.objects.select_for_update().get(pk=product_id)

    # Validar límite de 3 fotografías
    if product.images.count() >= 3:
        raise ValidationError(
            {"image": ["El producto ya tiene el máximo permitido de 3 fotografías."]}
        )

    # Fallback de alt_text si viene vacío (AC-HU-61-2)
    cleaned_alt = (alt_text or "").strip()
    if not cleaned_alt:
        cleaned_alt = product.name

    occupied_positions = set(product.images.values_list("position", flat=True))
    if position is None:
        for slot in range(1, 4):
            if slot not in occupied_positions:
                position = slot
                break
    else:
        if position < 1 or position > 3:
            raise ValidationError({"position": ["La posición debe estar entre 1 y 3."]})
        if position in occupied_positions:
            raise ValidationError(
                {"position": [f"La posición {position} ya está ocupada por otra imagen."]}
            )

    processed_file = process_image(file)

    product_image = ProductImage(
        product=product,
        alt_text=cleaned_alt,
        position=position,
    )
    product_image.image.save(processed_file.name, processed_file, save=True)
    return product_image


@transaction.atomic
def delete_product_image(*, product_id: int, image_id: int) -> None:
    """Elimina una imagen de la BD, purga el archivo del storage y recompacta posiciones."""
    product = Product.objects.select_for_update().get(pk=product_id)
    image = product.images.select_for_update().get(pk=image_id)

    if image.image:
        image.image.delete(save=False)

    image.delete()

    # Recompactar posiciones restantes 1..N
    remaining_images = list(product.images.select_for_update().order_by("position", "id"))
    for idx, img in enumerate(remaining_images, start=1):
        if img.position != idx:
            img.position = idx
            img.save(update_fields=["position"])


@transaction.atomic
def reorder_product_images(*, product_id: int, image_ids: list[int]) -> list[ProductImage]:
    """Reordena atómicamente las posiciones 1..N de las imágenes del producto."""
    product = Product.objects.select_for_update().get(pk=product_id)
    existing_images = {img.id: img for img in product.images.select_for_update()}

    if set(image_ids) != set(existing_images.keys()):
        raise ValidationError(
            {"image_ids": ["La lista de IDs debe coincidir con las imágenes del producto."]}
        )

    # Paso 1: Asignar posiciones temporales para evitar colisión con unique(product, position)
    for idx, img_id in enumerate(image_ids, start=101):
        img = existing_images[img_id]
        img.position = idx
        img.save(update_fields=["position"])

    # Paso 2: Asignar posiciones definitivas 1..N
    reordered_list: list[ProductImage] = []
    for idx, img_id in enumerate(image_ids, start=1):
        img = existing_images[img_id]
        img.position = idx
        img.save(update_fields=["position"])
        reordered_list.append(img)

    return reordered_list


def _normalize_variant_attributes(color: str, size: str) -> tuple[str, str]:
    cleaned_color = (color or "").strip().title()
    cleaned_size = (size or "").strip().upper()
    if not cleaned_color:
        raise ValidationError({"color": ["El color no puede estar vacío."]})
    if not cleaned_size:
        raise ValidationError({"size": ["La talla no puede estar vacía."]})
    return cleaned_color, cleaned_size


@transaction.atomic
def create_product_variant(
    *,
    product_id: int,
    color: str,
    size: str,
    stock_quantity: int = 0,
) -> ProductVariant:
    """Crea una variante de producto validando unicidad (AC-HU-36-1, AC-HU-36-2)."""
    product = Product.objects.select_for_update().get(pk=product_id)
    norm_color, norm_size = _normalize_variant_attributes(color, size)

    if stock_quantity < 0:
        raise ValidationError({"stock_quantity": ["El stock no puede ser negativo."]})

    if product.variants.filter(color__iexact=norm_color, size__iexact=norm_size).exists():
        raise ValidationError(
            {
                "non_field_errors": [
                    f"Ya existe una variante con el color '{norm_color}' y "
                    f"la talla '{norm_size}' para este producto."
                ]
            }
        )

    return ProductVariant.objects.create(
        product=product,
        color=norm_color,
        size=norm_size,
        stock_quantity=stock_quantity,
    )


@transaction.atomic
def bulk_create_variants(
    *,
    product_id: int,
    colors: list[str],
    sizes: list[str],
) -> list[ProductVariant]:
    """Genera combinaciones colores x tallas omitiendo las ya existentes sin error."""
    product = Product.objects.select_for_update().get(pk=product_id)
    if not colors:
        raise ValidationError({"colors": ["Debes especificar al menos un color."]})
    if not sizes:
        raise ValidationError({"sizes": ["Debes especificar al menos una talla."]})

    normalized_colors = []
    for c in colors:
        cleaned = (c or "").strip().title()
        if cleaned and cleaned not in normalized_colors:
            normalized_colors.append(cleaned)

    normalized_sizes = []
    for s in sizes:
        cleaned = (s or "").strip().upper()
        if cleaned and cleaned not in normalized_sizes:
            normalized_sizes.append(cleaned)

    existing_pairs = set(product.variants.values_list("color", "size"))

    to_create: list[ProductVariant] = []
    for c in normalized_colors:
        for s in normalized_sizes:
            if (c, s) not in existing_pairs:
                to_create.append(
                    ProductVariant(
                        product=product,
                        color=c,
                        size=s,
                        stock_quantity=0,
                    )
                )

    if to_create:
        ProductVariant.objects.bulk_create(to_create)

    return list(product.variants.order_by("size", "color"))


@transaction.atomic
def delete_product_variant(*, product_id: int, variant_id: int) -> None:
    """Elimina una variante de producto solo si su stock es 0 (AC-HU-36-3)."""
    product = Product.objects.select_for_update().get(pk=product_id)
    variant = product.variants.select_for_update().get(pk=variant_id)

    if variant.stock_quantity > 0:
        raise ValidationError(
            {
                "stock_quantity": [
                    f"No se puede eliminar una variante que posee stock "
                    f"({variant.stock_quantity} unidades) o reservas activas."
                ]
            }
        )

    variant.delete()
