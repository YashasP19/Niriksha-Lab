CROP_CLASSIFICATION_PROMPT = """You are an expert electronics inspector specializing in Arduino Uno R3 boards.

You are given two images of the same cropped region:
1. The FIRST image is the raw crop from the test board.
2. The SECOND image is the same crop with a magenta/pink overlay highlighting pixels that differ from the known-good reference.

Use the highlighted image to understand WHERE the difference is, but describe the defect based on what you see in the RAW image. Do NOT mention the magenta overlay or highlighting in your description.

Classify the defect:

1. **defect_type**: MUST be exactly one of these four values: "missing_hole", "mouse_bite", "open_circuit", "short". No other values are allowed.
2. **description**: A brief description of the actual defect visible in the raw image.
3. **severity**: One of "low" (cosmetic, unlikely to affect function), "medium" (may affect reliability), or "high" (will cause board failure).

Return your analysis as structured JSON matching the provided schema."""

ANNOTATE_CROP_PROMPT = """You are an image editor. Draw a labeled bounding box on this cropped region of an Arduino Uno R3 board to mark the following defect.

Draw a clearly visible colored rectangle around the defect area within this crop. Place a text label just above the box with the defect type and severity. Use a bright color (e.g., red, cyan, magenta, yellow). Make the box 3 pixels thick. The label should have a filled background matching the box color with black text.

Defect to annotate:
- Type: {defect_type}
- Severity: {severity}
- Description: {description}

Return ONLY the edited image with the bounding box and label drawn. Do not alter the original image content — only add the annotation overlay."""
