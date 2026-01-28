"""Unit tests for retry utilities."""

from unittest.mock import MagicMock, patch

import pytest

from ai_reviewer.utils.retry import (
    APIClientError,
    APIError,
    AuthenticationError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    RetryableError,
    ServerError,
    is_retryable_status,
    raise_for_status,
    with_retry,
)


class TestExceptionHierarchy:
    """Tests for custom exception hierarchy."""

    def test_retryable_error_base(self) -> None:
        """Test that RetryableError is base for retryable exceptions."""
        assert issubclass(RateLimitError, RetryableError)
        assert issubclass(ServerError, RetryableError)

    def test_api_client_error_base(self) -> None:
        """Test that APIClientError is base for non-retryable exceptions."""
        assert issubclass(AuthenticationError, APIClientError)
        assert issubclass(ForbiddenError, APIClientError)
        assert issubclass(NotFoundError, APIClientError)

    def test_rate_limit_error_with_retry_after(self) -> None:
        """Test RateLimitError with retry_after attribute."""
        error = RateLimitError("Rate limit exceeded", retry_after=60)
        assert str(error) == "Rate limit exceeded"
        assert error.retry_after == 60

    def test_rate_limit_error_default(self) -> None:
        """Test RateLimitError with default values."""
        error = RateLimitError()
        assert "rate limit" in str(error).lower()
        assert error.retry_after is None

    def test_server_error_with_status_code(self) -> None:
        """Test ServerError with status_code attribute."""
        error = ServerError("Internal Server Error", status_code=500)
        assert str(error) == "Internal Server Error"
        assert error.status_code == 500

    def test_server_error_default(self) -> None:
        """Test ServerError with default values."""
        error = ServerError()
        assert "server error" in str(error).lower()
        assert error.status_code is None

    def test_authentication_error_default(self) -> None:
        """Test AuthenticationError with default message."""
        error = AuthenticationError()
        assert "authentication" in str(error).lower()

    def test_forbidden_error_default(self) -> None:
        """Test ForbiddenError with default message."""
        error = ForbiddenError()
        assert "forbidden" in str(error).lower()

    def test_not_found_error_default(self) -> None:
        """Test NotFoundError with default message."""
        error = NotFoundError()
        assert "not found" in str(error).lower()


class TestAPIError:
    """Tests for APIError with context."""

    def test_api_error_basic(self) -> None:
        """Test basic APIError creation."""
        error = APIError("Something failed")
        assert str(error) == "Something failed"
        assert error.provider is None
        assert error.operation is None
        assert error.original_error is None

    def test_api_error_with_context(self) -> None:
        """Test APIError with full context."""
        original = ValueError("Original error")
        error = APIError(
            message="API call failed",
            provider="github",
            operation="get_pull_request",
            original_error=original,
        )
        assert str(error) == "API call failed"
        assert error.provider == "github"
        assert error.operation == "get_pull_request"
        assert error.original_error is original

    def test_format_for_comment(self) -> None:
        """Test formatting error for PR comment."""
        error = APIError(
            message="Rate limit exhausted",
            provider="github",
            operation="submit_review",
        )
        formatted = error.format_for_comment()

        assert "AI Code Review Failed" in formatted
        assert "Rate limit exhausted" in formatted
        assert "github" in formatted
        assert "submit_review" in formatted
        assert "CI logs" in formatted


class TestRaiseForStatus:
    """Tests for raise_for_status helper function."""

    def test_401_raises_authentication_error(self) -> None:
        """Test that 401 raises AuthenticationError."""
        with pytest.raises(AuthenticationError):
            raise_for_status(401)

    def test_403_raises_forbidden_error(self) -> None:
        """Test that 403 raises ForbiddenError."""
        with pytest.raises(ForbiddenError):
            raise_for_status(403)

    def test_404_raises_not_found_error(self) -> None:
        """Test that 404 raises NotFoundError."""
        with pytest.raises(NotFoundError):
            raise_for_status(404)

    def test_429_raises_rate_limit_error(self) -> None:
        """Test that 429 raises RateLimitError."""
        with pytest.raises(RateLimitError):
            raise_for_status(429)

    def test_500_raises_server_error(self) -> None:
        """Test that 500 raises ServerError."""
        with pytest.raises(ServerError):
            raise_for_status(500)

    def test_502_raises_server_error(self) -> None:
        """Test that 502 raises ServerError."""
        with pytest.raises(ServerError):
            raise_for_status(502)

    def test_503_raises_server_error(self) -> None:
        """Test that 503 raises ServerError."""
        with pytest.raises(ServerError):
            raise_for_status(503)

    def test_200_does_not_raise(self) -> None:
        """Test that 200 doesn't raise."""
        # Should not raise
        raise_for_status(200)

    def test_custom_message(self) -> None:
        """Test that custom message is used."""
        with pytest.raises(NotFoundError, match="Custom not found"):
            raise_for_status(404, "Custom not found")


class TestIsRetryableStatus:
    """Tests for is_retryable_status helper function."""

    def test_429_is_retryable(self) -> None:
        """Test that 429 is retryable."""
        assert is_retryable_status(429) is True

    def test_500_is_retryable(self) -> None:
        """Test that 500 is retryable."""
        assert is_retryable_status(500) is True

    def test_502_is_retryable(self) -> None:
        """Test that 502 is retryable."""
        assert is_retryable_status(502) is True

    def test_503_is_retryable(self) -> None:
        """Test that 503 is retryable."""
        assert is_retryable_status(503) is True

    def test_401_not_retryable(self) -> None:
        """Test that 401 is not retryable."""
        assert is_retryable_status(401) is False

    def test_403_not_retryable(self) -> None:
        """Test that 403 is not retryable."""
        assert is_retryable_status(403) is False

    def test_404_not_retryable(self) -> None:
        """Test that 404 is not retryable."""
        assert is_retryable_status(404) is False

    def test_200_not_retryable(self) -> None:
        """Test that 200 is not retryable."""
        assert is_retryable_status(200) is False


class TestWithRetryDecorator:
    """Tests for with_retry decorator."""

    def test_success_no_retry(self) -> None:
        """Test that successful call returns immediately."""
        mock_func = MagicMock(return_value="success")
        decorated = with_retry(mock_func)

        result = decorated()

        assert result == "success"
        assert mock_func.call_count == 1

    def test_non_retryable_error_fails_immediately(self) -> None:
        """Test that non-retryable errors are raised without retry."""
        mock_func = MagicMock(side_effect=AuthenticationError("Invalid token"))
        decorated = with_retry(mock_func)

        with pytest.raises(AuthenticationError):
            decorated()

        assert mock_func.call_count == 1

    def test_retryable_error_eventually_succeeds(self) -> None:
        """Test that retryable errors are retried until success."""
        # First two calls fail, third succeeds
        mock_func = MagicMock(
            side_effect=[
                RateLimitError("Rate limit"),
                RateLimitError("Rate limit"),
                "success",
            ]
        )
        decorated = with_retry(mock_func)

        # Mock the wait to avoid actual delays
        with patch("ai_reviewer.utils.retry.wait_exponential") as mock_wait:
            mock_wait.return_value = lambda *args, **kwargs: 0  # No wait
            result = decorated()

        assert result == "success"
        assert mock_func.call_count == 3

    def test_retryable_error_exhausts_retries(self) -> None:
        """Test that retryable errors eventually exhaust retries."""
        mock_func = MagicMock(side_effect=ServerError("Server error"))
        decorated = with_retry(mock_func)

        # Mock the wait to avoid actual delays
        with patch("ai_reviewer.utils.retry.wait_exponential") as mock_wait:
            mock_wait.return_value = lambda *args, **kwargs: 0  # No wait
            with pytest.raises(ServerError):
                decorated()

        # Should have tried MAX_ATTEMPTS times
        assert mock_func.call_count == 5  # MAX_ATTEMPTS = 5
