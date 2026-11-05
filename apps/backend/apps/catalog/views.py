from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import Category, Product, ProductStatus
from apps.catalog.serializers import (
    CategorySerializer,
    ProductCreateSerializer,
    ProductDetailSerializer,
    ProductImageReorderSerializer,
    ProductImageSerializer,
    ProductImageUploadSerializer,
    ProductUpdateSerializer,
    ProductVariantBulkCreateSerializer,
    ProductVariantCreateSerializer,
    ProductVariantSerializer,
    PublicProductSerializer,
)
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
from apps.users.permissions import IsRMAdmin


class AdminProductCreateView(APIView):
    """Lista todos los productos o crea un nuevo producto en estado borrador.

    Acceso exclusivo para administradores (HU-33, HU-34).
    """

    permission_classes = [IsRMAdmin]

    @extend_schema(
        summary="Listar todos los productos para administración",
        description=(
            "Retorna todos los productos del catálogo (borradores, publicados y archivados)."
        ),
        responses={200: ProductDetailSerializer(many=True)},
    )
    def get(self, request):
        products = Product.objects.select_related("category").order_by("-created_at", "-id")
        return Response(ProductDetailSerializer(products, many=True).data)

    @extend_schema(
        summary="Crear producto en catálogo",
        description=(
            "Permite al administrador crear una prenda con nombre, descripción, "
            "precio COP, material y categoría inicial. El producto se crea en modo "
            "borrador (`draft`). Si el catálogo alcanza o supera los 30 productos, "
            "se retorna una advertencia en el campo `warning`."
        ),
        request=ProductCreateSerializer,
        responses={
            201: ProductDetailSerializer,
        },
    )
    def post(self, request):
        serializer = ProductCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        product, warning = create_product(
            name=validated_data["name"],
            description=validated_data["description"],
            price=validated_data["price"],
            material=validated_data["material"],
            category=validated_data["category"],
            previous_price=validated_data.get("previous_price"),
        )

        response_data = ProductDetailSerializer(product).data
        if warning:
            response_data["warning"] = warning

        return Response(response_data, status=status.HTTP_201_CREATED)


class AdminProductDetailView(APIView):
    """Consulta, edita o elimina lógicamente un producto del catálogo.

    Acceso exclusivo para administradores (HU-34).
    """

    permission_classes = [IsRMAdmin]

    @extend_schema(
        summary="Obtener detalle de producto para administración",
        description="Retorna el detalle completo de una prenda por su ID.",
        responses={200: ProductDetailSerializer},
    )
    def get(self, request, pk: int):
        product = get_object_or_404(Product, pk=pk)
        return Response(ProductDetailSerializer(product).data)

    @extend_schema(
        summary="Actualizar producto en catálogo",
        description=(
            "Permite editar atributos de una prenda (nombre, descripción, precios COP, "
            "material, categoría y estado). Si cambia el nombre, se actualiza el slug."
        ),
        request=ProductUpdateSerializer,
        responses={200: ProductDetailSerializer},
    )
    def patch(self, request, pk: int):
        get_object_or_404(Product, pk=pk)
        serializer = ProductUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        product = update_product(product_id=pk, **serializer.validated_data)
        return Response(ProductDetailSerializer(product).data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Actualización completa de producto",
        description="Reemplaza o actualiza atributos del producto en el catálogo.",
        request=ProductUpdateSerializer,
        responses={200: ProductDetailSerializer},
    )
    def put(self, request, pk: int):
        return self.patch(request, pk)

    @extend_schema(
        summary="Eliminar producto del catálogo (borrado lógico)",
        description=(
            "Archiva lógicamente el producto (`status='archived'`) para no mostrarlo "
            "en el catálogo y preservar la consistencia con pedidos o carritos existentes."
        ),
        responses={204: None},
    )
    def delete(self, request, pk: int):
        get_object_or_404(Product, pk=pk)
        delete_product(product_id=pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminProductImageListCreateView(APIView):
    """Lista o sube fotografías para una prenda del catálogo (1 a 3 fotos)."""

    permission_classes = [IsRMAdmin]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @extend_schema(
        summary="Listar imágenes del producto",
        description="Retorna las fotos de la prenda ordenadas por posición (1 a 3).",
        responses={200: ProductImageSerializer(many=True)},
    )
    def get(self, request, product_id: int):
        product = get_object_or_404(Product, pk=product_id)
        images = product.images.order_by("position", "id")
        return Response(ProductImageSerializer(images, many=True).data)

    @extend_schema(
        summary="Subir fotografía de producto",
        description=(
            "Permite al administrador subir una foto (JPG, PNG o WebP de hasta 5 MB). "
            "El archivo se convierte automáticamente a WebP a máx 1600 px y calidad 85. "
            "Máximo 3 imágenes por prenda (AC-HU-35-3)."
        ),
        request=ProductImageUploadSerializer,
        responses={201: ProductImageSerializer},
    )
    def post(self, request, product_id: int):
        product = get_object_or_404(Product, pk=product_id)
        serializer = ProductImageUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        image = upload_product_image(
            product_id=product.id,
            file=data["image"],
            alt_text=data.get("alt_text", ""),
            position=data.get("position"),
        )
        return Response(
            ProductImageSerializer(image).data,
            status=status.HTTP_201_CREATED,
        )


class AdminProductImageDetailView(APIView):
    """Elimina una fotografía del producto."""

    permission_classes = [IsRMAdmin]

    @extend_schema(
        summary="Eliminar fotografía de producto",
        description=(
            "Elimina la foto de la base de datos, purga el archivo del almacenamiento "
            "y recompacta automáticamente las posiciones restantes (1..N)."
        ),
        responses={204: None},
    )
    def delete(self, request, product_id: int, image_id: int):
        get_object_or_404(Product, pk=product_id)
        delete_product_image(product_id=product_id, image_id=image_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminProductImageReorderView(APIView):
    """Reordena las posiciones (1..3) de las fotografías del producto."""

    permission_classes = [IsRMAdmin]

    @extend_schema(
        summary="Reordenar fotografías de producto",
        description=(
            "Recibe una lista de IDs de imágenes del producto y actualiza atómicamente "
            "sus posiciones en el orden suministrado (1, 2, ...)."
        ),
        request=ProductImageReorderSerializer,
        responses={200: ProductImageSerializer(many=True)},
    )
    def patch(self, request, product_id: int):
        get_object_or_404(Product, pk=product_id)
        serializer = ProductImageReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reordered = reorder_product_images(
            product_id=product_id,
            image_ids=serializer.validated_data["image_ids"],
        )
        return Response(
            ProductImageSerializer(reordered, many=True).data,
            status=status.HTTP_200_OK,
        )


class AdminProductVariantListCreateView(APIView):
    """Lista o crea combinaciones de color y talla para una prenda (HU-36)."""

    permission_classes = [IsRMAdmin]

    @extend_schema(
        summary="Listar variantes de producto",
        description="Retorna todas las combinaciones de color y talla del producto.",
        responses={200: ProductVariantSerializer(many=True)},
    )
    def get(self, request, product_id: int):
        product = get_object_or_404(Product, pk=product_id)
        variants = product.variants.order_by("size", "color")
        return Response(ProductVariantSerializer(variants, many=True).data)

    @extend_schema(
        summary="Crear variante individual de producto",
        description="Crea una nueva combinación color/talla con stock inicial opcional.",
        request=ProductVariantCreateSerializer,
        responses={201: ProductVariantSerializer},
    )
    def post(self, request, product_id: int):
        product = get_object_or_404(Product, pk=product_id)
        serializer = ProductVariantCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        variant = create_product_variant(
            product_id=product.id,
            color=data["color"],
            size=data["size"],
            stock_quantity=data.get("stock_quantity", 0),
        )
        return Response(
            ProductVariantSerializer(variant).data,
            status=status.HTTP_201_CREATED,
        )


class AdminProductVariantBulkCreateView(APIView):
    """Genera combinaciones masivas de color y talla para una prenda."""

    permission_classes = [IsRMAdmin]

    @extend_schema(
        summary="Generar variantes masivas de producto",
        description="Crea la matriz de combinaciones colores x tallas omitiendo duplicados.",
        request=ProductVariantBulkCreateSerializer,
        responses={201: ProductVariantSerializer(many=True)},
    )
    def post(self, request, product_id: int):
        product = get_object_or_404(Product, pk=product_id)
        serializer = ProductVariantBulkCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        variants = bulk_create_variants(
            product_id=product.id,
            colors=data["colors"],
            sizes=data["sizes"],
        )
        return Response(
            ProductVariantSerializer(variants, many=True).data,
            status=status.HTTP_201_CREATED,
        )


class AdminProductVariantDetailView(APIView):
    """Elimina una variante de producto (solo si stock == 0)."""

    permission_classes = [IsRMAdmin]

    @extend_schema(
        summary="Eliminar variante de producto",
        description="Elimina la variante si no posee stock (>0) ni reservas activas.",
        responses={204: None},
    )
    def delete(self, request, product_id: int, variant_id: int):
        get_object_or_404(Product, pk=product_id)
        delete_product_variant(product_id=product_id, variant_id=variant_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


def _published_products_queryset():
    """Retorna únicamente productos publicados que tienen al menos una variante (HU-1)."""
    return (
        Product.objects.filter(
            status=ProductStatus.PUBLISHED,
            variants__isnull=False,
        )
        .select_related("category")
        .prefetch_related("images", "variants")
        .distinct()
        .order_by("-created_at", "-id")
    )


class PublicCategoryListView(APIView):
    """Lista las categorías públicas del catálogo (HU-2)."""

    authentication_classes: list = []
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Listar categorías del catálogo",
        responses={200: CategorySerializer(many=True)},
    )
    def get(self, request):
        categories = Category.objects.order_by("id")
        return Response(CategorySerializer(categories, many=True).data)


class PublicProductListView(APIView):
    """Lista las prendas publicadas del catálogo sin requerir sesión (HU-1, HU-2)."""

    authentication_classes: list = []
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Listar productos publicados del catálogo",
        responses={200: PublicProductSerializer(many=True)},
    )
    def get(self, request):
        queryset = _published_products_queryset()
        category_slug = (request.query_params.get("category") or "").strip()
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        return Response(PublicProductSerializer(queryset, many=True).data)


class PublicProductDetailView(APIView):
    """Obtiene la ficha de detalle de una prenda publicada por su slug (HU-3)."""

    authentication_classes: list = []
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Obtener detalle público de una prenda por slug",
        responses={200: PublicProductSerializer},
    )
    def get(self, request, slug: str):
        product = get_object_or_404(_published_products_queryset(), slug=slug)
        return Response(PublicProductSerializer(product).data)
