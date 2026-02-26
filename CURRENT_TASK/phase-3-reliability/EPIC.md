# Epic: Reliability & Testing

## 🔙 Контекст

Beta-0 review виявив: немає timeout на Discovery, немає shared test fixtures (дублювання mock setup), 5x `type: ignore` в orchestrator.

## 🎯 Мета

Discovery працює надійно: timeout захищає CI, тести DRY і maintainable, type safety повна.

## Tasks

| Task | Опис | Estimate |
|------|------|----------|
| 3.1 Discovery Timeout | Загальний timeout 30s на Discovery pipeline | 1h |
| 3.2 Shared Fixtures | `conftest.py` з mock providers і sample data | 1-1.5h |
| 3.3 Type Fixes | Прибрати `type: ignore` в `_merge_ci_insights` | 30min |

## Вплив на користувача

- **Timeout** — CI pipeline не зависне якщо GitHub API повільний
- **Shared fixtures** — прискорює розробку Beta-1 (менше boilerplate в тестах)
- **Type safety** — менше ризик regression від mypy

## Review Gate

Після Phase 3:
- [ ] Discovery з mock slow provider → завершується за ≤30s
- [ ] conftest.py імпортується у всіх test modules
- [ ] `mypy --strict` passes без `type: ignore`
- [ ] `make check` passes
