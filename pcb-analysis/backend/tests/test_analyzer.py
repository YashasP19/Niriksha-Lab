import io
from unittest.mock import AsyncMock, patch

import numpy as np
import pytest
from PIL import Image

from src.analyzer import analyze_test_image, save_template, template_exists
from src.models import GeminiDefectResponse, Severity


def _make_png(
    size: tuple[int, int] = (200, 150),
    color: tuple[int, int, int] = (100, 100, 100),
) -> bytes:
    img = Image.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _make_png_with_rect(
    size: tuple[int, int] = (200, 150),
    bg_color: tuple[int, int, int] = (100, 100, 100),
    rect: tuple[int, int, int, int] = (50, 40, 100, 90),
    rect_color: tuple[int, int, int] = (255, 0, 0),
) -> bytes:
    img = Image.new("RGB", size, bg_color)
    arr = np.array(img)
    x1, y1, x2, y2 = rect
    arr[y1:y2, x1:x2] = rect_color
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture(autouse=True)
def _setup_template(tmp_path, monkeypatch):
    """Point template storage at a temp directory."""
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    monkeypatch.setattr("src.analyzer.TEMPLATE_DIR", template_dir)
    monkeypatch.setattr("src.analyzer.TEMPLATE_FILE", template_dir / "template.png")


@pytest.mark.asyncio
async def test_analyze_no_diff():
    """Identical images should produce zero defects."""
    img = _make_png()
    save_template(img)

    mock_response = GeminiDefectResponse(
        defect_type="none",
        description="No defect",
        severity=Severity.LOW,
    )

    with patch("src.analyzer.gemini_client.classify_crop", new_callable=AsyncMock) as mock_classify:
        mock_classify.return_value = mock_response
        result = await analyze_test_image(img)

    assert result.total_defects == 0
    assert result.defects == []
    assert result.template_image != ""
    assert "No differences" in result.diff_summary
    mock_classify.assert_not_called()


@pytest.mark.asyncio
async def test_analyze_with_diff():
    """A modified image should produce defects."""
    template = _make_png()
    test = _make_png_with_rect(rect=(50, 40, 100, 90), rect_color=(255, 255, 255))

    save_template(template)

    mock_response = GeminiDefectResponse(
        defect_type="damaged_trace",
        description="Trace appears damaged",
        severity=Severity.HIGH,
    )

    with patch("src.analyzer.gemini_client.classify_crop", new_callable=AsyncMock) as mock_classify, \
         patch("src.analyzer.gemini_client.annotate_crop", new_callable=AsyncMock) as mock_annotate:
        mock_classify.return_value = mock_response
        mock_annotate.return_value = None  # fall back to Pillow
        result = await analyze_test_image(test)

    assert result.total_defects >= 1
    assert len(result.defects) >= 1
    assert result.defects[0].defect_type == "damaged_trace"
    assert result.defects[0].severity == Severity.HIGH
    assert result.annotated_image != ""
    assert result.template_image != ""
    assert "difference region" in result.diff_summary
    mock_classify.assert_called()
    mock_annotate.assert_called()


@pytest.mark.asyncio
async def test_analyze_result_shape():
    """Result should have all expected fields."""
    template = _make_png()
    test = _make_png_with_rect(rect=(50, 40, 100, 90), rect_color=(255, 255, 255))

    save_template(template)

    mock_response = GeminiDefectResponse(
        defect_type="short",
        description="Solder bridge",
        severity=Severity.MEDIUM,
    )

    with patch("src.analyzer.gemini_client.classify_crop", new_callable=AsyncMock) as mock_classify, \
         patch("src.analyzer.gemini_client.annotate_crop", new_callable=AsyncMock) as mock_annotate:
        mock_classify.return_value = mock_response
        mock_annotate.return_value = None  # fall back to Pillow
        result = await analyze_test_image(test)

    # Check all fields exist
    data = result.model_dump()
    assert "defects" in data
    assert "total_defects" in data
    assert "template_image" in data
    assert "annotated_image" in data
    assert "diff_summary" in data

    # Check defect structure
    for defect in data["defects"]:
        assert "defect_type" in defect
        assert "description" in defect
        assert "severity" in defect
        assert "bounding_box" in defect
        bb = defect["bounding_box"]
        assert all(k in bb for k in ("x_min", "y_min", "x_max", "y_max"))


def test_template_save_and_exists():
    """Template should be saveable and detectable."""
    assert not template_exists()
    save_template(_make_png())
    assert template_exists()
