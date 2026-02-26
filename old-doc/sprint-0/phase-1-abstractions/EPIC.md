# Фаза 1: Three ABCs (Abstractions)

## Навігація

```
phase-1-abstractions/
├── EPIC.md                            ← ви тут
├── task-1.1-llm-provider/             LLMProvider ABC + GeminiProvider
├── task-1.2-repository-provider/      RepositoryProvider ABC + GitHub/GitLab impl
├── task-1.3-conversation-provider/    ConversationProvider ABC + impl
├── task-1.4-housekeeping/             Залежності, N+1, ініціалізація
└── task-1.5-linked-task-strategy/     Strategy-based linked task resolver
```

**Батьківський документ:** [../SPRINT.md](../SPRINT.md)

---

## 🔙 Контекст

### Що маємо

Робочий Alpha з хардкодженим Gemini, `GitProvider` ABC тільки для MR-операцій
(get_merge_request, post_comment, submit_review), і нуль знань про репозиторій.
Бот постить коментарі, але не відстежує відповіді.

Код чистий: mypy strict, ruff ALL, pytest, pre-commit. Pydantic-моделі frozen.
Retry з exponential backoff. Custom error hierarchy.

### Проблема

Discovery потребує:
1. **Generic LLM-виклики** — з різними response schema (не тільки ReviewResult)
2. **Доступ до Platform API** — мови, файли, метадані репозиторію
3. **Діалог** — ставити питання, читати відповіді, відповідати в threads

Жодної з цих абстракцій не існує.

---

## 🎯 Мета фази

Створити 3 ABC, на яких стоятиме весь Beta. **Існуючий функціонал НЕ ламається.**
CLI, action.yml, reviewer.py — все працює як раніше.

---

## Задачі

| # | Задача | Оцінка | Залежності |
|---|--------|--------|------------|
| 1.1 | LLMProvider ABC + GeminiProvider | 3-4 год | — |
| 1.2 | RepositoryProvider ABC + GitHub/GitLab | 4-5 год | — |
| 1.3 | ConversationProvider ABC + GitHub/GitLab | 5-7 год | — |
| 1.4 | Housekeeping (deps, N+1, init) | 2-3 год | 1.1 |
| 1.5 | Linked Task Discovery Strategy | 3-4 год | Фаза 1 (GitProvider ABC) |

Задачі 1.1–1.3 незалежні — можна паралелити.
Задача 1.4 залежить від 1.1 (GeminiProvider для fix ініціалізації).
Задача 1.5 — розширення ABC: єдиний multi-strategy resolver для linked tasks.

---

## Definition of Done

- [ ] `make check` проходить
- [ ] `LLMProvider.generate()` працює з довільною Pydantic schema
- [ ] `RepositoryProvider` — languages, metadata, file_tree, file_content для обох платформ
- [ ] `ConversationProvider` — post questions, read threads, reply для обох платформ
- [ ] Невикористані deps перенесено в optional
- [ ] GitLab N+1 виправлено
- [ ] Unit-тести з mocks на кожен ABC

---

## ⚠️ Ревізія після завершення

Перед переходом до Фази 2 перевірити:

1. Чи сигнатури ABC відповідають очікуванням `DiscoveryOrchestrator` (task 2.6)?
2. Чи `LLMResponse` model сумісна з існуючим `ReviewMetrics`?
3. Чи `RepositoryMetadata` покриває потреби `PlatformData` (task 2.1)?
4. Чи `BotQuestion`/`BotThread` зручні для orchestrator'а?

Оновити IMPLEMENTATION.md у Фазі 2 якщо щось змінилось.

---

## 🔭 Використання ABCs далі

| ABC | Beta-0 | Beta-1 | Beta-2 |
|-----|--------|--------|--------|
| LLMProvider | Discovery interpretation | LLM fallback | Scout + Deep review |
| RepositoryProvider | Platform data, configs | — | Scout requests files |
| ConversationProvider | Discovery questions | Deep linked tasks | Thread participation |
