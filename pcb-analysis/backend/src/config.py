from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = "gemini-3.1-flash-image-preview"
GEMINI_TEMPERATURE: float = 0.1

CORS_ORIGINS: list[str] = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

RATE_LIMIT_DELAY: float = float(os.getenv("RATE_LIMIT_DELAY", "4.0"))

MAX_IMAGE_DIMENSION: int = 2048

TEMPLATE_DIR: Path = BASE_DIR / "templates"
DIFF_THRESHOLD: int = 30
MIN_CONTOUR_AREA: int = 100
CROP_PADDING: int = 20
