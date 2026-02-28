"""LLM provider abstractions for AI Code Reviewer.

Public API:
    - ``LLMProvider`` — abstract base class for LLM backends.
    - ``LLMResponse`` — generic response wrapper with token/cost metrics.
    - ``KeyPool`` — round-robin pool of API keys.
    - ``RotatingGeminiProvider`` — Gemini provider with multi-key rotation.
"""

from ai_reviewer.llm.base import LLMProvider, LLMResponse
from ai_reviewer.llm.key_pool import KeyPool, RotatingGeminiProvider

__all__ = ["KeyPool", "LLMProvider", "LLMResponse", "RotatingGeminiProvider"]
