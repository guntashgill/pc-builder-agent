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
    """Wrapper for LLM API calls with structured JSON output support

    Supports both OpenAI and Ollama (local) providers
    """

    def __init__(self, model: Optional[str] = None, provider: Optional[str] = None):
        """
        Initialize LLM client

        Args:
            model: Model name (auto-detected from env if not provided)
            provider: "openai" or "ollama" (defaults to LLM_PROVIDER env var)
        """
        self.provider = provider or os.getenv("LLM_PROVIDER", "openai")

        if self.provider == "ollama":
            # Ollama setup (local, free)
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            self.model = model or os.getenv("OLLAMA_MODEL", "llama3.1:8b")
            self.client = OpenAI(
                base_url=f"{base_url}/v1",
                api_key="ollama"  # Ollama doesn't need a real API key
            )
            logger.info(f"LLMClient initialized with Ollama: {self.model} at {base_url}")

        elif self.provider == "openai":
            # OpenAI setup (cloud, paid)
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OpenAI API key not found. Set OPENAI_API_KEY in .env file"
                )
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
        """
        Call LLM and parse JSON response

        Args:
            system_prompt: System message defining the task
            user_prompt: User input to process
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens in response

        Returns:
            Parsed JSON response as dict

        Raises:
            ValueError: If response cannot be parsed as JSON
        """
        try:
            logger.debug(f"Calling LLM with temperature={temperature}")

            # Build request parameters
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

            # Only OpenAI supports response_format
            if self.provider == "openai":
                params["response_format"] = {"type": "json_object"}

            response = self.client.chat.completions.create(**params)
            content = response.choices[0].message.content

            if not content:
                raise ValueError("LLM returned empty response")

            # Parse JSON
            parsed = json.loads(content)

            logger.debug(f"Successfully parsed JSON response with {len(parsed)} keys")
            return parsed

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
        """
        Call LLM and return raw text response (for explanations, not structured data)

        Args:
            system_prompt: System message defining the task
            user_prompt: User input to process
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens in response

        Returns:
            Raw text response
        """
        try:
            logger.debug(f"Calling LLM (text mode) with temperature={temperature}")

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

            logger.debug(f"Successfully received text response ({len(content)} chars)")
            return content

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise
