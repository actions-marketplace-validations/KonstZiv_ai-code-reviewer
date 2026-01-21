"""Integration tests for Gemini client."""

from unittest.mock import MagicMock, Mock, patch

import pytest
from pydantic import SecretStr, ValidationError

from ai_reviewer.core.config import Settings
from ai_reviewer.core.models import (
    MergeRequest,
    ReviewContext,
    ReviewResult,
    TaskAlignmentStatus,
    Vulnerability,
    VulnerabilitySeverity,
)
from ai_reviewer.integrations.gemini import GeminiClient, analyze_code_changes


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
        mock_response = Mock()
        # Pass an invalid enum value to trigger ValidationError
        mock_response.parsed = {"task_alignment": "INVALID_STATUS"}
        client.client.models.generate_content.return_value = mock_response

        with pytest.raises(ValidationError):
            client.generate_review("Test prompt")


class TestAnalyzeCodeChanges:
    """Tests for analyze_code_changes orchestration function."""

    @pytest.fixture
    def mock_settings(self) -> Settings:
        """Create mock settings."""
        settings = Mock(spec=Settings)
        settings.google_api_key = SecretStr("test-key")
        settings.gemini_model = "gemini-pro"
        settings.review_max_files = 5
        settings.review_max_diff_lines = 10
        return settings

    @pytest.fixture
    def mock_context(self) -> ReviewContext:
        """Create mock review context."""
        mr = Mock(spec=MergeRequest)
        mr.number = 123
        mr.title = "Test PR"
        mr.description = "Desc"
        mr.changes = []

        context = Mock(spec=ReviewContext)
        context.mr = mr
        context.task = None
        return context

    @patch("ai_reviewer.integrations.gemini.GeminiClient")
    @patch("ai_reviewer.integrations.gemini.build_review_prompt")
    def test_analyze_flow(
        self,
        mock_build_prompt: MagicMock,
        mock_client_cls: MagicMock,
        mock_context: ReviewContext,
        mock_settings: Settings,
    ) -> None:
        """Test the full analysis flow."""
        # Setup mocks
        mock_build_prompt.return_value = "Constructed Prompt"

        mock_client_instance = mock_client_cls.return_value
        expected_result = ReviewResult(summary="LGTM")
        mock_client_instance.generate_review.return_value = expected_result

        # Execute
        result = analyze_code_changes(mock_context, mock_settings)

        # Verify
        assert result == expected_result

        # Verify prompt building
        mock_build_prompt.assert_called_once_with(mock_context, mock_settings)

        # Verify client initialization
        mock_client_cls.assert_called_once_with(
            api_key=mock_settings.google_api_key,
            model_name=mock_settings.gemini_model,
        )

        # Verify generation call
        mock_client_instance.generate_review.assert_called_once_with("Constructed Prompt")
