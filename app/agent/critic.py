import os
import json
import logging
from typing import Dict, Any

from app.llm.client import LLMClient
from app.models import Constraints, PCBuild, ValidationResult

logger = logging.getLogger(__name__)


class Critic:
    """Analyzes validation failures and generates revision instructions"""

    def __init__(self, llm_client: LLMClient = None):
        self.llm = llm_client or LLMClient()
        self.system_prompt = self._load_prompt()

    def _load_prompt(self) -> str:
        prompt_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "llm", "prompts", "critique.txt")
        )
        if not os.path.exists(prompt_path):
            raise FileNotFoundError(f"Critique prompt not found at: {prompt_path}")
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def analyze_failure(
        self,
        build: PCBuild,
        constraints: Constraints,
        validation_result: ValidationResult
    ) -> Dict[str, Any]:
        """Analyze build validation failure and generate revision instructions"""
        logger.info("Analyzing build failure: %d errors, %d warnings",
                    len(validation_result.errors),
                    len(validation_result.warnings))

        user_prompt = self._build_analysis_prompt(build, constraints, validation_result)

        try:
            critique = self.llm.call_with_json(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                temperature=0.3,
            )

            logger.info("Critique generated: %d critical issues, %d warnings",
                        len(critique.get("critical_issues", [])),
                        len(critique.get("warnings", [])))

            return critique

        except Exception as e:
            logger.error(f"Failed to generate critique: {e}")
            raise ValueError(f"Critique generation failed: {e}")

    def _build_analysis_prompt(
        self,
        build: PCBuild,
        constraints: Constraints,
        validation_result: ValidationResult
    ) -> str:

        # Format validation errors
        errors_text = "\n".join([
            f"- {err.severity.upper()}: {err.message} (component: {err.component or 'general'})"
            for err in validation_result.errors
        ])

        warnings_text = "\n".join([
            f"- {warn.severity.upper()}: {warn.message} (component: {warn.component or 'general'})"
            for warn in validation_result.warnings
        ]) if validation_result.warnings else "None"

        prompt = f"""# Build Validation Failure Analysis

## Original User Constraints
{constraints.model_dump_json(indent=2)}

## Current Build (FAILED)
{build.model_dump_json(indent=2)}

## Validation Errors
{errors_text}

## Validation Warnings
{warnings_text}

## Your Task
Analyze the validation failures and provide specific, actionable revision instructions as JSON.

Focus on:
1. **Critical errors first** - These MUST be fixed
2. **Root causes** - Why did this fail?
3. **Minimal changes** - Only change what's necessary
4. **Budget compliance** - Stay within ${constraints.budget_usd}

Return your analysis as JSON with critical_issues, warnings, recommended_changes, and preserve_components.
"""

        return prompt

    def format_feedback_for_planner(self, critique: Dict[str, Any]) -> str:
        """
        Convert critique into human-readable feedback for the planner

        Args:
            critique: Critique dict from analyze_failure

        Returns:
            Formatted string with revision instructions
        """
        feedback_parts = []

        # Critical issues
        if critique.get("critical_issues"):
            feedback_parts.append("CRITICAL ISSUES:")
            for issue in critique["critical_issues"]:
                feedback_parts.append(
                    f"  - {issue['component'].upper()}: {issue['issue']}\n"
                    f"    FIX: {issue['fix']}"
                )

        # Warnings
        if critique.get("warnings"):
            feedback_parts.append("\nWARNINGS:")
            for warning in critique["warnings"]:
                feedback_parts.append(
                    f"  - {warning['component'].upper()}: {warning['issue']}\n"
                    f"    SUGGESTION: {warning['fix']}"
                )

        # Recommended changes
        if critique.get("recommended_changes"):
            feedback_parts.append("\nRECOMMENDED CHANGES:")
            for component, changes in critique["recommended_changes"].items():
                feedback_parts.append(f"  {component.upper()}:")
                for field, value in changes.items():
                    if field != "reason":
                        feedback_parts.append(f"    - {field}: {value}")
                if "reason" in changes:
                    feedback_parts.append(f"    Reason: {changes['reason']}")

        # Preserve list
        if critique.get("preserve_components"):
            feedback_parts.append(
                f"\nDO NOT CHANGE: {', '.join(critique['preserve_components'])}"
            )

        return "\n".join(feedback_parts)
