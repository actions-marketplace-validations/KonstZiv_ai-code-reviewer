# Epic: Discovery Quality

## 🔙 Контекст (результати Beta-0)

Discovery pipeline працює: 4 layers, graceful degradation, fail-open integration.
Але Layer 2 (configs) **збирає** файли і **нічого з ними не робить** у deterministic path.
Це означає що для 80% проєктів (де CI має ≥2 tools) Discovery видає:
- `framework: None`
- `layout: None`
- `guidance.conventions: ()`

Користувач отримує review без контексту проєкту, хоча pyproject.toml/package.json вже прочитані.

## 🎯 Мета

Discovery видає корисний `ProjectProfile` для **кожного** проєкту:
- Framework з dependencies (Django, FastAPI, React, Next.js, Gin, etc.)
- Layout з file tree (src, flat, monorepo)
- Conventions з config rules (ruff: line-length, mypy: strict, etc.)

## Tasks

| Task | Опис | Estimate | Залежності |
|------|------|----------|------------|
| 1.1 Config Enrichment | Парсити configs → framework, layout, conventions | 2-3h | — |
| 1.2 Go Modules | Detect `go modules` в CI analyzer | 30min | — |
| 1.3 File Tree Truncation | Flag + handling для truncated trees | 30min | — |

## Вплив на користувача

**До:** "Stack: Python" → review без контексту
**Після:** "Stack: Python (Django) 3.13, uv, layout: src" → review знає що перевіряти

## Review Gate

Після завершення Phase 1 перевірити:
- [ ] `_build_profile_deterministic()` заповнює framework, layout, conventions
- [ ] `to_prompt_context()` включає нові дані
- [ ] Test fixtures оновлені (expected_profile.json)
- [ ] `make check` passes

## 🔮 Як це використає Beta-1

Framework detection → framework-specific review hints:
- Django: check migrations, verify admin registration, validate ORM queries
- FastAPI: validate response models, check dependency injection
- React: check hook rules, verify key props
