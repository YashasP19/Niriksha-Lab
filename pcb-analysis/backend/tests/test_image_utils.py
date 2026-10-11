import base64
import io

from PIL import Image

from src.image_utils import draw_bounding_boxes
from src.models import BoundingBox, DetectedDefect, Severity


def _make_png(color: tuple[int, int, int], size: tuple[int, int] = (200, 150)) -> bytes:
    """Create a solid-color PNG image as bytes."""
    img = Image.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_draw_bounding_boxes_returns_valid_base64_png():
    """Output should be a valid base64-encoded PNG."""
    image_bytes = _make_png((100, 100, 100))
    defects = [
        DetectedDefect(
            defect_type="scratch",
            description="Surface scratch",
            severity=Severity.LOW,
            bounding_box=BoundingBox(x_min=10, y_min=10, x_max=50, y_max=50),
        )
    ]
    result = draw_bounding_boxes(image_bytes, defects)
    decoded = base64.b64decode(result)
    img = Image.open(io.BytesIO(decoded))
    assert img.format == "PNG"


def test_draw_bounding_boxes_empty_defects():
    """Empty defect list should return the image unmodified (as base64 PNG)."""
    image_bytes = _make_png((100, 100, 100), size=(100, 80))
    result = draw_bounding_boxes(image_bytes, [])
    decoded = base64.b64decode(result)
    img = Image.open(io.BytesIO(decoded))
    assert img.format == "PNG"
    assert img.size == (100, 80)


def test_draw_bounding_boxes_preserves_dimensions():
    """Output image should keep the same dimensions as input."""
    size = (300, 200)
    image_bytes = _make_png((50, 50, 50), size=size)
    defects = [
        DetectedDefect(
            defect_type="short",
            description="Copper bridge",
            severity=Severity.HIGH,
            bounding_box=BoundingBox(x_min=20, y_min=20, x_max=100, y_max=100),
        ),
        DetectedDefect(
            defect_type="open_circuit",
            description="Broken trace",
            severity=Severity.MEDIUM,
            bounding_box=BoundingBox(x_min=150, y_min=50, x_max=250, y_max=150),
        ),
    ]
    result = draw_bounding_boxes(image_bytes, defects)
    decoded = base64.b64decode(result)
    img = Image.open(io.BytesIO(decoded))
    assert img.size == size


def test_draw_bounding_boxes_modifies_pixels():
    """Drawing annotations should change pixel values."""
    image_bytes = _make_png((128, 128, 128), size=(100, 100))
    defects = [
        DetectedDefect(
            defect_type="corrosion",
            description="Corrosion on pad",
            severity=Severity.MEDIUM,
            bounding_box=BoundingBox(x_min=10, y_min=10, x_max=90, y_max=90),
        )
    ]
    result = draw_bounding_boxes(image_bytes, defects)
    decoded = base64.b64decode(result)

    original = Image.open(io.BytesIO(image_bytes))
    annotated = Image.open(io.BytesIO(decoded))
    assert list(original.getdata()) != list(annotated.getdata())
