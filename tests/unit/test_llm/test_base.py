"""Unit tests for LLMProvider ABC and LLMResponse model."""

from __future__ import annotations

import pytest
from pydantic import BaseModel, ValidationError

from ai_reviewer.llm.base import LLMProvider, LLMResponse


class _DummySchema(BaseModel):
    """Minimal Pydantic model for testing generic responses."""

    value: str


class TestLLMResponse:
    """Tests for the LLMResponse generic model."""

    def test_create_with_string_content(self) -> None:
        """Test creating LLMResponse with raw text content."""
        resp: LLMResponse[str] = LLMResponse(content="hello")
        assert resp.content == "hello"
        assert resp.prompt_tokens == 0
        assert resp.completion_tokens == 0
        assert resp.total_tokens == 0
        assert resp.model_name == ""
        assert resp.latency_ms == 0
        assert resp.estimated_cost_usd == 0.0

    def test_create_with_model_content(self) -> None:
        """Test creating LLMResponse with a Pydantic model as content."""
        schema = _DummySchema(value="test")
        resp: LLMResponse[_DummySchema] = LLMResponse(
            content=schema,
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            model_name="test-model",
            latency_ms=42,
            estimated_cost_usd=0.001,
        )
        assert resp.content == schema
        assert resp.prompt_tokens == 100
        assert resp.completion_tokens == 50
        assert resp.total_tokens == 150
        assert resp.model_name == "test-model"
        assert resp.latency_ms == 42
        assert resp.estimated_cost_usd == pytest.approx(0.001)

    def test_frozen(self) -> None:
        """Test that LLMResponse is immutable."""
        resp = LLMResponse(content="hello")
        with pytest.raises(ValidationError):
            resp.content = "modified"  # type: ignore[misc]

    def test_negative_tokens_rejected(self) -> None:
        """Test that negative token counts are rejected."""
        with pytest.raises(ValidationError):
            LLMResponse(content="hello", prompt_tokens=-1)

    def test_negative_cost_rejected(self) -> None:
        """Test that negative cost is rejected."""
        with pytest.raises(ValidationError):
            LLMResponse(content="hello", estimated_cost_usd=-0.01)

    def test_serialization_roundtrip(self) -> None:
        """Test JSON serialization and deserialization."""
        resp = LLMResponse(
            content="test",
            prompt_tokens=10,
            model_name="m",
        )
        data = resp.model_dump()
        assert data["content"] == "test"
        assert data["prompt_tokens"] == 10
        assert data["model_name"] == "m"


class TestLLMProviderABC:
    """Tests for the LLMProvider abstract base class."""

    def test_cannot_instantiate(self) -> None:
        """Test that LLMProvider cannot be instantiated directly."""
        with pytest.raises(TypeError, match="abstract"):
            LLMProvider()  # type: ignore[abstract]

    def test_subclass_must_implement_generate(self) -> None:
        """Test that concrete subclass without generate() cannot be instantiated."""

        class _Incomplete(LLMProvider):
            pass

        with pytest.raises(TypeError, match="abstract"):
            _Incomplete()  # type: ignore[abstract]

    def test_concrete_subclass_works(self) -> None:
        """Test that a fully implemented subclass can be instantiated."""

        class _Concrete(LLMProvider):
            @property
            def model_name(self) -> str:
                return "test-model"

            def generate(  # type: ignore[override]
                self,
                prompt: str,
                *,
                system_prompt: str | None = None,
                response_schema: type | None = None,
                temperature: float = 0.0,
            ) -> LLMResponse:  # type: ignore[type-arg]
                return LLMResponse(content="stub")

        provider = _Concrete()
        resp = provider.generate("hello")
        assert resp.content == "stub"
