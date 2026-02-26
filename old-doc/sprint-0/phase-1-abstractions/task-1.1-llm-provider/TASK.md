# Task 1.1: LLMProvider ABC + GeminiProvider

| Поле | Значення |
|------|----------|
| **Фаза** | 1 — Abstractions |
| **Оцінка** | 3-4 години |
| **Залежності** | Немає |
| **Блокує** | 1.4, 2.5, 2.6, 3.2 |
| **Файли** | `src/ai_reviewer/llm/base.py`, `llm/gemini.py`, `llm/__init__.py` |

---

## Що робимо

Створюємо абстракцію для LLM-провайдера. Замість хардкодженого `GeminiClient`
що повертає тільки `ReviewResult` — generic інтерфейс `LLMProvider` з одним
методом `generate()`, який приймає будь-яку Pydantic schema.

## Навіщо

- Discovery потребує `generate(prompt, response_schema=ProjectProfile)`
- Review використовує `generate(prompt, response_schema=ReviewResult)`
- Beta-1 додасть fallback (Gemini → Claude)
- Beta-2 додасть Scout agent з іншою schema
- Один інтерфейс для всіх use cases

## Очікуваний результат

- `LLMProvider` ABC з методом `generate()`
- `LLMResponse[T]` — уніфікована відповідь (content, tokens, cost, latency)
- `GeminiProvider(LLMProvider)` — реалізація на google-genai
- Існуючий `analyze_code_changes()` делегує в `GeminiProvider` (зворотна сумісність)
- Unit-тести з mock google-genai

## Як перевірити

```bash
make check                  # нічого не зламано
pytest tests/unit/test_llm/ # нові тести проходять
```

Ручна перевірка: існуючий flow (CLI → Gemini → review) працює як раніше.

## Особливості

- `LLMResponse` має бути сумісна з існуючим `ReviewMetrics`
  (model_name, tokens, latency, cost)
- Pricing logic переноситься з `integrations/gemini.py` в `llm/gemini.py`
- Retry decorator `@with_retry` вже існує — використовувати його
