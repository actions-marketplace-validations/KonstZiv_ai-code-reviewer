"""Language detection utilities for AI Code Reviewer.

This module implements the "Proximity Rule" algorithm for detecting
the preferred response language from PR/MR context.

The algorithm prioritizes recent, substantial text from:
1. Comments (most recent first)
2. MR/PR description
3. Linked task description

Language detection is delegated to the LLM during the review process.
This module collects text samples for the LLM to analyze.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai_reviewer.core.config import LanguageMode

if TYPE_CHECKING:
    from ai_reviewer.core.config import Settings
    from ai_reviewer.core.models import ReviewContext

# Minimum word count for a text to be considered for language detection
MIN_WORDS_FOR_DETECTION = 8

# Default language when detection fails or is not possible
DEFAULT_LANGUAGE = "en"

MAX_SAMPLE_LENGTH = 500


def _count_words(text: str) -> int:
    """Count words in a text string.

    Args:
        text: The text to count words in.

    Returns:
        Number of words in the text.
    """
    return len(text.split())


def _is_substantial_text(text: str) -> bool:
    """Check if text is substantial enough for language detection.

    Args:
        text: The text to check.

    Returns:
        True if the text has enough words for reliable detection.
    """
    return _count_words(text) >= MIN_WORDS_FOR_DETECTION


def collect_text_samples(context: ReviewContext) -> tuple[str, ...]:
    """Collect text samples from context for language detection.

    Implements the "Proximity Rule" - collects texts in order of recency:
    1. Comments (most recent first, filtered for substantial length)
    2. MR description (if substantial)
    3. Task description (if substantial)

    Args:
        context: The review context containing MR and optional task.

    Returns:
        Tuple of text samples ordered by recency (most recent first).
    """
    samples: list[str] = []

    # 1. Collect substantial comments (most recent first)
    # Comments are already ordered, we reverse to get most recent first
    for comment in reversed(context.mr.comments):
        if _is_substantial_text(comment.body):
            samples.append(comment.body)

    # 2. MR description
    if context.mr.description and _is_substantial_text(context.mr.description):
        samples.append(context.mr.description)

    # 3. Task description (if linked)
    if context.task and context.task.description and _is_substantial_text(context.task.description):
        samples.append(context.task.description)

    return tuple(samples)


def get_language_for_review(context: ReviewContext, settings: Settings) -> str:
    """Determine the language to use for the review response.

    Applies the language mode logic:
    - FIXED: Always use the configured LANGUAGE setting
    - ADAPTIVE: Use text samples for LLM to detect, or fallback to LANGUAGE

    Args:
        context: The review context containing MR and optional task.
        settings: Application settings with language configuration.

    Returns:
        ISO 639 language code to use for the review.
    """
    if settings.language_mode == LanguageMode.FIXED:
        return settings.language

    # ADAPTIVE mode: collect samples for LLM detection
    # The actual detection happens in the LLM prompt
    # Here we just determine if we have enough context
    samples = collect_text_samples(context)

    if not samples:
        # No substantial text found, use configured language
        return settings.language

    # Return None to signal that LLM should detect from context
    # The prompt builder will handle this case
    # For now, we return the configured language as a fallback hint
    return settings.language


def build_language_instruction(
    context: ReviewContext,
    settings: Settings,
) -> str:
    """Build language instruction for the LLM prompt.

    Args:
        context: The review context.
        settings: Application settings.

    Returns:
        Instruction string for the LLM about response language.
    """
    if settings.language_mode == LanguageMode.FIXED:
        return (
            f"IMPORTANT: Respond in {settings.language} language. "
            f"All review comments and summaries must be written in {settings.language}."
        )

    # ADAPTIVE mode
    samples = collect_text_samples(context)

    if samples:
        # Take the most recent substantial text for context
        sample_preview = (
            samples[0][:500] + "..." if len(samples[0]) > MAX_SAMPLE_LENGTH else samples[0]
        )
        return (
            "IMPORTANT: Detect the language from the PR context and respond in the same language. "
            "Analyze the PR description, task description, and comments to determine the "
            "primary language. "
            f"If you cannot determine the language, use {settings.language} as fallback.\n"
            f"Context sample for language detection:\n```\n{sample_preview}\n```"
        )

    # No substantial context, use configured language
    return (
        f"IMPORTANT: Respond in {settings.language} language. "
        f"All review comments and summaries must be written in {settings.language}."
    )


__all__ = [
    "DEFAULT_LANGUAGE",
    "MIN_WORDS_FOR_DETECTION",
    "build_language_instruction",
    "collect_text_samples",
    "get_language_for_review",
]
