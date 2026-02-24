# Task 1.1: LLMProvider — Implementation Guide

## Поточний стан коду

```
src/ai_reviewer/
├── integrations/
│   └── gemini.py          # GeminiClient + analyze_code_changes()
├── llm/                   # ПУСТИЙ (тільки __init__.py)
└── core/
    └── models.py          # ReviewResult, ReviewMetrics
```

`integrations/gemini.py` (289 рядків) містить:
- `GeminiClient` — обгортка навколо `google.genai.Client`
- `generate_review()` — виклик з `response_schema=ReviewResult`, temp=0.0
- `GEMINI_PRICING` — dict з цінами per model
- Token tracking, cost calculation
- Error conversion: Google API errors → custom hierarchy
- `analyze_code_changes()` — точка входу (створює клієнт, будує prompt, викликає)

---

## Що створити

### 1. `src/ai_reviewer/llm/__init__.py`

```python
from ai_reviewer.llm.base import LLMProvider, LLMResponse

__all__ = ["LLMProvider", "LLMResponse"]
```

### 2. `src/ai_reviewer/llm/base.py`

```python
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T", bound=BaseModel)


class LLMResponse(BaseModel, Generic[T]):
    """Уніфікована відповідь від будь-якого LLM.

    Generic параметр T — тип parsed content (ReviewResult, ProjectProfile, etc.)
    Якщо response_schema не задана — content буде str.
    """
    model_config = ConfigDict(frozen=True)

    content: T | str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    model_name: str = ""
    latency_ms: int = 0
    estimated_cost_usd: float = 0.0


class LLMProvider(ABC):
    """Абстракція LLM-провайдера.

    Один метод generate() — prompt in, structured response out.
    Реалізації: GeminiProvider, (майбутні) ClaudeProvider, OpenAIProvider.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        response_schema: type[T] | None = None,
        temperature: float = 0.0,
    ) -> LLMResponse[T]:
        """Відправити prompt до LLM і отримати structured response.

        Args:
            prompt: User prompt.
            system_prompt: System instruction (optional).
            response_schema: Pydantic model для structured output.
                             Якщо None — повертає raw text.
            temperature: Sampling temperature (0.0 = deterministic).

        Returns:
            LLMResponse з parsed content або raw text.

        Raises:
            AuthenticationError: Invalid API key.
            RateLimitError: Rate limit exceeded (retryable).
            ServerError: Provider server error (retryable).
        """
        ...
```

### 3. `src/ai_reviewer/llm/gemini.py`

Витягнути з `integrations/gemini.py`:

```python
from __future__ import annotations

import logging
import time
from typing import TypeVar

from google import genai
from google.genai.types import GenerateContentConfig
from pydantic import BaseModel

from ai_reviewer.llm.base import LLMProvider, LLMResponse
from ai_reviewer.utils.retry import with_retry

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-3-flash-preview"

GEMINI_PRICING: dict[str, dict[str, float]] = {
    # Перенести з integrations/gemini.py
}


class GeminiProvider(LLMProvider):
    """LLM provider для Google Gemini."""

    def __init__(
        self,
        api_key: str,
        model_name: str = DEFAULT_MODEL,
    ) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model_name = model_name

    @with_retry
    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        response_schema: type[T] | None = None,
        temperature: float = 0.0,
    ) -> LLMResponse[T]:
        start = time.monotonic()

        config = GenerateContentConfig(
            temperature=temperature,
            response_mime_type="application/json" if response_schema else None,
            response_schema=response_schema,
        )
        if system_prompt:
            config.system_instruction = system_prompt

        try:
            response = self._client.models.generate_content(
                model=self._model_name,
                contents=prompt,
                config=config,
            )
        except Exception as e:
            raise _convert_google_exception(e) from e

        latency_ms = int((time.monotonic() - start) * 1000)

        # Parse content
        content = self._parse_response(response, response_schema)

        # Token usage
        usage = response.usage_metadata
        prompt_tokens = usage.prompt_token_count or 0
        completion_tokens = usage.candidates_token_count or 0

        return LLMResponse(
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            model_name=self._model_name,
            latency_ms=latency_ms,
            estimated_cost_usd=self._estimate_cost(prompt_tokens, completion_tokens),
        )

    def _parse_response(self, response, schema):
        """Parse response — structured або raw text."""
        text = response.text
        if schema is None:
            return text
        return schema.model_validate_json(text)

    def _estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        pricing = GEMINI_PRICING.get(self._model_name, {})
        input_cost = (prompt_tokens / 1_000_000) * pricing.get("input", 0)
        output_cost = (completion_tokens / 1_000_000) * pricing.get("output", 0)
        return input_cost + output_cost
```

**ВАЖЛИВО:** `_convert_google_exception()` — перенести з `integrations/gemini.py`.

### 4. Оновити `integrations/gemini.py`

Зробити тонкою обгорткою для зворотної сумісності:

```python
# integrations/gemini.py — ПІСЛЯ рефакторингу

from ai_reviewer.llm.gemini import GeminiProvider
from ai_reviewer.integrations.prompts import SYSTEM_PROMPT, build_review_prompt
from ai_reviewer.core.models import ReviewResult


def analyze_code_changes(context, settings):
    """Legacy entry point — delegates to GeminiProvider."""
    provider = GeminiProvider(
        api_key=settings.google_api_key,
        model_name=settings.gemini_model,
    )
    prompt = build_review_prompt(context, settings)
    response = provider.generate(
        prompt,
        system_prompt=SYSTEM_PROMPT,
        response_schema=ReviewResult,
    )

    # Map LLMResponse to ReviewResult + ReviewMetrics for compatibility
    result = response.content
    # Attach metrics...
    return result
```

Це зберігає API для `reviewer.py` який викликає `analyze_code_changes()`.

---

## Тести

### `tests/unit/test_llm/test_base.py`

- `LLMResponse` model creation, frozen, serialization
- `LLMProvider` is abstract (cannot instantiate)

### `tests/unit/test_llm/test_gemini.py`

- Mock `google.genai.Client`
- `generate()` з `response_schema` → повертає parsed model
- `generate()` без schema → повертає raw text
- Token counting і cost estimation
- Error conversion: Google errors → custom hierarchy
- Retry на RateLimitError, ServerError

---

## Чеклист

- [ ] `llm/base.py` — LLMProvider ABC, LLMResponse model
- [ ] `llm/gemini.py` — GeminiProvider з retry, pricing, error conversion
- [ ] `llm/__init__.py` — public exports
- [ ] `integrations/gemini.py` — тонка обгортка (зворотна сумісність)
- [ ] Unit-тести
- [ ] `make check` проходить
- [ ] `reviewer.py` → `analyze_code_changes()` працює як раніше
