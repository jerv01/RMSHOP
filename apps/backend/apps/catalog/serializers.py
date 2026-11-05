from rest_framework import serializers

from apps.catalog.models import (
    Category,
    Product,
    ProductImage,
    ProductStatus,
    ProductVariant,
)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug"]


class ProductCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    description = serializers.CharField()
    price = serializers.DecimalField(max_digits=12, decimal_places=0, min_value=1)
    previous_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=0,
        min_value=1,
        required=False,
        allow_null=True,
    )
    material = serializers.CharField(max_length=120)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source="category",
        error_messages={"does_not_exist": "La categoría seleccionada no existe."},
    )


class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    warning = serializers.CharField(read_only=True, required=False, allow_null=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "price",
            "previous_price",
            "material",
            "category",
            "status",
            "created_at",
            "updated_at",
            "warning",
        ]


class ProductUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False)
    price = serializers.DecimalField(
        max_digits=12,
        decimal_places=0,
        min_value=1,
        required=False,
    )
    previous_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=0,
        min_value=1,
        required=False,
        allow_null=True,
    )
    material = serializers.CharField(max_length=120, required=False)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source="category",
        required=False,
        error_messages={"does_not_exist": "La categoría seleccionada no existe."},
    )
    status = serializers.ChoiceField(choices=ProductStatus.choices, required=False)


class ProductImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = [
            "id",
            "product_id",
            "image_url",
            "alt_text",
            "position",
            "created_at",
        ]

    def get_image_url(self, obj: ProductImage) -> str | None:
        if obj.image:
            return obj.image.url
        return None


class ProductImageUploadSerializer(serializers.Serializer):
    image = serializers.FileField()
    alt_text = serializers.CharField(max_length=255, required=False, allow_blank=True)
    position = serializers.IntegerField(min_value=1, max_value=3, required=False)


class ProductImageReorderSerializer(serializers.Serializer):
    image_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=3,
    )


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = [
            "id",
            "product_id",
            "color",
            "size",
            "stock_quantity",
            "created_at",
            "updated_at",
        ]


class ProductVariantCreateSerializer(serializers.Serializer):
    color = serializers.CharField(max_length=50)
    size = serializers.CharField(max_length=20)
    stock_quantity = serializers.IntegerField(min_value=0, default=0, required=False)


class ProductVariantBulkCreateSerializer(serializers.Serializer):
    colors = serializers.ListField(
        child=serializers.CharField(max_length=50),
        min_length=1,
    )
    sizes = serializers.ListField(
        child=serializers.CharField(max_length=20),
        min_length=1,
    )


class PublicProductSerializer(serializers.ModelSerializer):
    """Producto publicado para el catálogo público y su ficha de detalle (HU-1, HU-2, HU-3)."""

    category = CategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    in_stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "price",
            "previous_price",
            "material",
            "category",
            "status",
            "images",
            "variants",
            "in_stock",
            "created_at",
            "updated_at",
        ]

    def get_in_stock(self, obj: Product) -> bool:
        return any(variant.stock_quantity > 0 for variant in obj.variants.all())
