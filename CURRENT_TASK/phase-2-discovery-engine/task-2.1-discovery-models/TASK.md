# Task 2.1: Discovery Models

| Поле | Значення |
|------|----------|
| **Фаза** | 2 — Discovery Engine |
| **Оцінка** | 2-3 години |
| **Залежності** | Фаза 1 (RepositoryMetadata) |
| **Блокує** | 2.2, 2.3, 2.4, 2.5, 2.6 |
| **Файли** | `src/ai_reviewer/discovery/__init__.py`, `discovery/models.py` |

## Що робимо

Pydantic-моделі для всього Discovery pipeline: `PlatformData`, `CIInsights`,
`DetectedTool`, `AutomatedChecks`, `ReviewGuidance`, `Gap`, `ProjectProfile`.

## Навіщо

Всі інші задачі Фази 2 залежать від цих моделей.
`ProjectProfile` — центральний об'єкт який проходить через весь pipeline.

## Очікуваний результат

- `discovery/models.py` з ~15 моделями
- `ProjectProfile.to_prompt_context()` → compact text для review prompt
- Всі моделі: `frozen=True`, `tuple` замість `list`
- Тести: validation, serialization, prompt context

## Як перевірити

```bash
pytest tests/unit/test_discovery/test_models.py
```
