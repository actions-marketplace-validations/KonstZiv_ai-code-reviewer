"""Gemini integration for AI Code Reviewer.

This module provides a client for interacting with the Google Gemini API.
It handles sending prompts and parsing structured responses.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, NoReturn

from google import genai
from google.genai import types
from pydantic import ValidationError

from ai_reviewer.core.models import ReviewResult
from ai_reviewer.integrations.prompts import SYSTEM_PROMPT

if TYPE_CHECKING:
    from pydantic import SecretStr

logger = logging.getLogger(__name__)

_PARSING_ERROR_MSG = "Gemini response could not be parsed into ReviewResult"


def _raise_parsing_error() -> NoReturn:
    """Raise a ValueError when parsing fails.

    This helper function satisfies linter rules about abstracting raises
    and avoiding string literals in exceptions.
    """
    raise ValueError(_PARSING_ERROR_MSG)


class GeminiClient:
    """Client for interacting with Google Gemini API.

    Attributes:
        client: The Google GenAI client.
        model_name: The name of the model to use.
    """

    def __init__(self, api_key: SecretStr, model_name: str = "gemini-2.5-flash") -> None:
        """Initialize Gemini client.

        Args:
            api_key: Google API key.
            model_name: Model name to use.
        """
        self.client = genai.Client(api_key=api_key.get_secret_value())
        self.model_name = model_name
        logger.debug("Gemini client initialized with model %s", model_name)

    def generate_review(self, prompt: str) -> ReviewResult:
        """Generate a code review from the given prompt.

        Args:
            prompt: The user prompt containing code changes and context.

        Returns:
            Structured review result.

        Raises:
            Exception: If API call fails or response parsing fails.
        """
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.0,  # Deterministic output
                    response_mime_type="application/json",
                    response_schema=ReviewResult,  # Pydantic model for schema enforcement
                ),
            )

            if not response.parsed:
                _raise_parsing_error()

            # The SDK automatically parses the JSON into the Pydantic model
            # if response_schema is provided with a Pydantic class.
            result = response.parsed

            if isinstance(result, ReviewResult):
                return result

            # For safety with current SDK behavior:
            if hasattr(result, "model_dump"):
                # It's likely a Pydantic model already
                return result  # type: ignore[return-value]

            # Fallback for dict-like objects
            return ReviewResult.model_validate(result)

        except ValidationError:
            logger.exception("Failed to validate Gemini response structure")
            raise
        except Exception:
            logger.exception("Gemini API call failed")
            raise
