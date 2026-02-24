# Task 2.6: DiscoveryOrchestrator

| Поле | Значення |
|------|----------|
| **Фаза** | 2 — Discovery Engine |
| **Оцінка** | 5-7 годин |
| **Залежності** | 2.1-2.5, Фаза 1 (всі ABCs) |
| **Блокує** | 3.2, 3.3 |
| **Файли** | `src/ai_reviewer/discovery/orchestrator.py` |

## Що робимо

Головний клас Discovery — зв'язує всі компоненти в 4-layer pipeline
з graceful degradation і діалогом.

## Навіщо

Це "мозок" Discovery. Вирішує: чи потрібен LLM? Які питання ставити?
Чи є відповіді на попередні питання?

## Очікуваний результат

- `DiscoveryOrchestrator(repo_provider, conversation, llm)`
- `discover(repo_name, mr_id) -> ProjectProfile`
- 4 сценарії: повний стек, без CI, без конфігів, з відповідями
- Graceful degradation: кожен layer може fail → continue

## Як перевірити

```bash
pytest tests/unit/test_discovery/test_orchestrator.py
```

4 тест-сценарії з mock providers.
