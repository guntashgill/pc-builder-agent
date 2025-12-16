import os
import json
import logging
from typing import Optional

from pydantic import ValidationError

from app.llm.client import LLMClient
from app.models import Constraints, PCBuild

logger = logging.getLogger(__name__)


class Planner:
    """Generates PC build configurations from structured constraints"""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()
        self.system_prompt = self._load_prompt()

    def _load_prompt(self) -> str:
        prompt_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "llm", "prompts", "plan.txt")
        )
        if not os.path.exists(prompt_path):
            raise FileNotFoundError(f"Planner prompt not found at: {prompt_path}")
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def generate_build(
        self,
        constraints: Constraints,
        previous_build: Optional[PCBuild] = None,
        feedback: Optional[str] = None
    ) -> PCBuild:
        """Generate PC build from constraints (supports revision mode)"""
        logger.info("Generating PC build for budget=$%d, workloads=%s",
                    constraints.budget_usd,
                    constraints.primary_workloads)

        user_prompt = self._build_prompt(constraints, previous_build, feedback)

        raw_response = self.llm.call_with_json(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            temperature=0.4,
        )

        if isinstance(raw_response, str):
            try:
                response_json = json.loads(raw_response)
            except json.JSONDecodeError:
                raise ValueError("LLM returned non-JSON response")
        elif isinstance(raw_response, dict):
            response_json = raw_response
        else:
            raise ValueError(f"Unexpected response type: {type(raw_response)}")

        try:
            build = PCBuild(**response_json)
            logger.info("Build generated successfully: cost=$%d, CPU=%s, GPU=%s",
                        build.estimated_cost_usd,
                        build.cpu.model,
                        build.gpu.model)
            return build
        except ValidationError as e:
            logger.error("Failed to validate build: %s", e)
            raise ValueError(f"Build validation failed: {e}")

    def _build_prompt(
        self,
        constraints: Constraints,
        previous_build: Optional[PCBuild] = None,
        feedback: Optional[str] = None
    ) -> str:

        if previous_build and feedback:
            # Revision mode
            prompt = f"""# Revision Request

The previous build failed validation. Please revise it based on the feedback below.

## Original Constraints
{constraints.model_dump_json(indent=2)}

## Previous Build
{previous_build.model_dump_json(indent=2)}

## Validation Feedback
{feedback}

## Instructions
Revise ONLY the components mentioned in the feedback. Keep all other valid components unchanged.
Return the complete revised build as JSON.
"""
        else:
            # Initial build generation
            prompt = f"""# Build Request

Generate a complete PC build based on these constraints:

{constraints.model_dump_json(indent=2)}

Return a complete build specification as JSON.
"""

        return prompt
