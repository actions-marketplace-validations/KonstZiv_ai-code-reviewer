# Sprint Beta-0.5: Pre-release Polish

## Навігація

```
sprint-beta-0.5/
├── SPRINT.md                          ← ви тут
├── REVIEW_GATE.md                     Обов'язковий чеклист між фазами
├── phase-1-discovery-quality/         Фаза 1: Discovery Quality (3-4h)
│   ├── EPIC.md
│   ├── task-1.1-config-enrichment/    Config → framework, layout, conventions
│   ├── task-1.2-go-modules/           Go modules detection в CI analyzer
│   └── task-1.3-file-tree-truncation/ Truncation flag + handling
├── phase-2-housekeeping/              Фаза 2: Housekeeping & Safety (1.5-2h)
│   ├── EPIC.md
│   ├── task-2.1-dead-deps/            Видалити langchain/anthropic/openai
│   ├── task-2.2-env-cleanup/          Почистити .env.example + action.yml
│   ├── task-2.3-roadmap-fix/          ROADMAP.md → root
│   └── task-2.4-raw-yaml-sanitize/    Прибрати raw_yaml з CIInsights
├── phase-3-reliability/               Фаза 3: Reliability & Testing (2-3h)
│   ├── EPIC.md
│   ├── task-3.1-discovery-timeout/    Загальний timeout на Discovery pipeline
│   ├── task-3.2-shared-fixtures/      conftest.py з shared mock fixtures
│   └── task-3.3-type-fixes/           Прибрати type: ignore в orchestrator
└── phase-4-user-experience/           Фаза 4: User Experience (2-3h)
    ├── EPIC.md
    ├── task-4.1-discover-cli/         `ai-review discover` standalone command
    ├── task-4.2-verbose-mode/         Опція always-post discovery comment
    └── task-4.3-review-gate-docs/     Фінальна синхронізація документації
```

---

## 🔙 Де ми зараз (після Beta-0)

### Що зроблено

- **3 ABCs**: `LLMProvider`, `RepositoryProvider`, `ConversationProvider` — працюють
- **Triple inheritance**: `GitHubClient` і `GitLabClient` реалізують усі 3 інтерфейси
- **Discovery pipeline**: 4-layer (Platform API → CI → Configs → LLM), graceful degradation
- **ConversationProvider**: `BotQuestion` з `question_id` + `default_assumption`, markdown format
- **Integration**: Discovery → review prompt (`## Project Context`), fail-open
- **Tests**: 30 файлів, 12K рядків, 6 fixture scenarios
- **Docs**: Discovery page (5 мов), README updated, `.reviewbot.md` example

### Що НЕ працює як треба

| Проблема | Вплив на користувача |
|----------|---------------------|
| `_build_profile_deterministic()` ігнорує configs | **80% проєктів**: framework не визначається, conventions порожні. Бот не знає що проєкт на Django/FastAPI навіть коли pyproject.toml зібраний |
| `all-providers` optional deps: langchain, anthropic, openai | Docker image +50MB, misleading для користувачів |
| `.env.example` містить `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` | Користувач думає що ці providers підтримуються |
| `ROADMAP.md` — broken link у README | README посилається на файл якого немає |
| `raw_yaml` в `CIInsights` | CI файли з secrets потрапляють у Pydantic repr |
| Немає timeout на Discovery | CI може чекати 60+ секунд |
| Go modules не детектуються | Go-проєкти отримують `package_manager: null` |
| Немає standalone discovery mode | Користувач не може протестувати Discovery без MR |
| `file_tree` truncation — silent | Monorepo: пропускаються CI файли без попередження |

### Артефакти з Beta-0

| Документ | Зміст |
|----------|-------|
| sprint-beta-0-review.md | Повний аудит: безпека, якість, надійність, відповідність |
| sprint-beta-0-after-review.md | Backlog з code review (Go modules) |
| CURRENT_TASK/ | Повна sprint документація (37 файлів) |

---

## 🎯 Мета спринту

**Витиснути максимум користі з написаного коду і підготуватись до публікації.**

Після Sprint Beta-0.5:

1. Discovery **реально покращує review** для Python/JS/Go/Rust проєктів — framework detection, conventions, layout
2. Користувач може **запустити `ai-review discover`** і побачити що бот дізнався про проєкт
3. Код чистий: немає dead deps, broken links, security concerns
4. **`make check` passes** — ready for v1.0.0b1 tag
5. Тести надійні: shared fixtures, edge cases покриті, type-safe

### Що отримує користувач

| До Beta-0.5 | Після Beta-0.5 |
|-------------|----------------|
| Бот знає мову і CI tools, але не framework | Бот знає Django/FastAPI/React/Next.js з pyproject.toml/package.json |
| Discovery comment тільки при gaps | Опція `discovery_verbose=true` для завжди-видимого аналізу |
| Тестувати Discovery тільки через MR | `ai-review discover owner/repo` — standalone перевірка |
| Conventions порожні для 80% проєктів | Conventions з config rules (ruff, mypy, eslint) |
| Немає info про layout | `src`, `flat`, `monorepo` визначається з file tree |

---

## Фази

### Фаза 1: Discovery Quality (3-4h) ⭐ Найбільший вплив

**Мета:** Discovery дає корисні дані для КОЖНОГО review, а не тільки для проєктів без CI.

- **1.1** Config-based enrichment: framework + layout + conventions з зібраних configs
- **1.2** Go modules detection в CI analyzer
- **1.3** File tree truncation flag і handling

**Чому першою:** Це foundation. Tasks 4.1 (CLI) і 4.2 (verbose) показують результати Discovery — вони мають бути якісними.

### Фаза 2: Housekeeping & Safety (1.5-2h)

**Мета:** Чистий, безпечний, не misleading codebase.

- **2.1** Видалити `all-providers` optional deps + порожній `agents/`
- **2.2** Почистити `.env.example`
- **2.3** Повернути `ROADMAP.md`
- **2.4** Прибрати `raw_yaml` з `CIInsights`

### Фаза 3: Reliability & Testing (2-3h)

**Мета:** Discovery працює надійно навіть у edge cases.

- **3.1** Timeout на Discovery pipeline (30s default)
- **3.2** `conftest.py` з shared fixtures
- **3.3** Прибрати `type: ignore` в orchestrator

### Фаза 4: User Experience (2-3h) ⭐ Найбільший wow-фактор

**Мета:** Користувач може побачити і контролювати Discovery.

- **4.1** `ai-review discover` CLI command — standalone discovery
- **4.2** `discovery_verbose` mode — always-post discovery comment
- **4.3** Review gate: `make check`, documentation sync, final verification

---

## Загальний обсяг

| Фаза | Estimate | Tasks |
|-------|----------|-------|
| Phase 1: Discovery Quality | 3-4h | 3 |
| Phase 2: Housekeeping | 1.5-2h | 4 |
| Phase 3: Reliability | 2-3h | 3 |
| Phase 4: User Experience | 2-3h | 3 |
| **Total** | **8.5-12h** | **13** |

---

## 🔮 Що далі (Beta-1)

Sprint Beta-0.5 закладає foundation для Beta-1:

- **Config enrichment (1.1)** → Beta-1: framework-specific review hints (Django: check migrations, FastAPI: validate response models)
- **Discover CLI (4.1)** → Beta-1: `ai-review discover --generate-config` для bootstrap `.reviewbot.md`
- **Verbose mode (4.2)** → Beta-1: usage footer у review comment (tokens, cost, discovery status)
- **Shared fixtures (3.2)** → Beta-1: швидше писати тести для нових фіч

---

## Definition of Done

- [ ] `make check` passes (lint + test) — zero warnings
- [ ] Discovery на Python проєкті з CI → знає framework, conventions
- [ ] Discovery на JS/Go проєкті → знає framework, package manager
- [ ] `ai-review discover owner/repo` → виводить ProjectProfile
- [ ] `discovery_verbose=true` → discovery comment поститься завжди
- [ ] Немає langchain/anthropic/openai в dependencies
- [ ] `.env.example` тільки робочі settings
- [ ] `ROADMAP.md` в root, README links працюють
- [ ] Coverage ≥ 80% для нового коду
