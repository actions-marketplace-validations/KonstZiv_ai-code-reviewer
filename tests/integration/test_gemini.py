"""Integration tests for Gemini client."""

from unittest.mock import MagicMock, Mock, patch

import pytest
from pydantic import SecretStr, ValidationError

from ai_reviewer.core.config import Settings
from ai_reviewer.core.models import (
    CodeIssue,
    IssueCategory,
    IssueSeverity,
    MergeRequest,
    ReviewContext,
    ReviewResult,
    TaskAlignmentStatus,
)
from ai_reviewer.integrations.gemini import (
    DEFAULT_MODEL,
    DEFAULT_PRICING,
    GEMINI_PRICING,
    GeminiClient,
    analyze_code_changes,
    calculate_cost,
)


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
            issues=(
                CodeIssue(
                    category=IssueCategory.SECURITY,
                    severity=IssueSeverity.CRITICAL,
                    title="SQL Injection",
                    description="Unsafe query",
                ),
            ),
            task_alignment=TaskAlignmentStatus.ALIGNED,
            summary="Code looks good but has one issue.",
        )

        mock_response.parsed = expected_result
        # Explicitly set usage_metadata to None to avoid Mock auto-creation
        mock_response.usage_metadata = None
        client.client.models.generate_content.return_value = mock_response

        # Execute
        result = client.generate_review("Test prompt")

        # Verify
        assert isinstance(result, ReviewResult)
        assert len(result.issues) == 1
        assert result.issues[0].title == "SQL Injection"
        assert result.task_alignment == TaskAlignmentStatus.ALIGNED
        # Verify metrics are present (even with zero tokens)
        assert result.metrics is not None
        assert result.metrics.model_name == DEFAULT_MODEL

        # Verify API call arguments
        client.client.models.generate_content.assert_called_once()
        call_kwargs = client.client.models.generate_content.call_args.kwargs
        assert call_kwargs["model"] == DEFAULT_MODEL
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
        mock_response.usage_metadata = None
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


class TestCalculateCost:
    """Tests for calculate_cost function."""

    def test_calculate_cost_known_model(self) -> None:
        """Test cost calculation for a known model."""
        # gemini-2.5-flash: $0.075/1M input, $0.30/1M output
        cost = calculate_cost("gemini-2.5-flash", 1_000_000, 500_000)
        expected = 0.075 + (0.30 * 0.5)  # $0.075 + $0.15 = $0.225
        assert cost == pytest.approx(expected)

    def test_calculate_cost_pro_model(self) -> None:
        """Test cost calculation for pro model."""
        # gemini-1.5-pro: $1.25/1M input, $5.00/1M output
        cost = calculate_cost("gemini-1.5-pro", 1_000_000, 100_000)
        expected = 1.25 + (5.00 * 0.1)  # $1.25 + $0.50 = $1.75
        assert cost == pytest.approx(expected)

    def test_calculate_cost_unknown_model(self) -> None:
        """Test cost calculation for unknown model uses default pricing."""
        cost = calculate_cost("unknown-model", 1_000_000, 500_000)
        expected = DEFAULT_PRICING["input"] + (DEFAULT_PRICING["output"] * 0.5)
        assert cost == pytest.approx(expected)

    def test_calculate_cost_zero_tokens(self) -> None:
        """Test cost calculation with zero tokens."""
        cost = calculate_cost("gemini-2.5-flash", 0, 0)
        assert cost == 0.0

    def test_calculate_cost_small_request(self) -> None:
        """Test cost calculation for typical small request."""
        # Typical code review: ~2000 prompt tokens, ~500 completion tokens
        cost = calculate_cost("gemini-2.5-flash", 2000, 500)
        # $0.075/1M * 2000 + $0.30/1M * 500
        expected = (2000 / 1_000_000) * 0.075 + (500 / 1_000_000) * 0.30
        assert cost == pytest.approx(expected)
        # Should be very cheap (less than a cent)
        assert cost < 0.01

    def test_gemini_pricing_has_expected_models(self) -> None:
        """Test that GEMINI_PRICING contains expected models."""
        expected_models = [
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-pro",
        ]
        for model in expected_models:
            assert model in GEMINI_PRICING
            assert "input" in GEMINI_PRICING[model]
            assert "output" in GEMINI_PRICING[model]


class TestGeminiClientWithMetrics:
    """Tests for GeminiClient metrics collection."""

    @pytest.fixture
    def mock_genai_client(self) -> MagicMock:
        """Mock google.genai.Client."""
        with patch("ai_reviewer.integrations.gemini.genai.Client") as mock:
            yield mock

    @pytest.fixture
    def client(self, mock_genai_client: MagicMock) -> GeminiClient:
        """Create GeminiClient instance with mocked backend."""
        return GeminiClient(SecretStr("test-key"))

    def test_generate_review_returns_metrics(self, client: GeminiClient) -> None:
        """Test that generate_review includes metrics in result."""
        mock_response = Mock()

        # Create a valid ReviewResult
        expected_result = ReviewResult(
            summary="LGTM",
            task_alignment=TaskAlignmentStatus.ALIGNED,
        )
        mock_response.parsed = expected_result

        # Mock usage_metadata with explicit values
        mock_response.usage_metadata = Mock()
        mock_response.usage_metadata.prompt_token_count = 1000
        mock_response.usage_metadata.candidates_token_count = 500
        mock_response.usage_metadata.total_token_count = 1500

        client.client.models.generate_content.return_value = mock_response

        result = client.generate_review("Test prompt")

        # Verify metrics are included
        assert result.metrics is not None
        assert result.metrics.model_name == DEFAULT_MODEL
        assert result.metrics.prompt_tokens == 1000
        assert result.metrics.completion_tokens == 500
        assert result.metrics.total_tokens == 1500
        assert result.metrics.api_latency_ms >= 0  # Can be 0 for very fast mock calls
        assert result.metrics.estimated_cost_usd > 0

    def test_generate_review_handles_missing_usage_metadata(self, client: GeminiClient) -> None:
        """Test that generate_review handles missing usage_metadata gracefully."""
        mock_response = Mock()
        mock_response.parsed = ReviewResult(summary="LGTM")
        mock_response.usage_metadata = None

        client.client.models.generate_content.return_value = mock_response

        result = client.generate_review("Test prompt")

        # Metrics should still be present but with zero tokens
        assert result.metrics is not None
        assert result.metrics.prompt_tokens == 0
        assert result.metrics.completion_tokens == 0
        assert result.metrics.total_tokens == 0
        assert result.metrics.estimated_cost_usd == 0.0

    def test_generate_review_handles_partial_usage_metadata(self, client: GeminiClient) -> None:
        """Test that generate_review handles partial usage_metadata."""
        mock_response = Mock()
        mock_response.parsed = ReviewResult(summary="LGTM")

        # Only some fields present
        mock_response.usage_metadata = Mock()
        mock_response.usage_metadata.prompt_token_count = 1000
        mock_response.usage_metadata.candidates_token_count = None
        mock_response.usage_metadata.total_token_count = 1000

        client.client.models.generate_content.return_value = mock_response

        result = client.generate_review("Test prompt")

        assert result.metrics is not None
        assert result.metrics.prompt_tokens == 1000
        assert result.metrics.completion_tokens == 0  # None → 0
        assert result.metrics.total_tokens == 1000


class TestGeminiClientErrorHandling:
    """Tests for GeminiClient error handling and exception conversion."""

    @pytest.fixture
    def mock_genai_client(self) -> MagicMock:
        """Mock google.genai.Client."""
        with patch("ai_reviewer.integrations.gemini.genai.Client") as mock:
            yield mock

    @pytest.fixture
    def client(self, mock_genai_client: MagicMock) -> GeminiClient:
        """Create GeminiClient instance with mocked backend."""
        return GeminiClient(SecretStr("test-key"))

    @patch("ai_reviewer.integrations.gemini.with_retry", lambda f: f)  # Disable retry for test
    def test_rate_limit_raises_error(self, client: GeminiClient) -> None:
        """Test that ResourceExhausted raises RateLimitError."""
        from google.api_core import exceptions as google_exceptions

        from ai_reviewer.utils.retry import RateLimitError

        client.client.models.generate_content.side_effect = google_exceptions.ResourceExhausted(
            "Quota exceeded"
        )

        with pytest.raises(RateLimitError):
            client.generate_review("Test prompt")

    @patch("ai_reviewer.integrations.gemini.with_retry", lambda f: f)  # Disable retry for test
    def test_auth_error_raises_error(self, client: GeminiClient) -> None:
        """Test that Unauthenticated raises AuthenticationError."""
        from google.api_core import exceptions as google_exceptions

        from ai_reviewer.utils.retry import AuthenticationError

        client.client.models.generate_content.side_effect = google_exceptions.Unauthenticated(
            "Invalid API key"
        )

        with pytest.raises(AuthenticationError):
            client.generate_review("Test prompt")

    @patch("ai_reviewer.integrations.gemini.with_retry", lambda f: f)  # Disable retry for test
    def test_forbidden_raises_error(self, client: GeminiClient) -> None:
        """Test that PermissionDenied raises ForbiddenError."""
        from google.api_core import exceptions as google_exceptions

        from ai_reviewer.utils.retry import ForbiddenError

        client.client.models.generate_content.side_effect = google_exceptions.PermissionDenied(
            "Access denied"
        )

        with pytest.raises(ForbiddenError):
            client.generate_review("Test prompt")

    @patch("ai_reviewer.integrations.gemini.with_retry", lambda f: f)  # Disable retry for test
    def test_server_error_raises_error(self, client: GeminiClient) -> None:
        """Test that InternalServerError raises ServerError."""
        from google.api_core import exceptions as google_exceptions

        from ai_reviewer.utils.retry import ServerError

        client.client.models.generate_content.side_effect = google_exceptions.InternalServerError(
            "Internal error"
        )

        with pytest.raises(ServerError):
            client.generate_review("Test prompt")
