"""Unit tests for configuration management."""

import os
from unittest.mock import patch

import pytest
from pydantic import SecretStr, ValidationError

from ai_reviewer.core.config import Settings, get_settings


class TestSettings:
    """Tests for Settings class."""

    @pytest.fixture
    def minimal_env(self) -> dict[str, str]:
        """Return minimal required environment variables."""
        return {
            "GITHUB_TOKEN": "ghp_test_token_12345",
            "GOOGLE_API_KEY": "AIza_test_key_12345",
        }

    @pytest.fixture
    def full_env(self) -> dict[str, str]:
        """Return all environment variables with custom values."""
        return {
            "GITHUB_TOKEN": "ghp_test_token_12345",
            "GOOGLE_API_KEY": "AIza_test_key_12345",
            "GEMINI_MODEL": "gemini-1.5-pro",
            "LOG_LEVEL": "DEBUG",
            "REVIEW_MAX_FILES": "50",
            "REVIEW_MAX_DIFF_LINES": "1000",
        }

    def test_create_settings_with_minimal_env(self, minimal_env: dict[str, str]) -> None:
        """Test creating settings with only required env vars."""
        with patch.dict(os.environ, minimal_env, clear=True):
            settings = Settings()

            assert settings.github_token.get_secret_value() == "ghp_test_token_12345"
            assert settings.google_api_key.get_secret_value() == "AIza_test_key_12345"
            # Check defaults
            assert settings.gemini_model == "gemini-2.5-flash"
            assert settings.log_level == "INFO"
            assert settings.review_max_files == 20
            assert settings.review_max_diff_lines == 500

    def test_create_settings_with_full_env(self, full_env: dict[str, str]) -> None:
        """Test creating settings with all env vars."""
        with patch.dict(os.environ, full_env, clear=True):
            settings = Settings()

            assert settings.gemini_model == "gemini-1.5-pro"
            assert settings.log_level == "DEBUG"
            assert settings.review_max_files == 50
            assert settings.review_max_diff_lines == 1000

    def test_missing_github_token_raises_error(self) -> None:
        """Test that missing GITHUB_TOKEN raises ValidationError."""
        env = {"GOOGLE_API_KEY": "AIza_test_key_12345"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            assert "github_token" in str(exc_info.value).lower()

    def test_missing_google_api_key_raises_error(self) -> None:
        """Test that missing GOOGLE_API_KEY raises ValidationError."""
        env = {"GITHUB_TOKEN": "ghp_test_token_12345"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            assert "google_api_key" in str(exc_info.value).lower()

    def test_github_token_too_short_raises_error(self) -> None:
        """Test that short GITHUB_TOKEN raises ValidationError."""
        env = {
            "GITHUB_TOKEN": "short",
            "GOOGLE_API_KEY": "AIza_test_key_12345",
        }
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            assert "too short" in str(exc_info.value).lower()

    def test_google_api_key_too_short_raises_error(self) -> None:
        """Test that short GOOGLE_API_KEY raises ValidationError."""
        env = {
            "GITHUB_TOKEN": "ghp_test_token_12345",
            "GOOGLE_API_KEY": "short",
        }
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            assert "too short" in str(exc_info.value).lower()

    def test_invalid_log_level_raises_error(self, minimal_env: dict[str, str]) -> None:
        """Test that invalid LOG_LEVEL raises ValidationError."""
        env = {**minimal_env, "LOG_LEVEL": "INVALID"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            error_msg = str(exc_info.value).lower()
            assert "log_level" in error_msg or "invalid" in error_msg

    def test_log_level_case_insensitive(self, minimal_env: dict[str, str]) -> None:
        """Test that LOG_LEVEL is case insensitive."""
        for level in ["debug", "Debug", "DEBUG", "dEbUg"]:
            env = {**minimal_env, "LOG_LEVEL": level}
            with patch.dict(os.environ, env, clear=True):
                settings = Settings()
                assert settings.log_level == "DEBUG"

    def test_all_valid_log_levels(self, minimal_env: dict[str, str]) -> None:
        """Test all valid log levels are accepted."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for level in valid_levels:
            env = {**minimal_env, "LOG_LEVEL": level}
            with patch.dict(os.environ, env, clear=True):
                settings = Settings()
                assert settings.log_level == level

    def test_review_max_files_validation(self, minimal_env: dict[str, str]) -> None:
        """Test REVIEW_MAX_FILES validation."""
        # Zero is invalid
        env = {**minimal_env, "REVIEW_MAX_FILES": "0"}
        with patch.dict(os.environ, env, clear=True), pytest.raises(ValidationError):
            Settings()

        # Negative is invalid
        env = {**minimal_env, "REVIEW_MAX_FILES": "-1"}
        with patch.dict(os.environ, env, clear=True), pytest.raises(ValidationError):
            Settings()

        # Over 100 is invalid
        env = {**minimal_env, "REVIEW_MAX_FILES": "101"}
        with patch.dict(os.environ, env, clear=True), pytest.raises(ValidationError):
            Settings()

        # Boundary value should be accepted
        env = {**minimal_env, "REVIEW_MAX_FILES": "100"}
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert settings.review_max_files == 100

    def test_review_max_diff_lines_validation(self, minimal_env: dict[str, str]) -> None:
        """Test REVIEW_MAX_DIFF_LINES validation."""
        # Zero is invalid
        env = {**minimal_env, "REVIEW_MAX_DIFF_LINES": "0"}
        with patch.dict(os.environ, env, clear=True), pytest.raises(ValidationError):
            Settings()

        # Over 5000 is invalid
        env = {**minimal_env, "REVIEW_MAX_DIFF_LINES": "5001"}
        with patch.dict(os.environ, env, clear=True), pytest.raises(ValidationError):
            Settings()

        # Boundary value should be accepted
        env = {**minimal_env, "REVIEW_MAX_DIFF_LINES": "5000"}
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert settings.review_max_diff_lines == 5000

    def test_secrets_are_hidden(self, minimal_env: dict[str, str]) -> None:
        """Test that secrets are not exposed in string representation."""
        with patch.dict(os.environ, minimal_env, clear=True):
            settings = Settings()

            # Check that secrets are SecretStr
            assert isinstance(settings.github_token, SecretStr)
            assert isinstance(settings.google_api_key, SecretStr)

            # Check that str/repr don't expose secrets
            settings_str = str(settings)
            settings_repr = repr(settings)

            assert "ghp_test_token_12345" not in settings_str
            assert "ghp_test_token_12345" not in settings_repr
            assert "AIza_test_key_12345" not in settings_str
            assert "AIza_test_key_12345" not in settings_repr

    def test_extra_env_vars_ignored(self, minimal_env: dict[str, str]) -> None:
        """Test that extra environment variables are ignored."""
        env = {**minimal_env, "UNKNOWN_VAR": "some_value"}
        with patch.dict(os.environ, env, clear=True):
            # Should not raise
            settings = Settings()
            assert not hasattr(settings, "unknown_var")


class TestGetSettings:
    """Tests for get_settings function."""

    def test_get_settings_returns_settings_instance(self) -> None:
        """Test that get_settings returns a Settings instance."""
        env = {
            "GITHUB_TOKEN": "ghp_test_token_12345",
            "GOOGLE_API_KEY": "AIza_test_key_12345",
        }
        with patch.dict(os.environ, env, clear=True):
            settings = get_settings()
            assert isinstance(settings, Settings)

    def test_get_settings_creates_new_instance_each_call(self) -> None:
        """Test that get_settings creates a new instance each call."""
        env = {
            "GITHUB_TOKEN": "ghp_test_token_12345",
            "GOOGLE_API_KEY": "AIza_test_key_12345",
        }
        with patch.dict(os.environ, env, clear=True):
            settings1 = get_settings()
            settings2 = get_settings()
            # Different objects
            assert settings1 is not settings2
            # But same values
            assert settings1.gemini_model == settings2.gemini_model

    def test_get_settings_raises_on_missing_env(self) -> None:
        """Test that get_settings raises when env vars are missing."""
        with patch.dict(os.environ, {}, clear=True), pytest.raises(ValidationError):
            get_settings()
