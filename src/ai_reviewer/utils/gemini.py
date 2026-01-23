"""Gemini API utilities and runtime validation using Google GenAI SDK.

This module provides:
- Runtime validation of Gemini API setup (key validity, model availability)
- Model listing and discovery
- Structured validation results for CLI/logging

This module uses the modern `google-genai` SDK (v1.59+).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum

from google import genai
from pydantic import SecretStr  # noqa: TC002

logger = logging.getLogger(__name__)

# Limits for model list display in error messages
_ERROR_MODEL_LIST_LIMIT = 10
_FORMAT_MODEL_LIST_LIMIT = 15


class ValidationStatus(str, Enum):
    """Status of Gemini setup validation."""

    SUCCESS = "success"
    INVALID_API_KEY = "invalid_api_key"
    MODEL_NOT_FOUND = "model_not_found"
    NETWORK_ERROR = "network_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass(frozen=True)
class GeminiModelInfo:
    """Information about a Gemini model.

    Attributes:
        name: Full model name (e.g., 'models/gemini-2.5-flash').
        display_name: Human-readable name.
        description: Model description.
        input_token_limit: Maximum input tokens.
        output_token_limit: Maximum output tokens.
    """

    name: str
    display_name: str
    description: str
    input_token_limit: int
    output_token_limit: int

    @property
    def short_name(self) -> str:
        """Get short model name without 'models/' prefix."""
        return self.name.removeprefix("models/")


@dataclass(frozen=True)
class GeminiValidationResult:
    """Result of Gemini setup validation.

    Attributes:
        status: Validation status code.
        message: Human-readable status message.
        model: Validated model name (if successful).
        available_models: List of available models (for diagnostics).
        error_details: Technical error details (for logging).
    """

    status: ValidationStatus
    message: str
    model: str | None = None
    available_models: tuple[str, ...] = field(default_factory=tuple)
    error_details: str | None = None

    @property
    def is_success(self) -> bool:
        """Check if validation was successful."""
        return self.status == ValidationStatus.SUCCESS

    @property
    def is_error(self) -> bool:
        """Check if validation failed with an error."""
        return self.status in (
            ValidationStatus.INVALID_API_KEY,
            ValidationStatus.MODEL_NOT_FOUND,
            ValidationStatus.UNKNOWN_ERROR,
        )

    @property
    def is_warning(self) -> bool:
        """Check if validation has a warning (e.g., network issue)."""
        return self.status == ValidationStatus.NETWORK_ERROR


def list_models(api_key: SecretStr) -> list[GeminiModelInfo]:
    """List available Gemini models using the new GenAI SDK.

    Args:
        api_key: Google API key.

    Returns:
        List of available Gemini models.

    Raises:
        Exception: If API call fails.
    """
    client = genai.Client(api_key=api_key.get_secret_value())
    models: list[GeminiModelInfo] = []

    # The new SDK returns an iterator of Model objects
    # We iterate and filter for models that support content generation
    for model in client.models.list():
        # Handle potential None name
        model_name = model.name or ""
        if not model_name:
            continue

        # Basic filtering for Gemini models
        if "gemini" not in model_name.lower():
            continue

        models.append(
            GeminiModelInfo(
                name=model_name,
                display_name=model.display_name or model_name,
                description=model.description or "",
                input_token_limit=model.input_token_limit or 0,
                output_token_limit=model.output_token_limit or 0,
            )
        )

    return models


def validate_gemini_setup(
    api_key: SecretStr,
    requested_model: str | None = None,
    default_model: str = "gemini-2.5-flash",
) -> GeminiValidationResult:
    """Validate Gemini API setup at runtime using Google GenAI SDK.

    Args:
        api_key: Google API key for Gemini access.
        requested_model: Specific model requested by user (optional).
        default_model: Default model to use if none requested.

    Returns:
        GeminiValidationResult with status, message, and diagnostics.
    """
    model_to_validate = requested_model or default_model

    try:
        # Attempt to list models to verify credentials and connectivity
        available = list_models(api_key)

    except Exception as e:
        error_str = str(e).lower()

        # Check for common API key errors
        if (
            "api key" in error_str
            or "invalid" in error_str
            or "401" in error_str
            or "unauthenticated" in error_str
        ):
            logger.exception("Gemini API key validation failed")
            return GeminiValidationResult(
                status=ValidationStatus.INVALID_API_KEY,
                message="Invalid Google API key. Please check your GOOGLE_API_KEY.",
                error_details=str(e),
            )

        # Check for network errors
        if "network" in error_str or "timeout" in error_str or "connection" in error_str:
            logger.warning("Network error while validating Gemini setup: %s", e)
            return GeminiValidationResult(
                status=ValidationStatus.NETWORK_ERROR,
                message=(
                    "Could not connect to Gemini API. "
                    "Proceeding with configured model, but API may be unavailable."
                ),
                model=model_to_validate,
                error_details=str(e),
            )

        # Unknown error
        logger.exception("Unknown error validating Gemini setup")
        return GeminiValidationResult(
            status=ValidationStatus.UNKNOWN_ERROR,
            message=f"Failed to validate Gemini setup: {e}",
            error_details=str(e),
        )

    # Check if requested model is available
    available_names = tuple(m.short_name for m in available)
    available_full_names = tuple(m.name for m in available)

    # Check both short and full names
    model_found = (
        model_to_validate in available_names
        or model_to_validate in available_full_names
        or f"models/{model_to_validate}" in available_full_names
    )

    if not model_found:
        # Format available models for error message
        model_list = ", ".join(sorted(available_names)[:_ERROR_MODEL_LIST_LIMIT])
        if len(available_names) > _ERROR_MODEL_LIST_LIMIT:
            model_list += f", ... ({len(available_names)} total)"

        logger.error(
            "Requested model '%s' not found. Available: %s",
            model_to_validate,
            available_names,
        )
        return GeminiValidationResult(
            status=ValidationStatus.MODEL_NOT_FOUND,
            message=(
                f"Model '{model_to_validate}' is not available. Available models: {model_list}"
            ),
            available_models=available_names,
            error_details=f"Requested: {model_to_validate}, Available: {available_names}",
        )

    # Success
    logger.info("Gemini setup validated successfully. Using model: %s", model_to_validate)
    return GeminiValidationResult(
        status=ValidationStatus.SUCCESS,
        message=f"Gemini API configured successfully with model '{model_to_validate}'.",
        model=model_to_validate,
        available_models=available_names,
    )


_DESC_MAX_LENGTH = 35


def format_models_table(models: list[GeminiModelInfo]) -> str:
    """Format models as a readable table string.

    Args:
        models: List of Gemini model info objects.

    Returns:
        Formatted table string.
    """
    lines = [
        "Available Gemini Models:",
        "=" * 80,
        f"{'Model':<25} | {'Input':<10} | {'Output':<10} | Description",
        "-" * 80,
    ]

    for model in sorted(models, key=lambda m: m.short_name):
        desc = model.description
        if len(desc) > _DESC_MAX_LENGTH:
            desc = desc[:_DESC_MAX_LENGTH] + "..."
        lines.append(
            f"{model.short_name:<25} | "
            f"{model.input_token_limit:<10} | "
            f"{model.output_token_limit:<10} | "
            f"{desc}"
        )

    lines.append("-" * 80)
    lines.append(f"Total: {len(models)} models")

    return "\n".join(lines)


def format_validation_result(result: GeminiValidationResult) -> str:
    """Format validation result for CLI output.

    Args:
        result: Validation result to format.

    Returns:
        Formatted string for CLI display.
    """
    if result.is_success:
        return f"[OK] {result.message}"

    if result.is_warning:
        return f"[WARNING] {result.message}"

    # Error
    output = f"[ERROR] {result.message}"
    if result.available_models:
        output += "\n\nAvailable models:\n"
        for model in sorted(result.available_models)[:_FORMAT_MODEL_LIST_LIMIT]:
            output += f"  - {model}\n"
        remaining = len(result.available_models) - _FORMAT_MODEL_LIST_LIMIT
        if remaining > 0:
            output += f"  ... and {remaining} more\n"

    return output


__all__ = [
    "GeminiModelInfo",
    "GeminiValidationResult",
    "ValidationStatus",
    "format_models_table",
    "format_validation_result",
    "list_models",
    "validate_gemini_setup",
]
