from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .agents import AgentRunner
from .config import Settings
from .diff_engine import DiffRegion, compute_diff
from .gemini_client import GeminiService
from .image_annotation import draw_boxes_on_image
from .schemas import (
    AgentTrace,
    BoundingBox,
    FinalOutput,
    OrchestrationRequest,
    OrchestrationResponse,
)
from .spec_parser import resolve_spec_excerpt
from .utils import load_image_bytes


class OrchestrationEngine:
    def __init__(
        self,
        *,
        settings: Settings,
        gemini_service: GeminiService,
        available_models_cache: list | None = None,
    ) -> None:
        self.settings = settings
        self.gemini = gemini_service
        self._available_models_cache = available_models_cache
        self.root_dir = Path(__file__).resolve().parents[1]

    def list_models(self):
        self._available_models_cache = self.gemini.list_generate_models()
        return self._available_models_cache

    def _pick_model(self, requested_model: str | None) -> str:
        try:
            available = self._available_models_cache or self.list_models()
        except Exception:
            normalized_requested = self.gemini.resolve_model_name(requested_model)
            if normalized_requested:
                return normalized_requested
            if self.settings.default_model:
                resolved_default = self.gemini.resolve_model_name(self.settings.default_model)
                return resolved_default or self.settings.default_model
            return "gemini-3.1-flash-image-preview"

        if requested_model:
            normalized_requested = self.gemini.resolve_model_name(requested_model)
            names = {m.name for m in available}
            if normalized_requested not in names:
                raise ValueError(f"Requested model '{requested_model}' is not available for this API key")
            return normalized_requested

        return self.gemini.pick_recommended_model(
            available,
            default_model=self.settings.default_model,
        )

    def run(self, request: OrchestrationRequest) -> OrchestrationResponse:
        started_at = datetime.now(tz=UTC)
        run_id = str(uuid.uuid4())

        candidate_models = self._candidate_models(request.options.model)
        last_error: Exception | None = None

        for model in candidate_models:
            try:
                return self._run_single_model(
                    request=request,
                    model=model,
                    run_id=run_id,
                    started_at=started_at,
                )
            except Exception as exc:
                last_error = exc
                if request.options.model:
                    raise

        if last_error:
            raise last_error
        raise RuntimeError("Orchestration failed without detailed error")

    def _candidate_models(self, requested_model: str | None) -> list[str]:
        primary = self._pick_model(requested_model)
        # Enforce latest-recommended model only.
        # If that single model fails, surface error instead of silently falling back to older families.
        return [primary]

    def _run_single_model(
        self,
        *,
        request: OrchestrationRequest,
        model: str,
        run_id: str,
        started_at: datetime,
    ) -> OrchestrationResponse:
        design_image_bytes = load_image_bytes(request.input.design_image, self.root_dir)
        tested_image_bytes = load_image_bytes(request.input.tested_image, self.root_dir)

        # Run OpenCV diff to get highlighted crop regions
        diff_regions: list[DiffRegion] = []
        try:
            diff_regions = compute_diff(design_image_bytes, tested_image_bytes)
        except (ValueError, Exception):
            pass

        # Derive heuristic bbox from the largest diff region
        heuristic_bbox: dict | None = None
        if diff_regions:
            largest = max(diff_regions, key=lambda r: r.area)
            bb = largest.bounding_box
            confidence = min(0.99, max(0.1, largest.area / 10000.0 + 0.25))
            heuristic_bbox = {
                "label": "diff_hotspot",
                "x1": bb.x_min,
                "y1": bb.y_min,
                "x2": bb.x_max,
                "y2": bb.y_max,
                "confidence": round(confidence, 3),
            }
        resolved_spec_excerpt = resolve_spec_excerpt(
            spec_excerpt=request.input.spec_excerpt,
            spec_document_path=request.input.spec_document_path,
            error_log=request.input.error_log,
            root_dir=self.root_dir,
        )

        runner = AgentRunner(
            gemini=self.gemini,
            model=model,
            temperature=self.settings.default_temperature,
            max_output_tokens=self.settings.max_output_tokens,
            background_context=request.input.background_context
            or self.settings.context_background_path.read_text(encoding="utf-8"),
            todo_context=request.input.todo_context
            or self.settings.context_todo_path.read_text(encoding="utf-8"),
            example_context=request.input.example_context
            or self.settings.context_example_path.read_text(encoding="utf-8"),
        )

        traces: list[AgentTrace] = []

        # Step 1: Symptom Analyzer — error log → fault candidates
        spec_focus_image_parts = [
            (load_image_bytes(image_input, self.root_dir), image_input.mime_type)
            for image_input in request.input.spec_image_parts
        ]
        symptom_result = runner.run_symptom_agent(
            request.input.error_log,
            spec_focus_plan=request.input.spec_focus_plan,
            spec_image_parts=spec_focus_image_parts,
        )
        traces.append(
            AgentTrace(
                agent_id="agent_1",
                agent_name="Symptom Analyzer",
                handoff_to="agent_2a,agent_2b",
                handoff_message=symptom_result.get("handoff_message"),
                output=symptom_result
                if request.options.include_raw_agent_payloads
                else {
                    "error_interpretation": symptom_result.get("error_interpretation"),
                    "suspect_part_count": len(symptom_result.get("suspect_parts", [])),
                    "spec_focus_sections": symptom_result.get("spec_navigation", {}).get("top_focus_sections", []),
                    "toc_sections": symptom_result.get("spec_navigation", {}).get("toc_sections", []),
                },
            )
        )

        # Step 2A + 2B: Spec precheck and CAD mapping run in parallel.
        with ThreadPoolExecutor(max_workers=2) as pool:
            spec_future = pool.submit(
                runner.run_spec_precheck_agent,
                resolved_spec_excerpt,
                symptom_result,
            )
            design_future = pool.submit(
                runner.run_design_agent,
                symptom_result,
                heuristic_bbox,
                request.input.design_reference_text,
                (design_image_bytes, request.input.design_image.mime_type),
            )
            spec_precheck_result = spec_future.result()
            design_result = design_future.result()

        traces.append(
            AgentTrace(
                agent_id="agent_2a",
                agent_name="Spec Precheck (Parallel)",
                handoff_to="agent_3",
                handoff_message=spec_precheck_result.get("handoff_message"),
                output=spec_precheck_result
                if request.options.include_raw_agent_payloads
                else {
                    "spec_watch_count": len(spec_precheck_result.get("spec_watchlist", [])),
                    "spec_risk_summary": spec_precheck_result.get("spec_risk_summary"),
                },
            )
        )
        traces.append(
            AgentTrace(
                agent_id="agent_2b",
                agent_name="CAD Mapper (Parallel)",
                handoff_to="agent_3",
                handoff_message=design_result.get("handoff_message"),
                output=design_result
                if request.options.include_raw_agent_payloads
                else {
                    "mapped_part_count": len(design_result.get("cad_mappings", [])),
                },
            )
        )

        # Step 3: Physical Vision — defect verification
        physical_result = runner.run_physical_agent(
            symptom_result=symptom_result,
            spec_precheck_result=spec_precheck_result,
            design_result=design_result,
            heuristic_bbox=heuristic_bbox,
            tested_image=(tested_image_bytes, request.input.tested_image.mime_type),
        )
        traces.append(
            AgentTrace(
                agent_id="agent_3",
                agent_name="Physical Vision",
                handoff_to="agent_4",
                handoff_message=physical_result.get("handoff_message"),
                output=physical_result
                if request.options.include_raw_agent_payloads
                else {
                    "verified_defect_count": len(physical_result.get("defect_verification", [])),
                    "root_cause_candidate": physical_result.get("root_cause_candidate"),
                },
            )
        )

        # Step 4: Spec Resolver — spec-based resolution
        spec_result = runner.run_spec_final_agent(
            spec_excerpt=resolved_spec_excerpt,
            symptom_result=symptom_result,
            spec_precheck_result=spec_precheck_result,
            design_result=design_result,
            physical_result=physical_result,
        )
        traces.append(
            AgentTrace(
                agent_id="agent_4",
                agent_name="Spec Resolver",
                handoff_to=None,
                handoff_message=None,
                output=spec_result
                if request.options.include_raw_agent_payloads
                else {
                    "spec_check_count": len(spec_result.get("spec_checks", [])),
                    "final_root_cause": spec_result.get("final_root_cause"),
                },
            )
        )

        output = self._build_final_output(spec_result, physical_result, heuristic_bbox)

        # Render annotated tested board image with highlighted diff crops + labels
        annotated_b64: str | None = None
        if output.bounding_boxes:
            try:
                annotated_b64 = draw_boxes_on_image(
                    tested_image_bytes,
                    output.bounding_boxes,
                    diff_regions=diff_regions or None,
                )
            except Exception:
                pass

        ended_at = datetime.now(tz=UTC)
        return OrchestrationResponse(
            run_id=run_id,
            model_used=model,
            started_at=started_at,
            ended_at=ended_at,
            input={
                "error_log": request.input.error_log,
                "spec_excerpt": resolved_spec_excerpt,
                "spec_document_path": request.input.spec_document_path,
                "spec_focus_plan": request.input.spec_focus_plan,
                "spec_image_count": len(request.input.spec_image_parts),
                "design_image": self._input_image_meta(request.input.design_image),
                "tested_image": self._input_image_meta(request.input.tested_image),
                "heuristic_diff_bbox": heuristic_bbox,
            },
            output=output,
            agent_trace=traces,
            annotated_tested_image=annotated_b64,
        )

    @staticmethod
    def _input_image_meta(image) -> dict[str, str]:
        return {
            "mime_type": image.mime_type,
            "source": "base64" if image.base64_data else image.file_path or "unknown",
        }

    @staticmethod
    def _build_final_output(
        spec_result: dict[str, Any],
        physical_result: dict[str, Any],
        heuristic_bbox: dict | None,
    ) -> FinalOutput:
        boxes: list[BoundingBox] = []
        for finding in physical_result.get("defect_verification", []):
            bbox = finding.get("bbox", {})
            boxes.append(
                BoundingBox(
                    label=str(finding.get("defect_type", finding.get("part_name", "defect"))),
                    x1=int(bbox.get("x1", 0)),
                    y1=int(bbox.get("y1", 0)),
                    x2=int(bbox.get("x2", 0)),
                    y2=int(bbox.get("y2", 0)),
                    confidence=float(max(0.0, min(1.0, finding.get("confidence", 0.0)))),
                )
            )

        if not boxes and heuristic_bbox:
            boxes.append(
                BoundingBox(
                    label=str(heuristic_bbox.get("label", "diff_hotspot")),
                    x1=int(heuristic_bbox.get("x1", 0)),
                    y1=int(heuristic_bbox.get("y1", 0)),
                    x2=int(heuristic_bbox.get("x2", 0)),
                    y2=int(heuristic_bbox.get("y2", 0)),
                    confidence=float(max(0.0, min(1.0, heuristic_bbox.get("confidence", 0.3)))),
                )
            )

        return FinalOutput(
            root_cause=str(
                spec_result.get(
                    "final_root_cause",
                    physical_result.get("root_cause_candidate", "No root cause provided"),
                )
            ),
            impact=str(physical_result.get("impact", "No impact provided")),
            resolution=[str(item) for item in spec_result.get("final_resolution", ["No action provided"])],
            confidence=float(
                max(
                    0.0,
                    min(
                        1.0,
                        spec_result.get(
                            "final_confidence",
                            physical_result.get("overall_confidence", 0.0),
                        ),
                    ),
                )
            ),
            bounding_boxes=boxes,
        )
