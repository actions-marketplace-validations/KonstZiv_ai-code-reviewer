# Task 4.1: Test Fixtures — Implementation Guide

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

---

## Чеклист

- [ ] 6 fixture directories
- [ ] Expected profiles для кожного
- [ ] Integration tests через mock providers
- [ ] `make check` проходить
