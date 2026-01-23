"""Configuration management for AI Code Reviewer.

This module provides configuration loading from environment variables
using pydantic-settings. All sensitive values (tokens, API keys) are
loaded from environment variables and never hardcoded.

This module performs only local validation (format, length, syntax).
Runtime validation (API availability, model existence) is handled by
provider-specific modules (e.g., gemini.py).

Example:
    >>> import os
    >>> os.environ["GITHUB_TOKEN"] = "ghp_xxxx"
    >>> os.environ["GOOGLE_API_KEY"] = "AIza_xxxx"
    >>> settings = Settings()
    >>> settings.github_token.get_secret_value()
    'ghp_xxxx'
"""

from __future__ import annotations

from typing import Annotated

from pydantic import AfterValidator, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# Minimum length for API tokens/keys validation
MIN_SECRET_LENGTH = 10

# Valid log levels
VALID_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})


def _create_secret_validator(
    field_name: str,
    min_length: int = MIN_SECRET_LENGTH,
) -> AfterValidator:
    """Create a validator for secret fields.

    Args:
        field_name: Human-readable field name for error messages.
        min_length: Minimum required length for the secret.

    Returns:
        AfterValidator that checks secret length.
    """

    def validate_secret(v: SecretStr) -> SecretStr:
        """Validate that secret meets minimum length requirement."""
        if len(v.get_secret_value()) < min_length:
            msg = (
                f"{field_name} is too short (minimum {min_length} characters). "
                f"Please provide a valid {field_name}."
            )
            raise ValueError(msg)
        return v

    return AfterValidator(validate_secret)


def _validate_log_level(v: str) -> str:
    """Validate and normalize log level."""
    normalized = v.upper()
    if normalized not in VALID_LOG_LEVELS:
        msg = f"Invalid log level '{v}'. Must be one of: {', '.join(sorted(VALID_LOG_LEVELS))}"
        raise ValueError(msg)
    return normalized


# Type aliases with validation
GitHubToken = Annotated[SecretStr, _create_secret_validator("GITHUB_TOKEN")]
GoogleApiKey = Annotated[SecretStr, _create_secret_validator("GOOGLE_API_KEY")]
LogLevel = Annotated[str, AfterValidator(_validate_log_level)]


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All sensitive values are stored as SecretStr to prevent accidental
    exposure in logs or error messages.

    This class performs only local validation:
    - Secret length checks
    - Log level validation
    - Numeric range validation

    Runtime validation (API connectivity, model availability) should be
    performed explicitly using provider modules (e.g., validate_gemini_setup).

    Attributes:
        github_token: GitHub personal access token for API access.
            Required for fetching PR data and posting review comments.
        google_api_key: Google API key for Gemini access.
            Required for AI-powered code analysis.
        gemini_model: Gemini model to use for analysis.
            Defaults to gemini-2.5-flash for cost efficiency.
        log_level: Logging level for the application.
            One of: DEBUG, INFO, WARNING, ERROR, CRITICAL.
        review_max_files: Maximum number of files to include in review context.
            Limits context size to avoid token limits.
        review_max_diff_lines: Maximum diff lines per file to include.
            Limits context size for large changes.

    Environment Variables:
        GITHUB_TOKEN: GitHub personal access token (required)
        GOOGLE_API_KEY: Google Gemini API key (required)
        GEMINI_MODEL: Model name (default: gemini-2.5-flash)
        LOG_LEVEL: Logging level (default: INFO)
        REVIEW_MAX_FILES: Max files in context (default: 20)
        REVIEW_MAX_DIFF_LINES: Max diff lines per file (default: 500)
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Required credentials (validated for minimum length only)
    github_token: GitHubToken = Field(
        ...,
        description="GitHub personal access token for API access",
    )
    google_api_key: GoogleApiKey = Field(
        ...,
        description="Google API key for Gemini access",
    )

    # Optional configuration with defaults
    gemini_model: str = Field(
        default="gemini-2.5-flash",
        description="Gemini model to use for analysis",
    )
    log_level: LogLevel = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    review_max_files: int = Field(
        default=20,
        gt=0,
        le=100,
        description="Maximum number of files to include in review context",
    )
    review_max_diff_lines: int = Field(
        default=500,
        gt=0,
        le=5000,
        description="Maximum diff lines per file to include",
    )


def get_settings() -> Settings:
    """Get application settings from environment.

    This function creates a new Settings instance each time it's called.
    For caching, use functools.lru_cache or store the result.

    Returns:
        Settings instance loaded from environment variables.

    Raises:
        pydantic.ValidationError: If required environment variables are missing
            or validation fails.

    Example:
        >>> settings = get_settings()  # doctest: +SKIP
        >>> print(settings.gemini_model)  # doctest: +SKIP
        gemini-2.5-flash
    """
    # pydantic-settings loads required fields from environment variables
    return Settings()


__all__ = [
    "MIN_SECRET_LENGTH",
    "VALID_LOG_LEVELS",
    "Settings",
    "get_settings",
]
