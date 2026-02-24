# Task 2.5: Discovery LLM Prompts

| Поле | Значення |
|------|----------|
| **Фаза** | 2 — Discovery Engine |
| **Оцінка** | 2-3 години |
| **Залежності** | 2.1 (models) |
| **Блокує** | 2.6 |
| **Файли** | `src/ai_reviewer/discovery/prompts.py` |

## Що робимо

System prompt і user prompt для LLM interpretation — Layer 3 Discovery.
Використовується ТІЛЬКИ коли детерміністичних даних недостатньо.

## Очікуваний результат

- `DISCOVERY_SYSTEM_PROMPT` — роль "interpret project setup"
- `build_interpretation_prompt()` — compact prompt з platform data, CI, configs
- `LLMDiscoveryResponse` model — що LLM заповнює
