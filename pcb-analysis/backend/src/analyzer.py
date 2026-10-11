from __future__ import annotations

import io
import logging

from PIL import Image

from .config import TEMPLATE_DIR
from .diff_engine import compute_diff
from .gemini_client import gemini_client
from .image_utils import composite_crops, draw_bounding_boxes, image_to_base64
from .models import AnalysisResult, BoundingBox, DetectedDefect

logger = logging.getLogger(__name__)

TEMPLATE_FILE = TEMPLATE_DIR / "template.png"


def save_template(image_bytes: bytes) -> None:
    """Save the reference template image to disk as PNG."""
    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    TEMPLATE_FILE.write_bytes(buf.getvalue())


def load_template() -> bytes:
    """Load the stored template image bytes."""
    if not TEMPLATE_FILE.exists():
        raise FileNotFoundError("No template image has been uploaded")
    return TEMPLATE_FILE.read_bytes()


def template_exists() -> bool:
    """Check if a template image has been saved."""
    return TEMPLATE_FILE.exists()


async def analyze_test_image(test_bytes: bytes) -> AnalysisResult:
    """Analyze a test image by diffing against the stored template."""
    template_bytes = load_template()
    template_b64 = image_to_base64(template_bytes)

    # Ensure test image is PNG
    img = Image.open(io.BytesIO(test_bytes)).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    test_png = buf.getvalue()

    # Compute diff regions (raises ValueError on dimension mismatch)
    regions = compute_diff(template_bytes, test_png)

    if not regions:
        return AnalysisResult(
            defects=[],
            total_defects=0,
            template_image=template_b64,
            annotated_image=image_to_base64(test_png),
            diff_summary="No differences detected between template and test image.",
        )

    # Classify each diff region and get annotated crops from Gemini
    defects: list[DetectedDefect] = []
    annotated_crops: list[tuple[BoundingBox, bytes]] = []
    all_annotated = True

    for region in regions:
        # Step 1: classify the crop (raw + highlighted so Gemini describes the actual board)
        classification = await gemini_client.classify_crop(
            crop_raw=region.crop_raw,
            crop_highlighted=region.crop_highlighted,
        )
        defect = DetectedDefect(
            defect_type=classification.defect_type,
            description=classification.description,
            severity=classification.severity,
            bounding_box=region.bounding_box,
        )
        defects.append(defect)

        # Step 2: ask Gemini to annotate the crop with bounding box
        annotated_crop = await gemini_client.annotate_crop(
            crop_bytes=region.crop_highlighted,
            defect_type=classification.defect_type,
            severity=classification.severity.value,
            description=classification.description,
        )

        if annotated_crop is not None:
            annotated_crops.append((region.bounding_box, annotated_crop))
        else:
            all_annotated = False

    # Composite annotated crops onto original image, or fall back to Pillow
    if annotated_crops and all_annotated:
        annotated_b64 = composite_crops(test_png, annotated_crops)
    else:
        logger.info("Gemini crop annotation incomplete, falling back to Pillow")
        annotated_b64 = draw_bounding_boxes(test_png, defects)

    diff_summary = (
        f"Found {len(regions)} difference region(s) between template and test image. "
        f"Total diff area: {sum(r.area for r in regions)} pixels."
    )

    return AnalysisResult(
        defects=defects,
        total_defects=len(defects),
        template_image=template_b64,
        annotated_image=annotated_b64,
        diff_summary=diff_summary,
    )
