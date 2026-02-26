# Task 4.1: Test Fixtures — Implementation Guide

## ⚠️ Revision Note (Phase 3 → Phase 4)

Phase 3 integration + review feedback produced **27 integration tests** that
cover reviewer, E2E, prompts, and discovery comment edge cases. These were
committed in `7eef823` on branch `103-task-41-test-fixtures`.

**Already covered:**
- `_run_discovery` unit tests (success, fail-open, settings, wiring)
- `_post_discovery_comment` unit tests (post/skip/silent/fail-open/language)
- E2E with `discovery_enabled=True` (5 scenarios)
- `build_review_prompt` with `ProjectProfile` injection (3 tests)
- Discovery comment formatting edge cases (8 tests)

**Remaining scope:** realistic fixture-based integration tests through
`DiscoveryOrchestrator.discover()` with mock providers.

---

## Структура

```
tests/fixtures/discovery/
├── modern_python/
│   ├── .github/workflows/ci.yml
│   ├── pyproject.toml
│   └── expected_profile.json
├── legacy_python/
│   ├── setup.cfg
│   ├── tox.ini
│   ├── Makefile
│   └── expected_profile.json
├── javascript/
│   ├── .github/workflows/ci.yml
│   ├── package.json
│   ├── .eslintrc.json
│   └── expected_profile.json
├── go_gitlab/
│   ├── .gitlab-ci.yml
│   ├── go.mod
│   ├── .golangci.yml
│   └── expected_profile.json
├── empty/
│   ├── README.md
│   └── expected_profile.json
└── with_reviewbot_md/
    ├── .reviewbot.md
    └── expected_profile.json
```

## Тест-підхід

Mock `RepositoryProvider` повертає файли з fixture directory.
Mock `LLMProvider` повертає заздалегідь визначені відповіді.
Порівняти `discover()` output з `expected_profile.json`.

**Нюанси з Фази 3:**
- Mock `_run_discovery` для E2E, `DiscoveryOrchestrator` для fixture-level
- Fixture тести мають включати перевірку `language` параметра
- Використовувати `BOT_NAME` константу з `core/config.py` в assertions

---

## Чеклист

- [x] Integration tests через mock providers (27 тестів — Phase 3 revision)
- [x] 6 fixture directories
- [x] Expected profiles для кожного
- [x] Fixture-based `discover()` integration tests (6 tests in `test_discovery_fixtures.py`)
- [x] `make check` проходить
