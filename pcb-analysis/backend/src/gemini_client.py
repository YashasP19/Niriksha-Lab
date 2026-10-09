from __future__ import annotations

import asyncio
import logging
import time

from google import genai
from google.genai import types

from .config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_TEMPERATURE, RATE_LIMIT_DELAY
from .models import GeminiDefectResponse
from .prompts import ANNOTATE_CROP_PROMPT, CROP_CLASSIFICATION_PROMPT

logger = logging.getLogger(__name__)


class GeminiClient:
    def __init__(self) -> None:
        self._client = genai.Client(api_key=GEMINI_API_KEY)
        self._last_request_time: float = 0.0
        self._lock = asyncio.Lock()

    async def _wait_for_rate_limit(self) -> None:
        async with self._lock:
            elapsed = time.monotonic() - self._last_request_time
            if elapsed < RATE_LIMIT_DELAY:
                await asyncio.sleep(RATE_LIMIT_DELAY - elapsed)
            self._last_request_time = time.monotonic()

    async def classify_crop(
        self,
        crop_raw: bytes,
        crop_highlighted: bytes,
        mime_type: str = "image/png",
    ) -> GeminiDefectResponse:
        await self._wait_for_rate_limit()

        try:
            response = await asyncio.to_thread(
                self._client.models.generate_content,
                model=GEMINI_MODEL,
                contents=[
                    types.Content(
                        parts=[
                            types.Part.from_bytes(data=crop_raw, mime_type=mime_type),
                            types.Part.from_bytes(data=crop_highlighted, mime_type=mime_type),
                            types.Part.from_text(text=CROP_CLASSIFICATION_PROMPT),
                        ]
                    )
                ],
                config=types.GenerateContentConfig(
                    temperature=GEMINI_TEMPERATURE,
                    response_mime_type="application/json",
                    response_schema=GeminiDefectResponse,
                ),
            )

            return GeminiDefectResponse.model_validate_json(response.text)

        except Exception:
            logger.exception("Gemini API call failed")
            return GeminiDefectResponse(
                defect_type="unknown",
                description="Classification failed due to an API error.",
                severity="medium",
            )

    async def annotate_crop(
        self,
        crop_bytes: bytes,
        defect_type: str,
        severity: str,
        description: str,
        mime_type: str = "image/png",
    ) -> bytes | None:
        """Send a diff crop to Gemini and get back the crop with annotations drawn.

        Returns annotated crop as PNG bytes, or None if Gemini fails.
        """
        await self._wait_for_rate_limit()

        prompt = ANNOTATE_CROP_PROMPT.format(
            defect_type=defect_type,
            severity=severity,
            description=description,
        )

        try:
            response = await asyncio.to_thread(
                self._client.models.generate_content,
                model=GEMINI_MODEL,
                contents=[
                    types.Content(
                        parts=[
                            types.Part.from_bytes(data=crop_bytes, mime_type=mime_type),
                            types.Part.from_text(text=prompt),
                        ]
                    )
                ],
                config=types.GenerateContentConfig(
                    temperature=GEMINI_TEMPERATURE,
                    response_modalities=["IMAGE", "TEXT"],
                ),
            )

            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                    return part.inline_data.data

            logger.warning("Gemini did not return an image in annotate_crop response")
            return None

        except Exception:
            logger.exception("Gemini annotate_crop call failed")
            return None


gemini_client = GeminiClient()
