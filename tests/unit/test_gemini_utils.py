"""Unit tests for Gemini utilities."""

from unittest.mock import MagicMock, patch

import pytest
from pydantic import SecretStr

from ai_reviewer.utils.gemini import (
    GeminiModelInfo,
    GeminiValidationResult,
    ValidationStatus,
    format_models_table,
    format_validation_result,
    validate_gemini_setup,
)


class TestGeminiModelInfo:
    """Tests for GeminiModelInfo dataclass."""

    @pytest.fixture
    def sample_model(self) -> GeminiModelInfo:
        """Create a sample model info for testing."""
        return GeminiModelInfo(
            name="models/gemini-2.5-flash",
            display_name="Gemini 2.5 Flash",
            description="Fast and versatile model for various tasks",
            input_token_limit=1048576,
            output_token_limit=8192,
        )

    def test_create_model_info(self, sample_model: GeminiModelInfo) -> None:
        """Test creating a GeminiModelInfo instance."""
        assert sample_model.name == "models/gemini-2.5-flash"
        assert sample_model.display_name == "Gemini 2.5 Flash"
        assert sample_model.input_token_limit == 1048576
        assert sample_model.output_token_limit == 8192

    def test_short_name_property(self, sample_model: GeminiModelInfo) -> None:
        """Test short_name removes 'models/' prefix."""
        assert sample_model.short_name == "gemini-2.5-flash"

    def test_short_name_without_prefix(self) -> None:
        """Test short_name when name has no prefix."""
        model = GeminiModelInfo(
            name="gemini-2.5-pro",
            display_name="Gemini 2.5 Pro",
            description="",
            input_token_limit=0,
            output_token_limit=0,
        )
        assert model.short_name == "gemini-2.5-pro"

    def test_model_info_is_frozen(self, sample_model: GeminiModelInfo) -> None:
        """Test that GeminiModelInfo is immutable."""
        with pytest.raises(AttributeError):
            sample_model.name = "modified"  # type: ignore[misc]


class TestFormatModelsTable:
    """Tests for format_models_table function."""

    def test_format_empty_list(self) -> None:
        """Test formatting an empty model list."""
        result = format_models_table([])
        assert "Available Gemini Models:" in result
        assert "Total: 0 models" in result

    def test_format_single_model(self) -> None:
        """Test formatting a single model."""
        models = [
            GeminiModelInfo(
                name="models/gemini-2.5-flash",
                display_name="Gemini 2.5 Flash",
                description="Fast model",
                input_token_limit=1000000,
                output_token_limit=8192,
            )
        ]
        result = format_models_table(models)
        assert "gemini-2.5-flash" in result
        assert "1000000" in result
        assert "8192" in result
        assert "Fast model" in result
        assert "Total: 1 models" in result

    def test_format_truncates_long_description(self) -> None:
        """Test that long descriptions are truncated."""
        models = [
            GeminiModelInfo(
                name="models/test",
                display_name="Test",
                description="This is a very long description that should be truncated",
                input_token_limit=0,
                output_token_limit=0,
            )
        ]
        result = format_models_table(models)
        assert "..." in result
        assert "truncated" not in result  # Original word should be cut off

    def test_format_models_sorted(self) -> None:
        """Test that models are sorted by short_name."""
        models = [
            GeminiModelInfo(
                name="models/z-model",
                display_name="Z",
                description="",
                input_token_limit=0,
                output_token_limit=0,
            ),
            GeminiModelInfo(
                name="models/a-model",
                display_name="A",
                description="",
                input_token_limit=0,
                output_token_limit=0,
            ),
        ]
        result = format_models_table(models)
        a_pos = result.find("a-model")
        z_pos = result.find("z-model")
        assert a_pos < z_pos  # a-model should appear before z-model


class TestValidationStatus:
    """Tests for ValidationStatus enum."""

    def test_all_statuses_are_strings(self) -> None:
        """Test that all statuses are string enums."""
        for status in ValidationStatus:
            assert isinstance(status.value, str)

    def test_status_values(self) -> None:
        """Test expected status values."""
        assert ValidationStatus.SUCCESS.value == "success"
        assert ValidationStatus.INVALID_API_KEY.value == "invalid_api_key"
        assert ValidationStatus.MODEL_NOT_FOUND.value == "model_not_found"
        assert ValidationStatus.NETWORK_ERROR.value == "network_error"
        assert ValidationStatus.UNKNOWN_ERROR.value == "unknown_error"


class TestGeminiValidationResult:
    """Tests for GeminiValidationResult dataclass."""

    def test_success_result(self) -> None:
        """Test creating a successful validation result."""
        result = GeminiValidationResult(
            status=ValidationStatus.SUCCESS,
            message="API configured successfully",
            model="gemini-2.5-flash",
            available_models=("gemini-2.5-flash", "gemini-2.5-pro"),
        )
        assert result.is_success is True
        assert result.is_error is False
        assert result.is_warning is False
        assert result.model == "gemini-2.5-flash"

    def test_error_result_invalid_key(self) -> None:
        """Test validation result for invalid API key."""
        result = GeminiValidationResult(
            status=ValidationStatus.INVALID_API_KEY,
            message="Invalid API key",
            error_details="401 Unauthorized",
        )
        assert result.is_success is False
        assert result.is_error is True
        assert result.is_warning is False

    def test_error_result_model_not_found(self) -> None:
        """Test validation result for model not found."""
        result = GeminiValidationResult(
            status=ValidationStatus.MODEL_NOT_FOUND,
            message="Model not found",
            available_models=("gemini-2.5-flash",),
        )
        assert result.is_success is False
        assert result.is_error is True
        assert result.is_warning is False

    def test_warning_result_network_error(self) -> None:
        """Test validation result for network error."""
        result = GeminiValidationResult(
            status=ValidationStatus.NETWORK_ERROR,
            message="Network error",
            model="gemini-2.5-flash",
            error_details="Connection timeout",
        )
        assert result.is_success is False
        assert result.is_error is False
        assert result.is_warning is True

    def test_unknown_error_result(self) -> None:
        """Test validation result for unknown error."""
        result = GeminiValidationResult(
            status=ValidationStatus.UNKNOWN_ERROR,
            message="Unknown error occurred",
        )
        assert result.is_success is False
        assert result.is_error is True
        assert result.is_warning is False

    def test_result_is_frozen(self) -> None:
        """Test that GeminiValidationResult is immutable."""
        result = GeminiValidationResult(
            status=ValidationStatus.SUCCESS,
            message="OK",
        )
        with pytest.raises(AttributeError):
            result.status = ValidationStatus.INVALID_API_KEY  # type: ignore[misc]


class TestFormatValidationResult:
    """Tests for format_validation_result function."""

    def test_format_success(self) -> None:
        """Test formatting successful result."""
        result = GeminiValidationResult(
            status=ValidationStatus.SUCCESS,
            message="Gemini API configured successfully",
        )
        formatted = format_validation_result(result)
        assert formatted.startswith("[OK]")
        assert "configured successfully" in formatted

    def test_format_warning(self) -> None:
        """Test formatting warning result."""
        result = GeminiValidationResult(
            status=ValidationStatus.NETWORK_ERROR,
            message="Could not connect to API",
            model="gemini-2.5-flash",
        )
        formatted = format_validation_result(result)
        assert formatted.startswith("[WARNING]")
        assert "connect" in formatted

    def test_format_error_without_models(self) -> None:
        """Test formatting error result without available models."""
        result = GeminiValidationResult(
            status=ValidationStatus.INVALID_API_KEY,
            message="Invalid API key",
        )
        formatted = format_validation_result(result)
        assert formatted.startswith("[ERROR]")
        assert "Invalid API key" in formatted

    def test_format_error_with_models(self) -> None:
        """Test formatting error result with available models list."""
        result = GeminiValidationResult(
            status=ValidationStatus.MODEL_NOT_FOUND,
            message="Model 'nonexistent' not found",
            available_models=("gemini-2.5-flash", "gemini-2.5-pro"),
        )
        formatted = format_validation_result(result)
        assert "[ERROR]" in formatted
        assert "Available models:" in formatted
        assert "gemini-2.5-flash" in formatted
        assert "gemini-2.5-pro" in formatted


class TestValidateGeminiSetup:
    """Tests for validate_gemini_setup function with mocked API."""

    @patch("ai_reviewer.utils.gemini.list_models")
    def test_success_with_default_model(self, mock_list: MagicMock) -> None:
        """Test successful validation with default model."""
        mock_list.return_value = [
            GeminiModelInfo(
                name="models/gemini-2.5-flash",
                display_name="Gemini 2.5 Flash",
                description="Fast model",
                input_token_limit=1000000,
                output_token_limit=8192,
            ),
        ]

        result = validate_gemini_setup(SecretStr("test-api-key"))

        assert result.is_success is True
        assert result.model == "gemini-2.5-flash"
        mock_list.assert_called_once()

    @patch("ai_reviewer.utils.gemini.list_models")
    def test_success_with_requested_model(self, mock_list: MagicMock) -> None:
        """Test successful validation with specific requested model."""
        mock_list.return_value = [
            GeminiModelInfo(
                name="models/gemini-2.5-pro",
                display_name="Gemini 2.5 Pro",
                description="Pro model",
                input_token_limit=2000000,
                output_token_limit=16384,
            ),
        ]

        result = validate_gemini_setup(SecretStr("test-api-key"), requested_model="gemini-2.5-pro")

        assert result.is_success is True
        assert result.model == "gemini-2.5-pro"

    @patch("ai_reviewer.utils.gemini.list_models")
    def test_model_not_found(self, mock_list: MagicMock) -> None:
        """Test validation when requested model is not available."""
        mock_list.return_value = [
            GeminiModelInfo(
                name="models/gemini-2.5-flash",
                display_name="Gemini 2.5 Flash",
                description="Fast model",
                input_token_limit=1000000,
                output_token_limit=8192,
            ),
        ]

        result = validate_gemini_setup(
            SecretStr("test-api-key"), requested_model="nonexistent-model"
        )

        assert result.status == ValidationStatus.MODEL_NOT_FOUND
        assert result.is_error is True
        assert "nonexistent-model" in result.message
        assert "gemini-2.5-flash" in result.available_models

    @patch("ai_reviewer.utils.gemini.list_models")
    def test_invalid_api_key(self, mock_list: MagicMock) -> None:
        """Test validation with invalid API key."""
        mock_list.side_effect = Exception("Invalid API key: 401 Unauthorized")

        result = validate_gemini_setup(SecretStr("invalid-key"))

        assert result.status == ValidationStatus.INVALID_API_KEY
        assert result.is_error is True
        assert "Invalid" in result.message or "API key" in result.message

    @patch("ai_reviewer.utils.gemini.list_models")
    def test_network_error(self, mock_list: MagicMock) -> None:
        """Test validation with network error."""
        mock_list.side_effect = Exception("Network connection timeout")

        result = validate_gemini_setup(SecretStr("test-api-key"))

        assert result.status == ValidationStatus.NETWORK_ERROR
        assert result.is_warning is True
        assert result.model == "gemini-2.5-flash"

    @patch("ai_reviewer.utils.gemini.list_models")
    def test_unknown_error(self, mock_list: MagicMock) -> None:
        """Test validation with unknown error."""
        mock_list.side_effect = Exception("Something unexpected happened")

        result = validate_gemini_setup(SecretStr("test-api-key"))

        assert result.status == ValidationStatus.UNKNOWN_ERROR
        assert result.is_error is True

    @patch("ai_reviewer.utils.gemini.list_models")
    def test_model_found_with_full_name(self, mock_list: MagicMock) -> None:
        """Test model found when using full name with models/ prefix."""
        mock_list.return_value = [
            GeminiModelInfo(
                name="models/gemini-2.5-flash",
                display_name="Gemini 2.5 Flash",
                description="Fast model",
                input_token_limit=1000000,
                output_token_limit=8192,
            ),
        ]

        result = validate_gemini_setup(
            SecretStr("test-api-key"), requested_model="models/gemini-2.5-flash"
        )

        assert result.is_success is True
