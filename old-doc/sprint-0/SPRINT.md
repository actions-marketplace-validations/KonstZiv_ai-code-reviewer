# Sprint Beta-0: Discovery Phase + Conversation Foundation

## Навігація

```
sprint-beta-0/
├── SPRINT.md                          ← ви тут
├── phase-1-abstractions/              Фаза 1: Three ABCs (рефакторинг)
│   ├── EPIC.md
│   ├── task-1.1-llm-provider/
│   ├── task-1.2-repository-provider/
│   ├── task-1.3-conversation-provider/
│   ├── task-1.4-housekeeping/
│   └── task-1.5-linked-task-strategy/
├── phase-2-discovery-engine/          Фаза 2: Discovery Engine
│   ├── EPIC.md
│   ├── task-2.1-discovery-models/
│   ├── task-2.2-ci-analyzer/
│   ├── task-2.3-config-collection/
│   ├── task-2.4-reviewbot-config/
│   ├── task-2.5-discovery-prompts/
│   └── task-2.6-discovery-orchestrator/
├── phase-3-integration/               Фаза 3: Integration
│   ├── EPIC.md
│   ├── task-3.1-prompt-integration/
│   ├── task-3.2-reviewer-integration/
│   └── task-3.3-discovery-comment/
└── phase-4-polish/                    Фаза 4: Polish
    ├── EPIC.md
    ├── task-4.1-test-fixtures/
    ├── task-4.2-edge-cases/
    └── task-4.3-documentation/
```

---

## 🔙 Де ми зараз (Alpha)

### Що працює

- **Платформи:** GitHub (PyGithub) + GitLab (python-gitlab) — повний цикл рев'ю
- **LLM:** Google Gemini, single provider, sync, structured output через Pydantic
- **Flow:** однокроковий — fetch MR → build prompt → Gemini → format → post
- **Review output:** summary comment + inline comments з suggestions
- **Контекст MR:** title, description, diff, comments (threading), linked task (regex)
- **Resilience:** retry з exponential backoff, custom error hierarchy, fail-open
- **Code quality:** mypy strict, ruff (ALL), pytest з coverage, pre-commit

### Чого не вистачає

- **Контекст проєкту:** бот не знає мову, CI, інструменти → шумні рев'ю
- **LLM абстракція:** Gemini захардкоджений
- **Repository API:** Platform API (languages, file tree) не використовується
- **Діалог:** бот постить, але не читає відповіді на свої питання
- **Мертві залежності:** langchain/anthropic/openai в deps але не використовуються

### Артефакти

| Документ | Зміст |
|----------|-------|
| AI-ReviewBot-Beta-Plan.md | 3 епіки, 4 спринти, загальна стратегія |
| AI-ReviewBot-Discovery-Phase-v3.md | Platform-first, 4-layer architecture |
| AI-ReviewBot-Codebase-Audit.md | Аудит коду: блокери, проблеми, рекомендації |

---

## 🎯 Мета спринту

**Бот розуміє проєкт і вміє ставити питання.**

Після Sprint Beta-0:

1. Бот знає мову, CI, інструменти, конвенції проєкту перед рев'ю
2. Рев'ю не коментує те, що вже перевіряє CI (~30-40% менше шуму)
3. Бот ставить structured questions і розуміє відповіді
4. 3 абстракції — фундамент для всього Beta

---

## Фази

| # | Фаза | Зміст | Оцінка |
|---|------|-------|--------|
| 1 | **Abstractions** | LLMProvider + RepositoryProvider + ConversationProvider + cleanup | 14-19 год |
| 2 | **Discovery Engine** | Models, CI Analyzer, Configs, .reviewbot.md, Prompts, Orchestrator | 16-23 год |
| 3 | **Integration** | Prompt context, Reviewer flow, Discovery comment | 5-8 год |
| 4 | **Polish** | Test fixtures, Edge cases, Documentation | 6-9 год |
| | **Разом** | | **41-59 год** |

---

## Порядок виконання

```
Тиждень 1:   1.1 → 1.2 → 1.3 → 1.4
              LLM ABC → Repo ABC → Conversation ABC → Cleanup
              ✅ Checkpoint: абстракції готові, існуючий код працює

Тиждень 2:   2.1 → 2.2 → 2.3 → 2.4 → 2.5
              Models → CI Analyzer → Configs → .reviewbot.md → Prompts
              ✅ Checkpoint: всі Discovery компоненти готові ізольовано

Тиждень 3:   2.6 → 3.1 → 3.2 → 3.3
              Orchestrator → Prompt → Reviewer → Comment
              ✅ Checkpoint: Discovery працює end-to-end

Тиждень 4:   4.1 → 4.2 → 4.3
              Fixtures → Edge cases → Docs
              ✅ Checkpoint: production-ready
```

---

## Definition of Done

- [ ] `make check` проходить — нічого не зламано
- [ ] Discovery запускається для GitHub і GitLab MR
- [ ] Проєкт з CI → рев'ю НЕ коментує те що перевіряє CI
- [ ] Проєкт без CI → бот ставить structured questions
- [ ] Другий запуск → бот бачить відповіді на свої питання
- [ ] `.reviewbot.md` парситься і використовується
- [ ] `ConversationProvider` — post questions + read responses працює
- [ ] Coverage для нового коду ≥ 80%

---

## ⚠️ Правило ревізії між фазами

> **Після завершення кожної фази** і перед початком наступної виконавець
> ОБОВ'ЯЗКОВО переглядає описи всіх задач наступних фаз:
>
> 1. Чи не змінились інтерфейси/моделі відносно запланованих?
> 2. Чи не з'явились нові знання, які впливають на дизайн?
> 3. Чи не застаріли припущення в IMPLEMENTATION.md?
>
> Якщо знайдено розбіжності — **оновити документацію ДО початку** нової фази.

---

## 🔭 Далі: Vision

### Sprint Beta-1: Deep Context + Stability

- ~~Глибший linked tasks~~ → перенесено в task 1.5 (вже актуально)
- Rate limit & token tracking, usage footer
- Framework-specific hints (Django, FastAPI)
- LLM fallback (Gemini → Claude/OpenAI)

### Sprint Beta-2: Multi-Step Review + Dialogue

- Scout → Enrich → Deep Review
- Бот відповідає в threads
- Decision context tracking

### Sprint Beta-3: Interactive Mode

- Автор відповів → бот реагує → повторний аналіз
- State management для multi-turn
- Auto-update .reviewbot.md

**Принцип:** кожен спринт будує на ABCs з Beta-0. Змінюється реалізація — не інтерфейс.
