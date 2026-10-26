from PIL import Image
from io import BytesIO
from image_quality import inspect_image


def test_rejects_non_image_bytes():
    assert inspect_image(b"not an image")["ok"] is False


def test_checks_dimensions():
    image = Image.new("RGB", (100, 100), "white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    result = inspect_image(buffer.getvalue())
    assert result["ok"] is False
    assert "too small" in result["message"]
