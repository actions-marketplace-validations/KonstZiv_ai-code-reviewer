# Task 4.1: Test Fixtures

| Поле | Значення |
|------|----------|
| **Фаза** | 4 — Polish |
| **Оцінка** | 3-4 години |
| **Файли** | `tests/fixtures/`, `tests/unit/test_discovery/` |

## Що робимо

Реалістичні тест-сценарії для Discovery на різних типах проєктів.

## Fixtures

1. **Modern Python** — pyproject.toml + ruff + mypy + pytest + GH Actions + uv
2. **Legacy Python** — setup.cfg + flake8 + tox.ini, no CI
3. **JS/TS** — package.json + eslint + jest + GH Actions + npm
4. **Go** — go.mod + golangci-lint + GitLab CI
5. **Empty/minimal** — тільки README
6. **With .reviewbot.md** — skip discovery
