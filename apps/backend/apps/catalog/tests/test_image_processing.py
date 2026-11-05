import io

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.catalog.services import process_image


def _create_image_file(name: str, format: str = "JPEG", size=(2000, 1000), color="blue"):
    buf = io.BytesIO()
    img = Image.new("RGB", size, color=color)
    img.save(buf, format=format)
    buf.seek(0)
    return SimpleUploadedFile(name, buf.getvalue(), content_type=f"image/{format.lower()}")


def test_process_image_resizes_and_converts_to_webp():
    uploaded = _create_image_file("foto.jpg", format="JPEG", size=(2000, 1000))
    result = process_image(uploaded)

    assert result.name.endswith(".webp")
    # Verify image dimensions and format with Pillow
    img = Image.open(result)
    assert img.format == "WEBP"
    assert max(img.width, img.height) == 1600
    assert img.width == 1600
    assert img.height == 800


def test_process_image_retains_small_dimensions():
    uploaded = _create_image_file("pequena.png", format="PNG", size=(800, 600))
    result = process_image(uploaded)

    img = Image.open(result)
    assert img.format == "WEBP"
    assert img.width == 800
    assert img.height == 600


def test_process_image_rejects_corrupted_or_non_image():
    uploaded = SimpleUploadedFile("fake.txt", b"not an image", content_type="text/plain")
    with pytest.raises(ValidationError) as exc:
        process_image(uploaded)
    assert "image" in exc.value.message_dict


def test_process_image_rejects_oversized_file():
    # 6 MB fake file
    big_data = b"0" * (6 * 1024 * 1024)
    uploaded = SimpleUploadedFile("big.jpg", big_data, content_type="image/jpeg")
    with pytest.raises(ValidationError) as exc:
        process_image(uploaded)
    assert "image" in exc.value.message_dict
