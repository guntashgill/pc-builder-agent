import os
import json
import logging
from typing import Dict, Any, Optional

from pydantic import ValidationError

from app.llm.client import LLMClient
from app.models import Constraints

logger = logging.getLogger(__name__)


class Interpreter:
    """Converts natural language user input into structured constraints"""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()
        self.system_prompt = self._load_prompt()

    def _load_prompt(self) -> str:
        prompt_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "llm", "prompts", "interpret.txt")
        )
        if not os.path.exists(prompt_path):
            raise FileNotFoundError(f"Interpreter prompt not found at: {prompt_path}")
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def extract_constraints(self, user_input: str) -> Constraints:
        """Convert natural language to structured Constraints"""
        if not self.validate_input(user_input):
            raise ValueError("User input is too short or empty")

        logger.info("Extracting constraints from user input")

        raw_response = self.llm.call_with_json(
            system_prompt=self.system_prompt,
            user_prompt=user_input,
            temperature=0.3,
        )

        if isinstance(raw_response, str):
            try:
                response_json = json.loads(raw_response)
            except json.JSONDecodeError:
                raise ValueError("LLM returned a non-JSON string response")
        elif isinstance(raw_response, dict):
            response_json = raw_response
        else:
            raise ValueError(f"Unexpected LLM response type: {type(raw_response)}")

        try:
            constraints = Constraints(**response_json)
            logger.info("Constraints extracted successfully: budget=%s workloads=%s",
                        getattr(constraints, "budget_usd", None),
                        getattr(constraints, "primary_workloads", None))
            return constraints
        except ValidationError as e:
            raise ValueError(f"Failed to validate extracted constraints: {e}")

    def validate_input(self, user_input: str) -> bool:
        if not user_input or len(user_input.strip()) < 10:
            return False
        return True