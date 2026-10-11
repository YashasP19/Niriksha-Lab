from __future__ import annotations

from dataclasses import dataclass

from .gemini_client import GeminiService
from .prompts import (
    DESIGN_SCHEMA,
    PHYSICAL_SCHEMA,
    SPEC_PRECHECK_SCHEMA,
    SPEC_FINAL_SCHEMA,
    SYMPTOM_SCHEMA,
    base_context,
    design_prompt,
    physical_prompt,
    spec_precheck_prompt,
    spec_final_prompt,
    symptom_prompt,
)


@dataclass
class AgentRunner:
    gemini: GeminiService
    model: str
    temperature: float
    max_output_tokens: int
    background_context: str
    todo_context: str
    example_context: str

    def _context(self) -> str:
        return base_context(
            background=self.background_context,
            todo=self.todo_context,
            example=self.example_context,
        )

    def run_symptom_agent(
        self,
        error_log: str,
        *,
        spec_focus_plan: str | None = None,
        spec_image_parts: list[tuple[bytes, str]] | None = None,
    ) -> dict:
        prompt = symptom_prompt(
            context=self._context(),
            error_log=error_log,
            spec_focus_plan=spec_focus_plan,
        )
        return self.gemini.generate_json(
            model=self.model,
            prompt=prompt,
            response_schema=SYMPTOM_SCHEMA,
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens,
            image_parts=spec_image_parts,
        )

    def run_spec_precheck_agent(self, spec_excerpt: str, symptom_result: dict) -> dict:
        prompt = spec_precheck_prompt(
            context=self._context(),
            spec_excerpt=spec_excerpt,
            symptom_result=symptom_result,
        )
        return self.gemini.generate_json(
            model=self.model,
            prompt=prompt,
            response_schema=SPEC_PRECHECK_SCHEMA,
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens,
        )

    def run_design_agent(
        self,
        symptom_result: dict,
        heuristic_bbox: dict | None,
        design_reference_text: str | None,
        design_image: tuple[bytes, str],
    ) -> dict:
        prompt = design_prompt(
            context=self._context(),
            symptom_result=symptom_result,
            heuristic_bbox=heuristic_bbox,
            design_reference_text=design_reference_text,
        )
        return self.gemini.generate_json(
            model=self.model,
            prompt=prompt,
            response_schema=DESIGN_SCHEMA,
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens,
            image_parts=[design_image],
        )

    def run_physical_agent(
        self,
        symptom_result: dict,
        spec_precheck_result: dict,
        design_result: dict,
        heuristic_bbox: dict | None,
        tested_image: tuple[bytes, str],
    ) -> dict:
        prompt = physical_prompt(
            context=self._context(),
            symptom_result=symptom_result,
            spec_precheck_result=spec_precheck_result,
            design_result=design_result,
            heuristic_bbox=heuristic_bbox,
        )
        return self.gemini.generate_json(
            model=self.model,
            prompt=prompt,
            response_schema=PHYSICAL_SCHEMA,
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens,
            image_parts=[tested_image],
        )

    def run_spec_final_agent(
        self,
        spec_excerpt: str,
        symptom_result: dict,
        spec_precheck_result: dict,
        design_result: dict,
        physical_result: dict,
    ) -> dict:
        prompt = spec_final_prompt(
            context=self._context(),
            spec_excerpt=spec_excerpt,
            symptom_result=symptom_result,
            spec_precheck_result=spec_precheck_result,
            design_result=design_result,
            physical_result=physical_result,
        )
        return self.gemini.generate_json(
            model=self.model,
            prompt=prompt,
            response_schema=SPEC_FINAL_SCHEMA,
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens,
        )
