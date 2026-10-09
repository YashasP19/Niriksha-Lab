from __future__ import annotations

import base64
from dataclasses import dataclass, field
import time
from typing import Any, Callable

from google import genai
from google.genai import types
import requests

from .key_pool import ApiKeyPool, KeyUnavailableError
from .prompts import ANNOTATE_CROP_PROMPT, CROP_CLASSIFICATION_PROMPT
from .schemas import GeminiDefectResponse, ModelInfo
from .utils import safe_json_loads

MODEL_PRIORITY = [
    "gemini-3.1-flash-image-preview",
    "gemini-3.1-pro",
    "gemini-3.1-pro-preview",
    "gemini-3.1-pro-preview-customtools",
    "gemini-3-flash-preview",
    "gemini-3-pro-preview",
    "gemini-2.5-pro",
    "gemini-2.5-flash",
]

MODEL_ALIAS = {
    "gemini-3.1-flash": "gemini-3.1-flash-image-preview",
    "gemini-3.1-flash-image": "gemini-3.1-flash-image-preview",
}

# Models that are image-focused and unreliable for structured JSON output.
# generate_json will swap to JSON_FALLBACK_MODEL for these.
_IMAGE_ONLY_MODELS = {"gemini-3.1-flash-image-preview"}
JSON_FALLBACK_MODEL = "gemini-3.1-pro-preview"


@dataclass
class GeminiService:
    api_keys: list[str]
    request_timeout_sec: int = 45
    key_pool: ApiKeyPool = field(init=False)

    def __post_init__(self) -> None:
        self.key_pool = ApiKeyPool(keys=self.api_keys)
        self._clients: dict[str, genai.Client] = {}

    def _client_for_key(self, key: str) -> genai.Client:
        client = self._clients.get(key)
        if client is None:
            client = genai.Client(
                api_key=key,
                http_options=types.HttpOptions(timeout=max(1, int(self.request_timeout_sec * 1000))),
            )
            self._clients[key] = client
        return client

    def _with_retry(self, operation: Callable[[genai.Client], Any], max_attempts: int | None = None) -> Any:
        attempts = max_attempts or max(4, len(self.api_keys) * 3)
        last_error: Exception | None = None

        for attempt in range(attempts):
            try:
                slot = self.key_pool.acquire()
            except KeyUnavailableError as exc:
                wait_seconds = self.key_pool.next_available_in_seconds()
                if wait_seconds == float("inf"):
                    last_error = exc
                    break
                # Wait longer on repeated cooldowns (up to 10s)
                sleep_time = min(wait_seconds + 0.5, 10.0)
                time.sleep(sleep_time)
                last_error = exc
                continue

            client = self._client_for_key(slot.key)
            try:
                result = operation(client)
                self.key_pool.report_success(slot)
                return result
            except Exception as exc:
                self.key_pool.report_failure(slot, exc)
                last_error = exc

        if last_error:
            raise last_error
        raise RuntimeError("Gemini operation failed without specific error")

    def list_generate_models(self) -> list[ModelInfo]:
        discovered: dict[str, ModelInfo] = {}

        def _list_once(client: genai.Client) -> list[ModelInfo]:
            models: list[ModelInfo] = []
            for model in client.models.list():
                raw_name = getattr(model, "name", "") or ""
                name = raw_name.replace("models/", "")
                if not name:
                    continue

                actions = list(getattr(model, "supported_actions", []) or [])
                if actions and "generateContent" not in actions:
                    continue

                models.append(
                    ModelInfo(
                        name=name,
                        display_name=getattr(model, "display_name", None),
                        supported_actions=actions,
                    )
                )
            return models

        # Probe each key once to avoid missing models due per-key entitlement differences.
        attempts = max(1, len(self.api_keys))
        for _ in range(attempts):
            try:
                partial = self._with_retry(_list_once, max_attempts=1)
            except Exception:
                continue
            for item in partial:
                discovered[item.name] = item

        if not discovered:
            raise RuntimeError("Could not list Gemini models from any configured API key")

        return sorted(discovered.values(), key=lambda m: m.name)

    @staticmethod
    def resolve_model_name(model_name: str | None) -> str | None:
        if not model_name:
            return None
        return MODEL_ALIAS.get(model_name, model_name)

    @staticmethod
    def pick_recommended_model(
        available: list[ModelInfo],
        default_model: str | None = None,
    ) -> str:
        names = {m.name for m in available}
        resolved_default = GeminiService.resolve_model_name(default_model)
        if resolved_default and resolved_default in names:
            return resolved_default

        for candidate in MODEL_PRIORITY:
            resolved_candidate = GeminiService.resolve_model_name(candidate)
            if resolved_candidate in names:
                return resolved_candidate

        if available:
            return available[0].name

        return "gemini-3.1-flash-image-preview"

    def generate_json(
        self,
        *,
        model: str,
        prompt: str,
        response_schema: dict[str, Any],
        temperature: float,
        max_output_tokens: int,
        image_parts: list[tuple[bytes, str]] | None = None,
    ) -> dict[str, Any]:
        # Image-focused models are unreliable for structured JSON;
        # swap to the pro model for JSON generation.
        if model in _IMAGE_ONLY_MODELS:
            model = JSON_FALLBACK_MODEL

        parts: list[Any] = [prompt]
        for image_bytes, mime_type in image_parts or []:
            parts.append(types.Part.from_bytes(data=image_bytes, mime_type=mime_type))

        is_pro_thinking_model = (
            model.startswith("gemini-3.1-pro")
            or model.startswith("gemini-3-pro-preview")
        )
        thinking_budget = 128 if is_pro_thinking_model else 0
        effective_max_output_tokens = max(
            max_output_tokens,
            2048 if is_pro_thinking_model else max_output_tokens,
        )

        primary_config: dict[str, Any] = {
            "temperature": temperature,
            "max_output_tokens": effective_max_output_tokens,
            "response_mime_type": "application/json",
            "response_schema": response_schema,
            "response_json_schema": response_schema,
        }
        if thinking_budget > 0:
            primary_config["thinking_config"] = {"thinking_budget": thinking_budget}
        fallback_config = {
            "temperature": temperature,
            "max_output_tokens": effective_max_output_tokens,
            "response_mime_type": "application/json",
            "response_schema": response_schema,
            "response_json_schema": response_schema,
        }
        if is_pro_thinking_model:
            fallback_config["thinking_config"] = {"thinking_budget": thinking_budget}

        def _op(client: genai.Client):
            return client.models.generate_content(
                model=model,
                contents=parts,
                config=primary_config,
            )

        try:
            response = self._with_retry(_op)
        except Exception as exc:
            message = str(exc).lower()
            if "only works in thinking mode" in message or "budget 0 is invalid" in message:
                response = self._with_retry(
                    lambda client: client.models.generate_content(
                        model=model,
                        contents=parts,
                        config=fallback_config,
                    )
                )
            else:
                raise
        parsed = self._try_parse_json_response(response)
        if parsed is not None:
            return parsed

        # Second pass: strict repair instruction.
        repair_prompt = (
            f"{prompt}\n\n"
            "IMPORTANT: return ONLY valid JSON object. No markdown, no preamble, no trailing text."
        )

        def _repair_op(client: genai.Client):
            return client.models.generate_content(
                model=model,
                contents=[repair_prompt, *parts[1:]],
                config={
                    **fallback_config,
                    "max_output_tokens": max(
                        effective_max_output_tokens,
                        3072 if is_pro_thinking_model else effective_max_output_tokens,
                    ),
                },
            )

        repair_response = self._with_retry(_repair_op)
        parsed_repair = self._try_parse_json_response(repair_response)
        if parsed_repair is not None:
            return parsed_repair

        raise ValueError("Model output did not contain valid JSON")

    def probe_vision_models(
        self,
        *,
        candidate_models: list[str],
        image_bytes: bytes,
        mime_type: str = "image/png",
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")

        for model in candidate_models:
            try:
                text = self._probe_vision_once_via_rest(
                    model=model,
                    encoded_image=encoded_image,
                    mime_type=mime_type,
                )
                sample = text[:120] if text else "(empty text response)"
                rows.append({"model": model, "vision_callable": True, "sample_response": sample})
            except Exception as exc:
                rows.append({"model": model, "vision_callable": False, "error": str(exc)[:200]})

        return rows

    def _probe_vision_once_via_rest(self, *, model: str, encoded_image: str, mime_type: str) -> str:
        attempts = max(1, min(3, len(self.api_keys)))
        last_error: Exception | None = None

        for _ in range(attempts):
            try:
                slot = self.key_pool.acquire()
            except KeyUnavailableError as exc:
                wait_seconds = self.key_pool.next_available_in_seconds()
                if wait_seconds != float("inf"):
                    time.sleep(min(wait_seconds, 1.0))
                    last_error = exc
                    continue
                last_error = exc
                break

            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": "Does this image show any manufacturing defect? Reply in one short sentence."},
                            {"inline_data": {"mime_type": mime_type, "data": encoded_image}},
                        ]
                    }
                ],
                "generationConfig": {"temperature": 0, "maxOutputTokens": 40},
            }

            try:
                response = requests.post(
                    url,
                    params={"key": slot.key},
                    json=payload,
                    timeout=7,
                )
                if response.status_code >= 400:
                    raise RuntimeError(f"{response.status_code} {response.text[:180]}")

                body = response.json()
                text = self._extract_text_from_rest_response(body)
                self.key_pool.report_success(slot)
                return text
            except Exception as exc:
                self.key_pool.report_failure(slot, exc)
                last_error = exc

        if last_error:
            raise last_error
        raise RuntimeError("Vision probe failed without specific error")

    @staticmethod
    def _extract_text_from_rest_response(body: dict[str, Any]) -> str:
        candidates = body.get("candidates", [])
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts", [])
        chunks = [part.get("text", "") for part in parts if part.get("text")]
        return "\n".join(chunks).strip()

    def key_pool_status(self) -> list[dict]:
        return self.key_pool.status()

    @staticmethod
    def _extract_text(response: Any) -> str:
        text = getattr(response, "text", None)
        if text:
            return text

        candidates = getattr(response, "candidates", None) or []
        if not candidates:
            raise ValueError("Gemini returned an empty response")

        parts = (
            getattr(candidates[0], "content", None)
            and getattr(candidates[0].content, "parts", None)
        ) or []

        chunked: list[str] = []
        for part in parts:
            value = getattr(part, "text", None)
            if value:
                chunked.append(value)

        return "\n".join(chunked)

    # ------------------------------------------------------------------
    # PCB crop-level methods (ported from pcb-analysis gemini_client)
    # ------------------------------------------------------------------

    def classify_crop(
        self,
        crop_raw: bytes,
        crop_highlighted: bytes,
        *,
        model: str = "gemini-3.1-flash-image-preview",
        mime_type: str = "image/png",
        temperature: float = 0.1,
    ) -> GeminiDefectResponse:
        """Classify a diff crop using raw + highlighted images.

        Uses the multi-key pool with retry logic.
        """
        def _op(client: genai.Client) -> GeminiDefectResponse:
            response = client.models.generate_content(
                model=model,
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
                    temperature=temperature,
                    response_mime_type="application/json",
                    response_schema=GeminiDefectResponse,
                ),
            )
            return GeminiDefectResponse.model_validate_json(response.text)

        try:
            return self._with_retry(_op)
        except Exception:
            return GeminiDefectResponse(
                defect_type="unknown",
                description="Classification failed due to an API error.",
                severity="medium",
            )

    def annotate_crop(
        self,
        crop_bytes: bytes,
        defect_type: str,
        severity: str,
        description: str,
        *,
        model: str = "gemini-3.1-flash-image-preview",
        mime_type: str = "image/png",
        temperature: float = 0.1,
    ) -> bytes | None:
        """Send a diff crop to Gemini and get back the crop with annotations.

        Returns annotated crop as image bytes, or None on failure.
        """
        prompt = ANNOTATE_CROP_PROMPT.format(
            defect_type=defect_type,
            severity=severity,
            description=description,
        )

        def _op(client: genai.Client) -> bytes | None:
            response = client.models.generate_content(
                model=model,
                contents=[
                    types.Content(
                        parts=[
                            types.Part.from_bytes(data=crop_bytes, mime_type=mime_type),
                            types.Part.from_text(text=prompt),
                        ]
                    )
                ],
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    response_modalities=["IMAGE", "TEXT"],
                ),
            )
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                    return part.inline_data.data
            return None

        try:
            return self._with_retry(_op)
        except Exception:
            return None

    @staticmethod
    def _try_parse_json_response(response: Any) -> dict[str, Any] | None:
        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, dict):
            return parsed
        if parsed is not None and hasattr(parsed, "model_dump"):
            dumped = parsed.model_dump()
            if isinstance(dumped, dict):
                return dumped

        text = GeminiService._extract_text(response)
        if not text:
            return None
        try:
            return safe_json_loads(text)
        except Exception:
            return None
