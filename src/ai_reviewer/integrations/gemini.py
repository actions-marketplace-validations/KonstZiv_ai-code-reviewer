"""Gemini integration for AI Code Reviewer (compatibility layer).

This module provides backward-compatible entry points that delegate to
:mod:`ai_reviewer.llm.gemini`. New code should use ``GeminiProvider``
directly.

.. deprecated::
    ``GeminiClient`` is deprecated and will be removed in v1.0.0 stable.
    Use :class:`ai_reviewer.llm.gemini.GeminiProvider` instead.
"""

from __future__ import annotations

import logging
import warnings
from typing import TYPE_CHECKING

from ai_reviewer.core.models import ReviewMetrics, ReviewResult
from ai_reviewer.integrations.prompts import SYSTEM_PROMPT, build_review_prompt
from ai_reviewer.llm.gemini import (
    DEFAULT_MODEL,
    DEFAULT_PRICING,
    GEMINI_PRICING,
    GeminiProvider,
    calculate_cost,
)

if TYPE_CHECKING:
    from pydantic import SecretStr

    from ai_reviewer.core.config import Settings
    from ai_reviewer.core.models import ReviewContext

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for interacting with Google Gemini API.

    .. deprecated::
        Use :class:`ai_reviewer.llm.gemini.GeminiProvider` instead.
        ``GeminiClient`` will be removed in v1.0.0 stable.

    Attributes:
        client: The underlying GeminiProvider.
        model_name: The name of the model to use.
    """

    def __init__(self, api_key: SecretStr, model_name: str = DEFAULT_MODEL) -> None:
        """Initialize Gemini client.

        Args:
            api_key: Google API key.
            model_name: Model name to use.
        """
        warnings.warn(
            "GeminiClient is deprecated and will be removed in v1.0.0 stable. "
            "Use ai_reviewer.llm.gemini.GeminiProvider instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self._provider = GeminiProvider(
            api_key=api_key.get_secret_value(),
            model_name=model_name,
        )
        self.model_name = model_name
        logger.debug("GeminiClient initialized with model %s (deprecated)", model_name)

    def generate_review(self, prompt: str) -> ReviewResult:
        """Generate a code review from the given prompt.

        Args:
            prompt: The user prompt containing code changes and context.

        Returns:
            Structured review result with metrics.
        """
        response = self._provider.generate(
            prompt,
            system_prompt=SYSTEM_PROMPT,
            response_schema=ReviewResult,
        )

        result = response.content
        assert isinstance(result, ReviewResult)  # guaranteed by response_schema

        metrics = ReviewMetrics(
            model_name=response.model_name,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            total_tokens=response.total_tokens,
            api_latency_ms=response.latency_ms,
            estimated_cost_usd=response.estimated_cost_usd,
        )

        return result.model_copy(update={"metrics": metrics})


def analyze_code_changes(context: ReviewContext, settings: Settings) -> ReviewResult:
    """Analyze code changes using Gemini.

    This function orchestrates the review process:
    1. Builds the prompt from the context.
    2. Initializes the Gemini provider.
    3. Generates the review.

    Args:
        context: The review context (MR, task, etc.).
        settings: Application settings.

    Returns:
        The review result with attached metrics.
    """
    logger.info("Starting code analysis for PR #%s", context.mr.number)

    # 1. Build prompt
    prompt = build_review_prompt(context, settings)
    logger.debug("Generated prompt of length %d chars", len(prompt))

    # 2. Initialize provider
    provider = GeminiProvider(
        api_key=settings.google_api_key.get_secret_value(),
        model_name=settings.gemini_model,
    )

    # 3. Generate review
    response = provider.generate(
        prompt,
        system_prompt=SYSTEM_PROMPT,
        response_schema=ReviewResult,
    )

    result = response.content
    assert isinstance(result, ReviewResult)  # guaranteed by response_schema

    # 4. Map LLMResponse metrics → ReviewMetrics for compatibility
    metrics = ReviewMetrics(
        model_name=response.model_name,
        prompt_tokens=response.prompt_tokens,
        completion_tokens=response.completion_tokens,
        total_tokens=response.total_tokens,
        api_latency_ms=response.latency_ms,
        estimated_cost_usd=response.estimated_cost_usd,
    )

    result = result.model_copy(update={"metrics": metrics})
    logger.info("Analysis complete. Found %d issues.", result.issue_count)

    return result


# Re-exports for backward compatibility
__all__ = [
    "DEFAULT_MODEL",
    "DEFAULT_PRICING",
    "GEMINI_PRICING",
    "GeminiClient",
    "analyze_code_changes",
    "calculate_cost",
]
