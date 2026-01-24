"""Gemini integration for AI Code Reviewer.

This module provides a client for interacting with the Google Gemini API.
It handles sending prompts and parsing structured responses.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, NoReturn

from google import genai
from google.genai import types
from pydantic import ValidationError

from ai_reviewer.core.models import ReviewMetrics, ReviewResult
from ai_reviewer.integrations.prompts import SYSTEM_PROMPT, build_review_prompt

if TYPE_CHECKING:
    from pydantic import SecretStr

    from ai_reviewer.core.config import Settings
    from ai_reviewer.core.models import ReviewContext

logger = logging.getLogger(__name__)

# Gemini pricing per 1M tokens (as of January 2026)
# https://ai.google.dev/pricing
GEMINI_PRICING: dict[str, dict[str, float]] = {
    # Gemini 2.5 Flash
    "gemini-2.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-2.5-flash-preview-05-20": {"input": 0.075, "output": 0.30},
    # Gemini 2.0 Flash
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
    "gemini-2.0-flash-001": {"input": 0.10, "output": 0.40},
    # Gemini 1.5 Flash
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-1.5-flash-latest": {"input": 0.075, "output": 0.30},
    # Gemini 1.5 Pro
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
    "gemini-1.5-pro-latest": {"input": 1.25, "output": 5.00},
    # Gemini Pro (legacy)
    "gemini-pro": {"input": 0.50, "output": 1.50},
}

# Default pricing for unknown models (conservative estimate)
DEFAULT_PRICING = {"input": 1.00, "output": 3.00}

# Default model to use when not specified
DEFAULT_MODEL = "gemini-2.5-flash"


def calculate_cost(
    model_name: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> float:
    """Calculate estimated cost for Gemini API usage.

    Args:
        model_name: The model name used for the request.
        prompt_tokens: Number of input tokens.
        completion_tokens: Number of output tokens.

    Returns:
        Estimated cost in USD.
    """
    pricing = GEMINI_PRICING.get(model_name, DEFAULT_PRICING)
    input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
    output_cost = (completion_tokens / 1_000_000) * pricing["output"]
    return input_cost + output_cost


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

    def __init__(self, api_key: SecretStr, model_name: str = DEFAULT_MODEL) -> None:
        """Initialize Gemini client.

        Args:
            api_key: Google API key.
            model_name: Model name to use (default: gemini-2.5-flash).
        """
        self.client = genai.Client(api_key=api_key.get_secret_value())
        self.model_name = model_name
        logger.debug("Gemini client initialized with model %s", model_name)

    def generate_review(self, prompt: str) -> ReviewResult:
        """Generate a code review from the given prompt.

        Args:
            prompt: The user prompt containing code changes and context.

        Returns:
            Structured review result with metrics.

        Raises:
            Exception: If API call fails or response parsing fails.
        """
        try:
            start_time = time.perf_counter()

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

            elapsed_ms = int((time.perf_counter() - start_time) * 1000)

            if not response.parsed:
                _raise_parsing_error()

            # Extract token usage from response metadata
            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0

            if response.usage_metadata:
                prompt_tokens = response.usage_metadata.prompt_token_count or 0
                completion_tokens = response.usage_metadata.candidates_token_count or 0
                total_tokens = response.usage_metadata.total_token_count or 0

            # Calculate estimated cost
            estimated_cost = calculate_cost(self.model_name, prompt_tokens, completion_tokens)

            # Create metrics
            metrics = ReviewMetrics(
                model_name=self.model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                api_latency_ms=elapsed_ms,
                estimated_cost_usd=estimated_cost,
            )

            logger.debug(
                "Gemini API call: %d tokens (%d in, %d out), %dms, $%.4f",
                total_tokens,
                prompt_tokens,
                completion_tokens,
                elapsed_ms,
                estimated_cost,
            )

            # The SDK automatically parses the JSON into the Pydantic model
            # when response_schema is provided with a Pydantic class.
            parsed = response.parsed

            # Attach metrics to result using model_copy for efficiency
            if isinstance(parsed, ReviewResult):
                return parsed.model_copy(update={"metrics": metrics})

            # Fallback for dict-like responses from SDK
            result_data = parsed if isinstance(parsed, dict) else dict(parsed)  # type: ignore[arg-type]
            result_data["metrics"] = metrics
            return ReviewResult.model_validate(result_data)

        except ValidationError:
            logger.exception("Failed to validate Gemini response structure")
            raise
        except Exception:
            logger.exception("Gemini API call failed")
            raise


def analyze_code_changes(context: ReviewContext, settings: Settings) -> ReviewResult:
    """Analyze code changes using Gemini.

    This function orchestrates the review process:
    1. Builds the prompt from the context.
    2. Initializes the Gemini client.
    3. Generates the review.

    Args:
        context: The review context (MR, task, etc.).
        settings: Application settings.

    Returns:
        The review result.
    """
    logger.info("Starting code analysis for PR #%s", context.mr.number)

    # 1. Build prompt
    prompt = build_review_prompt(context, settings)
    logger.debug("Generated prompt of length %d chars", len(prompt))

    # 2. Initialize client
    client = GeminiClient(
        api_key=settings.google_api_key,
        model_name=settings.gemini_model,
    )

    # 3. Generate review
    result = client.generate_review(prompt)
    logger.info("Analysis complete. Found %d issues.", result.issue_count)

    return result
