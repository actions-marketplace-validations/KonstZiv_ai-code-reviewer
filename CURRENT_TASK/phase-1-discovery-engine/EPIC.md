# Epic: Discovery Engine Redesign

## 🔙 Контекст (результати Beta-0)

Discovery pipeline працює: 4 layers, graceful degradation, fail-open.
Але є дві критичні проблеми:

1. **`_build_profile_deterministic()`** збирає configs і нічого з ними не робить
2. **CI analyzer** (457 рядків regex) — крихкий, обмежене покриття, не розуміє якість

### Архітектурний pivot

**Regex CI analysis → LLM як domain expert.**

Замість того щоб підтримувати regex для кожного нового CI tool,
один LLM-запит (~200 tokens) аналізує ВСЕ і повертає:
- Три зони уваги (well/not/weakly covered)
- Watch-files list (коли перезапускати)
- Framework + layout detection

## 🎯 Мета

Discovery розуміє проєкт і видає **actionable** результат:
не "Stack: Python", а "Django project, ruff+mypy+pytest in CI, SQL injection NOT covered".

## Tasks

| Task | Опис | Estimate | Залежності |
|------|------|----------|------------|
| 1.1 Raw Data Enrichment | Fix deterministic path + Go + truncation | 1.5-2h | — |
| 1.2 LLM Analysis Prompt | Один промпт → три зони + watch-files | 2-3h | 1.1 |
| 1.3 Watch-Files Caching | Зберігання + кеш механізм | 1-1.5h | 1.2 |
| 1.4 MR-Aware Discovery | Diff language + new deps + watch-files trigger | 1.5-2h | 1.2 |

Tasks 1.3 і 1.4 незалежні — можна паралелити після 1.2.

## Вплив на користувача

**До:**
```
## Project Context
- Languages: Python (95%), Shell (5%)
- CI: GitHub Actions
- Tools: ruff, pytest
```

**Після:**
```
## Project Context — Three Attention Zones

✅ Well covered (SKIP in review):
  - Code formatting (ruff --format enforced in CI)
  - Type checking (mypy --strict in CI)

❌ Not covered (FOCUS in review):
  - SQL injection prevention
  - Authentication/authorization patterns
  - Input validation

⚠️ Weakly covered (CHECK + recommend):
  - Testing exists (pytest) but no coverage threshold
  - Linting exists (ruff) but limited rule set

Framework: Django 5.1 | Layout: src | Package manager: uv
```

## Review Gate

Після Phase 1 перевірити:
- [ ] LLM prompt на fixture repo → три зони парсяться
- [ ] Watch-files list генерується
- [ ] Framework detection працює (Django з pyproject.toml)
- [ ] MR з SQL файлами → мова diff визначається як SQL
- [ ] Fallback працює (LLM недоступний → graceful degradation)
- [ ] `make check` passes

## 🔮 Як це використає Beta-1

- Three zones → framework-specific review hints (Django: check migrations)
- Watch-files → persistent storage між runs
- MR-aware → test coverage gap detection
