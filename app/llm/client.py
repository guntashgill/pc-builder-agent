import os
import json
import logging
from typing import Dict, Any, Optional, Union

from openai import OpenAI
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class LLMClient:
    """Wrapper for LLM API calls supporting OpenAI and Ollama"""

    def __init__(self, model: Optional[str] = None, provider: Optional[str] = None):
        self.provider = provider or os.getenv("LLM_PROVIDER", "openai")

        if self.provider == "ollama":
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            self.model = model or os.getenv("OLLAMA_MODEL", "llama3.1:8b")
            self.client = OpenAI(base_url=f"{base_url}/v1", api_key="ollama")
            logger.info(f"LLMClient initialized with Ollama: {self.model} at {base_url}")

        elif self.provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY in .env file")
            self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            self.client = OpenAI(api_key=api_key)
            logger.info(f"LLMClient initialized with OpenAI: {self.model}")

        else:
            raise ValueError(f"Unknown provider: {self.provider}. Use 'openai' or 'ollama'")

    def call_with_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Call LLM and parse JSON response"""
        try:
            params = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": temperature,
            }

            if max_tokens:
                params["max_tokens"] = max_tokens

            if self.provider == "openai":
                params["response_format"] = {"type": "json_object"}

            response = self.client.chat.completions.create(**params)
            content = response.choices[0].message.content

            if not content:
                raise ValueError("LLM returned empty response")

            return json.loads(content)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            raise ValueError(f"LLM response was not valid JSON: {e}")
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

    def call(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Call LLM and return raw text response"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("LLM returned empty response")

            return content

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise
