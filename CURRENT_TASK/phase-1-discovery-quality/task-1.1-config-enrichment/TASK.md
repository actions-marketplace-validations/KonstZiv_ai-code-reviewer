# Task 1.1: Config-Based Profile Enrichment

## Тип: Feature Enhancement
## Пріоритет: CRITICAL
## Estimate: 2-3h

## Опис

`_build_profile_deterministic()` в `orchestrator.py` отримує зібрані config файли (`_configs` параметр з underscore = unused) але ігнорує їх. Потрібно парсити configs для витягування:

1. **Framework** з dependencies (pyproject.toml → Django/FastAPI, package.json → React/Next.js)
2. **Layout** з file tree (наявність `src/`, monorepo patterns)
3. **Conventions** з config rules (ruff line-length, mypy strict mode, eslint rules)

## Acceptance Criteria

- [ ] Python проєкт з Django в pyproject.toml → `framework: "Django"`
- [ ] JS проєкт з React в package.json → `framework: "React"`
- [ ] Проєкт з `src/` → `layout: "src"`
- [ ] Проєкт з ruff config → conventions містить key rules
- [ ] Deterministic path виробляє такий самий або кращий результат ніж LLM path
- [ ] Existing tests не broken
- [ ] Нові unit tests для config parsing

## Блокує

- Task 4.1 (Discover CLI) — CLI показує результати Discovery, вони мають бути якісними
- Task 4.2 (Verbose mode) — discovery comment містить framework info

## Залежності

- Немає (самостійна таска)
