# Epic: Polish & UX

## 🔙 Контекст

Discovery Engine працює (Phase 1), review prompt адаптивний (Phase 2), код чистий (Phase 3).
Залишилось: надійність (timeout, types), видимість для користувача (CLI), документація.

## 🎯 Мета

1. Discovery надійний навіть у edge cases (timeout, type safety)
2. Користувач може запустити Discovery standalone і побачити результат
3. Документація відповідає коду

## Tasks

| Task | Опис | Estimate |
|------|------|----------|
| 4.1 Reliability | Timeout + type fixes + conftest.py | 1h |
| 4.2 Discover CLI | `ai-review discover` standalone | 1-1.5h |
| 4.3 Docs + Gate | Фінальна синхронізація документації | 30min |

## Review Gate (фінальний)

- [ ] `make check` passes — zero warnings
- [ ] `ai-review discover` виводить три зони
- [ ] Discovery timeout працює (30s default)
- [ ] conftest.py з shared fixtures
- [ ] Docs відповідають коду
- [ ] Sprint DONE → ready for v1.0.0b1
