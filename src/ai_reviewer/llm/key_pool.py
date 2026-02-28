"""Multi-key rotation pool for Google API keys.

Provides round-robin key rotation with automatic fallback when individual
keys hit rate limits or quota exhaustion.  Each key is tried with full
``@with_retry`` logic (3 attempts) before the pool moves to the next key.

Typical usage::

    pool = KeyPool(settings.google_api_keys)
    provider = RotatingGeminiProvider(key_pool=pool, model_name="gemini-2.5-flash")
    response = provider.generate(prompt, response_schema=ReviewResult)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, overload

from pydantic import BaseModel

from ai_reviewer.llm.base import LLMProvider
from ai_reviewer.llm.gemini import GeminiProvider
from ai_reviewer.utils.retry import (
    AuthenticationError,
    QuotaExhaustedError,
    RateLimitError,
    ServerError,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from ai_reviewer.llm.base import LLMResponse

logger = logging.getLogger(__name__)


def _mask_key(key: str) -> str:
    """Mask an API key for safe logging, showing only the last 4 characters.

    Args:
        key: The API key to mask.

    Returns:
        Masked string like ``...XXXX``.

    Examples:
        >>> _mask_key("AIzaSyD1234567890")
        '...7890'
        >>> _mask_key("ab")
        '...ab'
    """
    suffix_len = min(4, len(key))
    return f"...{key[-suffix_len:]}"


class KeyPool:
    """Round-robin pool of API keys.

    Each call to ``__iter__`` yields every key exactly once, starting from
    the first key.  The pool is stateless — iteration order is always the
    same, and callers decide when to advance to the next key.

    Args:
        keys: Non-empty list of API key strings.

    Raises:
        ValueError: If *keys* is empty.
    """

    def __init__(self, keys: list[str]) -> None:
        if not keys:
            msg = "KeyPool requires at least one API key"
            raise ValueError(msg)
        self._keys = list(keys)

    @property
    def size(self) -> int:
        """Return the number of keys in the pool."""
        return len(self._keys)

    def __iter__(self) -> Iterator[str]:
        """Yield each key exactly once."""
        yield from self._keys


# Errors that should trigger key rotation (after per-key retries exhaust).
_ROTATABLE_ERRORS = (QuotaExhaustedError, AuthenticationError, RateLimitError, ServerError)


class RotatingGeminiProvider(LLMProvider):
    """LLM provider that rotates through multiple API keys on failure.

    For each key the underlying ``GeminiProvider`` (which has ``@with_retry``)
    is allowed to exhaust its retry budget.  If it still fails with a
    rotatable error, the next key is tried.  When all keys are exhausted
    the last error is re-raised.

    Args:
        key_pool: Pool of API keys to rotate through.
        model_name: Gemini model identifier.
    """

    def __init__(self, key_pool: KeyPool, model_name: str) -> None:
        self._key_pool = key_pool
        self._model_name = model_name

    @property
    def model_name(self) -> str:
        """Return the Gemini model identifier."""
        return self._model_name

    @overload
    def generate[T: BaseModel](
        self,
        prompt: str,
        *,
        system_prompt: str | None = ...,
        response_schema: type[T],
        temperature: float = ...,
    ) -> LLMResponse[T]: ...

    @overload
    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = ...,
        response_schema: None = ...,
        temperature: float = ...,
    ) -> LLMResponse[str]: ...

    def generate[T: BaseModel](
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        response_schema: type[T] | None = None,
        temperature: float = 0.0,
    ) -> LLMResponse[T] | LLMResponse[str]:
        """Send a prompt to Gemini, rotating keys on rotatable errors.

        Args:
            prompt: User prompt text.
            system_prompt: Optional system instruction.
            response_schema: Pydantic model for structured JSON output.
            temperature: Sampling temperature (0.0 = deterministic).

        Returns:
            LLMResponse with parsed content or raw text.

        Raises:
            AuthenticationError: If all keys fail with auth errors.
            RateLimitError: If all keys are rate-limited.
            QuotaExhaustedError: If all keys are quota-exhausted.
            ServerError: If all keys hit server errors.
            ValueError: If structured response cannot be parsed.
        """
        last_error: Exception | None = None

        for key in self._key_pool:
            provider = GeminiProvider(api_key=key, model_name=self._model_name)
            try:
                return provider.generate(
                    prompt,
                    system_prompt=system_prompt,
                    response_schema=response_schema,
                    temperature=temperature,
                )
            except _ROTATABLE_ERRORS as exc:
                last_error = exc
                masked = _mask_key(key)
                logger.warning(
                    "Key %s failed on model %s (%s: %s), rotating to next key",
                    masked,
                    self._model_name,
                    type(exc).__name__,
                    str(exc)[:120],
                )

        # All keys exhausted — re-raise the last error
        assert last_error is not None  # guaranteed: pool is non-empty
        raise last_error


__all__ = [
    "KeyPool",
    "RotatingGeminiProvider",
    "_mask_key",
]
