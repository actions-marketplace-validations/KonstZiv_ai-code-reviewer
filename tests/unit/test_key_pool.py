"""Unit tests for KeyPool and RotatingGeminiProvider."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from ai_reviewer.llm.base import LLMResponse
from ai_reviewer.llm.key_pool import KeyPool, RotatingGeminiProvider, _mask_key
from ai_reviewer.utils.retry import (
    AuthenticationError,
    QuotaExhaustedError,
    RateLimitError,
    ServerError,
)


class TestMaskKey:
    """Tests for _mask_key helper."""

    def test_normal_key(self) -> None:
        """Test masking a normal-length key."""
        assert _mask_key("AIzaSyD1234567890") == "...7890"

    def test_short_key(self) -> None:
        """Test masking a key shorter than 4 characters."""
        assert _mask_key("ab") == "...ab"

    def test_exactly_four_chars(self) -> None:
        """Test masking a key with exactly 4 characters."""
        assert _mask_key("abcd") == "...abcd"

    def test_single_char(self) -> None:
        """Test masking a single character key."""
        assert _mask_key("x") == "...x"


class TestKeyPool:
    """Tests for KeyPool class."""

    def test_empty_raises(self) -> None:
        """Test that empty key list raises ValueError."""
        with pytest.raises(ValueError, match="at least one"):
            KeyPool([])

    def test_single_key(self) -> None:
        """Test pool with a single key."""
        pool = KeyPool(["key1"])
        assert pool.size == 1
        assert list(pool) == ["key1"]

    def test_multi_key_iteration(self) -> None:
        """Test that iteration yields all keys in order."""
        pool = KeyPool(["key1", "key2", "key3"])
        assert pool.size == 3
        assert list(pool) == ["key1", "key2", "key3"]

    def test_repeated_iteration(self) -> None:
        """Test that pool can be iterated multiple times."""
        pool = KeyPool(["a", "b"])
        assert list(pool) == ["a", "b"]
        assert list(pool) == ["a", "b"]

    def test_size_property(self) -> None:
        """Test size property returns correct count."""
        assert KeyPool(["a"]).size == 1
        assert KeyPool(["a", "b", "c"]).size == 3


class TestRotatingGeminiProvider:
    """Tests for RotatingGeminiProvider."""

    def test_model_name_property(self) -> None:
        """Test model_name property returns the configured model."""
        pool = KeyPool(["key1"])
        provider = RotatingGeminiProvider(key_pool=pool, model_name="gemini-test")
        assert provider.model_name == "gemini-test"

    @patch("ai_reviewer.llm.key_pool.GeminiProvider")
    def test_single_key_success(self, mock_provider_cls: Mock) -> None:
        """Test successful generation with a single key."""
        expected = LLMResponse(content="OK", model_name="gemini-test")
        mock_provider_cls.return_value.generate.return_value = expected

        pool = KeyPool(["key1"])
        provider = RotatingGeminiProvider(key_pool=pool, model_name="gemini-test")

        result = provider.generate("prompt")

        assert result.content == "OK"
        mock_provider_cls.assert_called_once_with(api_key="key1", model_name="gemini-test")

    @patch("ai_reviewer.llm.key_pool.GeminiProvider")
    def test_rotation_on_quota_exhausted(self, mock_provider_cls: Mock) -> None:
        """Test key rotation when first key hits quota exhaustion."""
        expected = LLMResponse(content="OK", model_name="gemini-test")

        provider1 = Mock()
        provider1.generate.side_effect = QuotaExhaustedError("quota exceeded")
        provider2 = Mock()
        provider2.generate.return_value = expected

        mock_provider_cls.side_effect = [provider1, provider2]

        pool = KeyPool(["key1", "key2"])
        rotating = RotatingGeminiProvider(key_pool=pool, model_name="gemini-test")

        result = rotating.generate("prompt")

        assert result.content == "OK"
        assert mock_provider_cls.call_count == 2

    @patch("ai_reviewer.llm.key_pool.GeminiProvider")
    def test_rotation_on_auth_error(self, mock_provider_cls: Mock) -> None:
        """Test key rotation when first key has authentication error."""
        expected = LLMResponse(content="OK", model_name="gemini-test")

        provider1 = Mock()
        provider1.generate.side_effect = AuthenticationError("bad key")
        provider2 = Mock()
        provider2.generate.return_value = expected

        mock_provider_cls.side_effect = [provider1, provider2]

        pool = KeyPool(["bad-key", "good-key"])
        rotating = RotatingGeminiProvider(key_pool=pool, model_name="gemini-test")

        result = rotating.generate("prompt")

        assert result.content == "OK"

    @patch("ai_reviewer.llm.key_pool.GeminiProvider")
    def test_rotation_on_rate_limit(self, mock_provider_cls: Mock) -> None:
        """Test key rotation when first key hits rate limit."""
        expected = LLMResponse(content="OK", model_name="gemini-test")

        provider1 = Mock()
        provider1.generate.side_effect = RateLimitError("429")
        provider2 = Mock()
        provider2.generate.return_value = expected

        mock_provider_cls.side_effect = [provider1, provider2]

        pool = KeyPool(["key1", "key2"])
        rotating = RotatingGeminiProvider(key_pool=pool, model_name="gemini-test")

        result = rotating.generate("prompt")

        assert result.content == "OK"

    @patch("ai_reviewer.llm.key_pool.GeminiProvider")
    def test_rotation_on_server_error(self, mock_provider_cls: Mock) -> None:
        """Test key rotation when first key hits server error."""
        expected = LLMResponse(content="OK", model_name="gemini-test")

        provider1 = Mock()
        provider1.generate.side_effect = ServerError("503")
        provider2 = Mock()
        provider2.generate.return_value = expected

        mock_provider_cls.side_effect = [provider1, provider2]

        pool = KeyPool(["key1", "key2"])
        rotating = RotatingGeminiProvider(key_pool=pool, model_name="gemini-test")

        result = rotating.generate("prompt")

        assert result.content == "OK"

    @patch("ai_reviewer.llm.key_pool.GeminiProvider")
    def test_all_keys_exhausted_raises_last_error(self, mock_provider_cls: Mock) -> None:
        """Test that last error is raised when all keys fail."""
        provider1 = Mock()
        provider1.generate.side_effect = QuotaExhaustedError("quota 1")
        provider2 = Mock()
        provider2.generate.side_effect = RateLimitError("rate limit 2")

        mock_provider_cls.side_effect = [provider1, provider2]

        pool = KeyPool(["key1", "key2"])
        rotating = RotatingGeminiProvider(key_pool=pool, model_name="gemini-test")

        with pytest.raises(RateLimitError, match="rate limit 2"):
            rotating.generate("prompt")

    @patch("ai_reviewer.llm.key_pool.GeminiProvider")
    def test_non_rotatable_error_propagates(self, mock_provider_cls: Mock) -> None:
        """Test that non-rotatable errors propagate immediately."""
        provider1 = Mock()
        provider1.generate.side_effect = ValueError("parse error")

        mock_provider_cls.side_effect = [provider1]

        pool = KeyPool(["key1", "key2"])
        rotating = RotatingGeminiProvider(key_pool=pool, model_name="gemini-test")

        with pytest.raises(ValueError, match="parse error"):
            rotating.generate("prompt")

        # Only one provider was created (didn't rotate)
        assert mock_provider_cls.call_count == 1

    @patch("ai_reviewer.llm.key_pool.GeminiProvider")
    def test_passes_kwargs_to_generate(self, mock_provider_cls: Mock) -> None:
        """Test that generate kwargs are forwarded to inner provider."""
        expected = LLMResponse(content="OK", model_name="gemini-test")
        mock_provider_cls.return_value.generate.return_value = expected

        pool = KeyPool(["key1"])
        rotating = RotatingGeminiProvider(key_pool=pool, model_name="gemini-test")

        rotating.generate("prompt", system_prompt="sys", temperature=0.5)

        mock_provider_cls.return_value.generate.assert_called_once_with(
            "prompt",
            system_prompt="sys",
            response_schema=None,
            temperature=0.5,
        )
