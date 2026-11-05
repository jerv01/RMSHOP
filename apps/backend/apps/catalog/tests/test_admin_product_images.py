import io
from decimal import Decimal

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient

from apps.catalog.models import Category
from apps.catalog.services import create_product, upload_product_image
from apps.users.clerk import ClerkClaims
from apps.users.models import User


def _create_test_image(name: str = "test.jpg", format: str = "JPEG"):
    buf = io.BytesIO()
    img = Image.new("RGB", (400, 300), color="blue")
    img.save(buf, format=format)
    buf.seek(0)
    return SimpleUploadedFile(name, buf.getvalue(), content_type=f"image/{format.lower()}")


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_client(db):
    client = APIClient()
    user = User.objects.create(clerk_user_id="admin_img_1", email="admin@rmshop.co")
    claims = ClerkClaims(sub="admin_img_1", email="admin@rmshop.co", role="admin")
    client.force_authenticate(user=user, token=claims)
    return client


@pytest.fixture
def customer_client(db):
    client = APIClient()
    user = User.objects.create(clerk_user_id="cust_img_1", email="cliente@rmshop.co")
    claims = ClerkClaims(sub="cust_img_1", email="cliente@rmshop.co", role=None)
    client.force_authenticate(user=user, token=claims)
    return client


@pytest.fixture
def sample_product(db):
    category = Category.objects.get(slug="camisetas-tops")
    product, _ = create_product(
        name="Camiseta Deportiva",
        description="Ideal para entrenamiento",
        price=Decimal("55000"),
        material="Poliéster",
        category=category,
    )
    return product


@pytest.mark.django_db
def test_admin_can_upload_product_image(admin_client, sample_product):
    image_file = _create_test_image("foto.png", format="PNG")
    response = admin_client.post(
        f"/api/v1/admin/products/{sample_product.id}/images/",
        {"image": image_file, "alt_text": "Camiseta vista frontal"},
        format="multipart",
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["id"] is not None
    assert data["product_id"] == sample_product.id
    assert data["alt_text"] == "Camiseta vista frontal"
    assert data["position"] == 1
    assert data["image_url"].endswith(".webp")


@pytest.mark.django_db
def test_upload_image_fallback_alt_text_uses_product_name(admin_client, sample_product):
    image_file = _create_test_image("foto.jpg", format="JPEG")
    response = admin_client.post(
        f"/api/v1/admin/products/{sample_product.id}/images/",
        {"image": image_file},
        format="multipart",
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["alt_text"] == sample_product.name


@pytest.mark.django_db
def test_admin_cannot_upload_more_than_three_images(admin_client, sample_product):
    for i in range(3):
        upload_product_image(
            product_id=sample_product.id,
            file=_create_test_image(f"f{i}.jpg"),
        )

    response = admin_client.post(
        f"/api/v1/admin/products/{sample_product.id}/images/",
        {"image": _create_test_image("f4.jpg")},
        format="multipart",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["code"] == "validation_error"
    assert "image" in data["fields"]


@pytest.mark.django_db
def test_upload_rejects_non_image_file(admin_client, sample_product):
    fake_file = SimpleUploadedFile("fake.txt", b"not an image", content_type="text/plain")
    response = admin_client.post(
        f"/api/v1/admin/products/{sample_product.id}/images/",
        {"image": fake_file},
        format="multipart",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["code"] == "validation_error"
    assert "image" in data["fields"]


@pytest.mark.django_db
def test_admin_can_list_product_images(admin_client, sample_product):
    upload_product_image(product_id=sample_product.id, file=_create_test_image("1.jpg"))
    upload_product_image(product_id=sample_product.id, file=_create_test_image("2.jpg"))

    response = admin_client.get(f"/api/v1/admin/products/{sample_product.id}/images/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    assert data[0]["position"] == 1
    assert data[1]["position"] == 2


@pytest.mark.django_db
def test_admin_can_delete_image_and_positions_recompact(admin_client, sample_product):
    img1 = upload_product_image(product_id=sample_product.id, file=_create_test_image("1.jpg"))
    img2 = upload_product_image(product_id=sample_product.id, file=_create_test_image("2.jpg"))
    img3 = upload_product_image(product_id=sample_product.id, file=_create_test_image("3.jpg"))

    response = admin_client.delete(f"/api/v1/admin/products/{sample_product.id}/images/{img2.id}/")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verificar que quedan 2 imágenes con posiciones 1 y 2
    list_response = admin_client.get(f"/api/v1/admin/products/{sample_product.id}/images/")
    remaining = list_response.json()
    assert len(remaining) == 2
    assert remaining[0]["id"] == img1.id and remaining[0]["position"] == 1
    assert remaining[1]["id"] == img3.id and remaining[1]["position"] == 2


@pytest.mark.django_db
def test_admin_can_reorder_product_images(admin_client, sample_product):
    img1 = upload_product_image(product_id=sample_product.id, file=_create_test_image("1.jpg"))
    img2 = upload_product_image(product_id=sample_product.id, file=_create_test_image("2.jpg"))

    response = admin_client.patch(
        f"/api/v1/admin/products/{sample_product.id}/images/reorder/",
        {"image_ids": [img2.id, img1.id]},
        format="json",
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data[0]["id"] == img2.id and data[0]["position"] == 1
    assert data[1]["id"] == img1.id and data[1]["position"] == 2


@pytest.mark.django_db
def test_permissions_image_endpoints(api_client, customer_client, sample_product):
    url = f"/api/v1/admin/products/{sample_product.id}/images/"

    # Unauthenticated
    assert api_client.get(url).status_code == status.HTTP_401_UNAUTHORIZED
    assert api_client.post(url).status_code == status.HTTP_401_UNAUTHORIZED

    # Regular customer
    assert customer_client.get(url).status_code == status.HTTP_403_FORBIDDEN
    assert customer_client.post(url).status_code == status.HTTP_403_FORBIDDEN
