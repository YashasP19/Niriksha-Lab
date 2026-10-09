import json

from src.models import (
    AnalysisResult,
    BoundingBox,
    DetectedDefect,
    GeminiDefectResponse,
    Severity,
)


def test_severity_values():
    assert Severity.LOW.value == "low"
    assert Severity.MEDIUM.value == "medium"
    assert Severity.HIGH.value == "high"


def test_bounding_box_pixel_coords():
    box = BoundingBox(x_min=10, y_min=20, x_max=50, y_max=60)
    assert box.x_min == 10
    assert box.y_min == 20
    assert box.x_max == 50
    assert box.y_max == 60


def test_gemini_defect_response():
    resp = GeminiDefectResponse(
        defect_type="solder_bridge",
        description="Solder bridging two pads",
        severity=Severity.HIGH,
    )
    data = resp.model_dump()
    assert data["defect_type"] == "solder_bridge"
    assert data["severity"] == "high"
    assert data["description"] == "Solder bridging two pads"


def test_gemini_defect_response_json_roundtrip():
    resp = GeminiDefectResponse(
        defect_type="missing_component",
        description="IC chip missing from socket",
        severity=Severity.HIGH,
    )
    json_str = resp.model_dump_json()
    restored = GeminiDefectResponse.model_validate_json(json_str)
    assert restored.defect_type == "missing_component"
    assert restored.severity == Severity.HIGH


def test_detected_defect():
    defect = DetectedDefect(
        defect_type="scratch",
        description="Surface scratch on trace",
        severity=Severity.LOW,
        bounding_box=BoundingBox(x_min=100, y_min=200, x_max=150, y_max=250),
    )
    data = defect.model_dump()
    assert data["defect_type"] == "scratch"
    assert data["bounding_box"]["x_min"] == 100
    assert data["severity"] == "low"


def test_analysis_result():
    result = AnalysisResult(
        defects=[
            DetectedDefect(
                defect_type="open_circuit",
                description="Break in trace",
                severity=Severity.HIGH,
                bounding_box=BoundingBox(x_min=20, y_min=30, x_max=40, y_max=50),
            )
        ],
        total_defects=1,
        annotated_image="base64data",
        diff_summary="Found 1 region",
    )
    assert result.total_defects == 1
    assert result.defects[0].defect_type == "open_circuit"
    assert result.diff_summary == "Found 1 region"


def test_analysis_result_json_roundtrip():
    result = AnalysisResult(
        defects=[
            DetectedDefect(
                defect_type="short",
                description="Copper bridge",
                severity=Severity.MEDIUM,
                bounding_box=BoundingBox(x_min=10, y_min=20, x_max=30, y_max=40),
            )
        ],
        total_defects=1,
        annotated_image="abc123",
        diff_summary="1 difference found",
    )
    json_str = result.model_dump_json()
    restored = AnalysisResult.model_validate_json(json_str)
    assert restored.total_defects == 1
    assert restored.defects[0].defect_type == "short"


def test_analysis_result_defaults():
    result = AnalysisResult()
    assert result.defects == []
    assert result.total_defects == 0
    assert result.template_image == ""
    assert result.annotated_image == ""
    assert result.diff_summary == ""


def test_analysis_result_json_schema():
    schema = AnalysisResult.model_json_schema()
    assert "properties" in schema
    assert "defects" in schema["properties"]
    assert "annotated_image" in schema["properties"]
