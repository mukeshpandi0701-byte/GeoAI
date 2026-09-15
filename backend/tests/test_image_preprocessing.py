from io import BytesIO

from PIL import Image

from app.ai.image_preprocessing import preprocess_image


def image_bytes(*, mode: str, size: tuple[int, int], image_format: str) -> BytesIO:
    image = Image.new(mode, size, color=128)
    content = BytesIO()
    image.save(content, format=image_format)
    content.seek(0)
    return content


def test_preprocesses_valid_image_to_rgb_and_reports_properties():
    result = preprocess_image(image_bytes(mode="L", size=(20, 10), image_format="PNG"))

    assert result.is_valid
    assert result.error is None
    assert result.image.mode == "RGB"
    assert result.properties.source_format == "PNG"
    assert result.properties.original_mode == "L"
    assert result.properties.original_width == 20
    assert result.properties.original_height == 10
    assert result.properties.processed_width == 20
    assert result.properties.processed_height == 10


def test_preprocess_resizes_oversized_image_without_changing_aspect_ratio():
    result = preprocess_image(
        image_bytes(mode="RGB", size=(400, 200), image_format="PNG"),
        max_dimension=100,
    )

    assert result.is_valid
    assert result.image.size == (100, 50)
    assert (result.properties.processed_width, result.properties.processed_height) == (100, 50)


def test_preprocess_returns_failure_result_for_unreadable_image():
    result = preprocess_image(BytesIO(b"not an image"))

    assert not result.is_valid
    assert result.image is None
    assert result.properties is None
    assert result.error.startswith("Unable to read image:")
