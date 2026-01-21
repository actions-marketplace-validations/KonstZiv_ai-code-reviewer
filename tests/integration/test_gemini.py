"""Integration tests for Gemini client."""

from unittest.mock import MagicMock, Mock, patch

import pytest
from pydantic import SecretStr, ValidationError

from ai_reviewer.core.models import (
    ReviewResult,
    TaskAlignmentStatus,
    Vulnerability,
    VulnerabilitySeverity,
)
from ai_reviewer.integrations.gemini import GeminiClient


class TestGeminiClient:
    """Tests for GeminiClient."""

    @pytest.fixture
    def mock_genai_client(self) -> MagicMock:
        """Mock google.genai.Client."""
        with patch("ai_reviewer.integrations.gemini.genai.Client") as mock:
            yield mock

    @pytest.fixture
    def client(self, mock_genai_client: MagicMock) -> GeminiClient:
        """Create GeminiClient instance with mocked backend."""
        return GeminiClient(SecretStr("test-key"))

    def test_init(self, mock_genai_client: MagicMock) -> None:
        """Test client initialization."""
        GeminiClient(SecretStr("test-key"), model_name="gemini-2.0-flash")
        mock_genai_client.assert_called_once_with(api_key="test-key")

    def test_generate_review_success(self, client: GeminiClient) -> None:
        """Test successful review generation."""
        # Setup mock response
        mock_response = Mock()

        # Create a valid ReviewResult object that the SDK would return
        expected_result = ReviewResult(
            vulnerabilities=(
                Vulnerability(
                    title="SQL Injection",
                    description="Unsafe query",
                    severity=VulnerabilitySeverity.CRITICAL,
                ),
            ),
            task_alignment=TaskAlignmentStatus.ALIGNED,
            summary="Code looks good but has one issue.",
        )

        mock_response.parsed = expected_result
        client.client.models.generate_content.return_value = mock_response

        # Execute
        result = client.generate_review("Test prompt")

        # Verify
        assert isinstance(result, ReviewResult)
        assert len(result.vulnerabilities) == 1
        assert result.vulnerabilities[0].title == "SQL Injection"
        assert result.task_alignment == TaskAlignmentStatus.ALIGNED

        # Verify API call arguments
        client.client.models.generate_content.assert_called_once()
        call_kwargs = client.client.models.generate_content.call_args.kwargs
        assert call_kwargs["model"] == "gemini-2.5-flash"
        assert call_kwargs["contents"] == ["Test prompt"]
        assert call_kwargs["config"].response_mime_type == "application/json"
        assert call_kwargs["config"].response_schema == ReviewResult

    def test_generate_review_parsing_error(self, client: GeminiClient) -> None:
        """Test handling of parsing errors (empty parsed response)."""
        mock_response = Mock()
        mock_response.parsed = None  # Parsing failed
        client.client.models.generate_content.return_value = mock_response

        with pytest.raises(ValueError, match="could not be parsed"):
            client.generate_review("Test prompt")

    def test_generate_review_api_error(self, client: GeminiClient) -> None:
        """Test handling of API errors."""
        client.client.models.generate_content.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="API Error"):
            client.generate_review("Test prompt")

    def test_generate_review_validation_error(self, client: GeminiClient) -> None:
        """Test handling of validation errors when converting to model."""
        # This simulates a case where parsed returns a dict that doesn't match the model
        # (though with response_schema this shouldn't happen often)
        mock_response = Mock()
        mock_response.parsed = {"invalid": "data"}  # Not a ReviewResult
        client.client.models.generate_content.return_value = mock_response

        with pytest.raises(ValidationError):
            client.generate_review("Test prompt")
