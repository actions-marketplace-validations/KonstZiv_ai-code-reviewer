# Sprint Beta-0.5: LLM-Driven Discovery + Pre-release Polish

## Навігація

```
sprint-beta-0.5/
├── SPRINT.md                              ← ви тут
├── REVIEW_GATE.md                         Обов'язковий чеклист між фазами
├── phase-1-discovery-engine/              Фаза 1: Discovery Engine Redesign (6-8h) ⭐
│   ├── EPIC.md
│   ├── task-1.1-raw-data-enrichment/      Детерміністичні дані: configs → framework/layout
│   ├── task-1.2-llm-analysis-prompt/      LLM-промпт: три зони уваги + watch-files
│   ├── task-1.3-watch-files-caching/      Зберігання результатів + кешування
│   └── task-1.4-mr-aware-discovery/       Edge cases: мова diff, deps в MR, watch-files в diff
├── phase-2-review-integration/            Фаза 2: Review Integration (2-3h)
│   ├── EPIC.md
│   ├── task-2.1-dynamic-system-prompt/    Три зони → інструкції для review
│   └── task-2.2-discovery-comment/        Verbose mode + візуалізація зон
├── phase-3-housekeeping/                  Фаза 3: Housekeeping (1.5h)
│   ├── EPIC.md
│   └── task-3.1-cleanup-bundle/           Dead deps, .env, ROADMAP, raw_yaml
└── phase-4-polish/                        Фаза 4: Polish & UX (2-3h)
    ├── EPIC.md
    ├── task-4.1-reliability/              Timeout, type fixes, conftest.py
    ├── task-4.2-discover-cli/             `ai-review discover` standalone
    └── task-4.3-docs-gate/               Документація + фінальна верифікація
```

---

## 🔙 Де ми зараз (після Beta-0)

### Що зроблено (85%)

- **3 ABCs**: `LLMProvider`, `RepositoryProvider`, `ConversationProvider`
- **Triple inheritance**: `GitHubClient` і `GitLabClient` реалізують усі 3 інтерфейси
- **Discovery pipeline**: 4-layer (Platform API → CI → Configs → LLM), graceful degradation
- **ConversationProvider**: `BotQuestion` з `question_id` + `default_assumption`
- **Integration**: Discovery → review prompt (`## Project Context`), fail-open
- **Tests**: 30 файлів, 12K рядків, 6 fixture scenarios
- **Docs**: Discovery page (5 мов), README updated

### Критична проблема

`_build_profile_deterministic()` **збирає** configs (pyproject.toml, package.json) але **нічого з ними не робить**. Для 80% проєктів Discovery видає `framework: None`, `conventions: ()`.

### Архітектурне рішення: LLM замість regex

**Було (Beta-0):** Regex-based CI analyzer (457 рядків) — крихкий, обмежене покриття tools.

**Стає (Beta-0.5):** LLM як domain expert з трьома зонами уваги:

```
                    ┌─────────────────────────┐
                    │   Raw Data (0 tokens)    │
                    │  languages, deps, CI,    │
                    │  file tree, configs      │
                    └──────────┬──────────────┘
                               │
                    ┌──────────▼──────────────┐
                    │  LLM Analysis (~200 tok) │
                    │  ONE focused prompt      │
                    └──────────┬──────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                 ▼
     ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
     │ ✅ Well       │ │ ❌ Not       │ │ ⚠️ Weakly    │
     │ covered      │ │ covered      │ │ covered      │
     │ → SKIP       │ │ → FOCUS      │ │ → CHECK +    │
     │   in review  │ │   in review  │ │   recommend  │
     └──────────────┘ └──────────────┘ └──────────────┘
              │                │                 │
              └────────────────┼────────────────┘
                               │
                    ┌──────────▼──────────────┐
                    │  Watch-Files List        │
                    │  "re-run me when these   │
                    │   files change"          │
                    └─────────────────────────┘
```

**Deprecated:** regex CI analyzer (`_analyze_ci_*`, 457 рядків).

---

## 🎯 Мета спринту

**Перетворити Discovery з пасивного збирача даних на активного радника для review.**

Після Sprint Beta-0.5:

1. Discovery **розуміє** проєкт через LLM — framework, coverage gaps, quality рекомендації
2. Review prompt **адаптується** — "DON'T check formatting (CI handles it)", "MUST check SQL injection (not covered)"
3. **MR-aware** — аналізує мови diff, нові deps, зміни в CI config
4. **Кеш** — перший запуск ~200 tokens, наступні 0 tokens (поки watch-files не змінились)
5. Код чистий, ready for v1.0.0b1 tag

### Що отримує користувач

| До Beta-0.5 | Після Beta-0.5 |
|-------------|----------------|
| Бот знає мову і CI tools, але не framework | Бот знає Django/FastAPI/React + якість CI coverage |
| Review prompt: "## Project Context" (пасивний) | Review prompt: "SKIP formatting, FOCUS security" (активний) |
| Однаковий аналіз для repo і MR | MR з SQL+YAML → промпт адаптується до diff |
| Discovery запускається кожен раз | Watch-files кеш: 0 tokens якщо CI не змінився |
| Нові deps в MR — невидимі | "Додано sqlalchemy — перевір security surface" |
| Тестувати Discovery тільки через MR | `ai-review discover owner/repo` — standalone |

---

## Фази

### Фаза 1: Discovery Engine Redesign (6-8h) ⭐ Ядро спринту

**Мета:** Discovery розуміє проєкт і видає три зони уваги.

- **1.1** Raw Data Enrichment — fix `_build_profile_deterministic()`, Go modules, file tree truncation
- **1.2** LLM Analysis Prompt — один промпт → три зони + watch-files + framework/layout
- **1.3** Watch-Files & Caching — зберігання результатів, механізм кешування
- **1.4** MR-Aware Discovery — мова diff, нові deps, watch-files в diff

**Чому першою:** Це foundation. Все інше (prompt integration, CLI, verbose) будується на результатах Discovery.

### Фаза 2: Review Integration (2-3h)

**Мета:** Три зони → реальний вплив на якість review.

- **2.1** Dynamic System Prompt — зони стають інструкціями для LLM
- **2.2** Discovery Comment — verbose mode, візуалізація зон для користувача

### Фаза 3: Housekeeping (1.5h)

**Мета:** Чистий, безпечний codebase.

- **3.1** Cleanup bundle: dead deps + .env + ROADMAP + raw_yaml (один task, 4 дрібні зміни)

### Фаза 4: Polish & UX (2-3h)

**Мета:** Надійність + видимість для користувача.

- **4.1** Reliability: timeout, type fixes, conftest.py
- **4.2** `ai-review discover` CLI — standalone discovery command
- **4.3** Docs + Review Gate — синхронізація документації, фінальна верифікація

---

## Загальний обсяг

| Фаза | Estimate | Tasks |
|-------|----------|-------|
| Phase 1: Discovery Engine | 6-8h | 4 |
| Phase 2: Review Integration | 2-3h | 2 |
| Phase 3: Housekeeping | 1.5h | 1 |
| Phase 4: Polish & UX | 2-3h | 3 |
| **Total** | **11.5-15.5h** | **10** |

---

## 🔮 Що далі (Beta-1 preview)

Sprint Beta-0.5 закладає foundation для Beta-1:

- **Три зони** → Beta-1: framework-specific hints (Django: check migrations, React: check hook rules)
- **Watch-files** → Beta-1: persistent storage між runs (Redis/file-based)
- **MR-aware** → Beta-1: test coverage gap detection (source changed, no test in diff)
- **Discover CLI** → Beta-1: `ai-review discover --generate-config` для bootstrap `.reviewbot.md`
- **ConversationProvider** → Beta-1: deep linked task search, follow-up dialogue

---

## Definition of Done

- [ ] `make check` passes (lint + test) — zero warnings
- [ ] LLM Discovery prompt → три зони для Python проєкту з CI
- [ ] Watch-files mechanism → повторний запуск = 0 LLM tokens
- [ ] MR з іншою мовою ніж repo → промпт адаптується
- [ ] Dynamic system prompt містить "SKIP/FOCUS/CHECK" інструкції
- [ ] `ai-review discover owner/repo` → виводить три зони
- [ ] Немає langchain/anthropic/openai в dependencies
- [ ] `.env.example` тільки робочі settings
- [ ] Coverage ≥ 80% для нового коду
