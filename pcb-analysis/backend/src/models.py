from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class BoundingBox(BaseModel):
    x_min: int = Field(description="Left edge in pixels")
    y_min: int = Field(description="Top edge in pixels")
    x_max: int = Field(description="Right edge in pixels")
    y_max: int = Field(description="Bottom edge in pixels")


class GeminiDefectResponse(BaseModel):
    defect_type: str = Field(description="Type of defect detected")
    description: str = Field(description="Description of the defect")
    severity: Severity = Field(description="Severity level")


class DetectedDefect(BaseModel):
    defect_type: str = Field(description="Type of defect detected")
    description: str = Field(description="Description of the defect")
    severity: Severity = Field(description="Severity level")
    bounding_box: BoundingBox = Field(description="Location in pixels")


class AnalysisResult(BaseModel):
    defects: list[DetectedDefect] = Field(default_factory=list)
    total_defects: int = Field(default=0, description="Total number of defects found")
    template_image: str = Field(default="", description="Base64 reference template PNG")
    annotated_image: str = Field(default="", description="Base64 annotated PNG")
    diff_summary: str = Field(default="", description="Summary of diff analysis")
