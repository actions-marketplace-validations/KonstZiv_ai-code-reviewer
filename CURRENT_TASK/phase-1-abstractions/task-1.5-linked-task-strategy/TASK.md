# Task 1.5: Linked Task Discovery Strategy

| Поле | Значення |
|------|----------|
| **Фаза** | 1 — Abstractions (розширення) |
| **Пріоритет** | High — зараз sidebar relations не знаходяться |
| **Оцінка** | 3-4 години |
| **Залежності** | Фаза 1 (GitProvider ABC) |
| **Блокує** | — |
| **Файли** | `src/ai_reviewer/integrations/base.py`, `github.py`, `gitlab.py`, `reviewer.py` |

## Проблема

Зараз `reviewer.py` викликає `GitProvider.get_linked_task()`, який шукає
пов'язані задачі **тільки через regex** в описі PR/MR (`Fixes #123`,
`Closes #123`). Це знаходить лише один шлях зв'язування з багатьох.

Реальні користувачі зв'язують задачі різними способами:

| Спосіб | GitHub | GitLab | Поточна підтримка |
|--------|--------|--------|-------------------|
| Closing keywords в description | `Fixes #123` | `Closes #123` | ✅ regex |
| Sidebar "Development" relations | PR → Issue link | MR → Issue link | ❌ |
| Timeline events | `connected`, `cross-referenced` | — | ❌ (є `get_linked_tasks_deep`, не викликається) |
| `closes_issues()` API | — | `mr.closes_issues()` | ❌ (є `get_linked_tasks_deep`, не викликається) |
| Closing keywords в commits | `fix #123` в commit msg | `closes #123` в commit msg | ❌ |
| Branch name convention | `86-task-22-foo` → issue #86 | `86-task-22-foo` → issue #86 | ❌ |
| External trackers | Jira (`PROJECT-123`) | Jira integration | ❌ (future) |

Вже є `get_linked_tasks_deep()` в обох клієнтах (GitHub: timeline events,
GitLab: `closes_issues()` API), але:
1. Метод не входить до ABC `GitProvider` — немає контракту
2. `reviewer.py` його не викликає
3. Повертає `tuple[LinkedTask, ...]`, а `ReviewContext.task` — `LinkedTask | None`

## Що робимо

Створити **Strategy-based linked task resolver** з підтримкою кількох
методів пошуку та єдиним інтерфейсом для обох платформ.

### Архітектурне рішення

```
GitProvider ABC
  get_linked_tasks(repo_name, mr_id) -> tuple[LinkedTask, ...]
      │
      ├── Strategy 1: Description regex (Fixes #N, Closes #N)
      ├── Strategy 2: Platform API (timeline events / closes_issues)
      ├── Strategy 3: Branch name convention (123-feature → #123)
      └── (extensible: додаткові стратегії без зміни інтерфейсу)
```

### Ключові принципи

1. **Один метод в ABC** — `get_linked_tasks()` замінює `get_linked_task()`
2. **Fail-open** — якщо одна стратегія падає, інші працюють
3. **Deduplicated** — результати об'єднані, без дублікатів
4. **Ordered** — description regex першим (найнадійніший), потім API, потім branch
5. **Extensible** — нова стратегія = новий метод в конкретному клієнті

### Кроки

1. **Оновити ABC `GitProvider`:**
   - Замінити `get_linked_task(repo_name, mr) -> LinkedTask | None`
     на `get_linked_tasks(repo_name, mr_id) -> tuple[LinkedTask, ...]`
   - Deprecated alias для backward compatibility (1 release)

2. **Рефакторити `GitHubClient`:**
   - Об'єднати логіку з `get_linked_task()` і `get_linked_tasks_deep()` в `get_linked_tasks()`
   - Додати branch name parsing strategy
   - Видалити `get_linked_tasks_deep()` (перенести логіку)

3. **Рефакторити `GitLabClient`:**
   - Аналогічно: об'єднати + branch name parsing
   - Видалити `get_linked_tasks_deep()`

4. **Оновити `ReviewContext`:**
   - `task: LinkedTask | None` → `tasks: tuple[LinkedTask, ...] = ()`
   - Оновити всі місця використання (prompts, etc.)

5. **Оновити `reviewer.py`:**
   - Викликати `get_linked_tasks(repo_name, mr.number)`
   - Логувати кількість знайдених tasks

6. **Тести:**
   - Кожна стратегія окремо (regex, API, branch)
   - Комбінований тест: кілька стратегій → deduplicated результат
   - Fail-open: одна стратегія кидає exception → інші працюють
   - Оновити mock у всіх existing tests

### Branch name convention

Типові паттерни:
- `86-task-22-cipipelineanalyzer` → issue `#86`
- `feature/123-add-login` → issue `#123`
- `fix/456` → issue `#456`
- `GH-789-refactor` → issue `#789`

Regex: `^(?:\w+/)?(?:GH-)?(\d+)[-_]` — витягує перше число з branch name.
Валідація: перевірити що issue з таким номером існує (API call).

## Очікуваний результат

- `reviewer.py` знаходить linked tasks через sidebar relations
- Branch name `86-task-22-...` → автоматично знаходить issue #86
- GitLab: `closes_issues()` API працює
- GitHub: timeline events працюють
- Нова стратегія додається без зміни ABC
- Всі existing tests оновлені і зелені

## Зв'язок з іншими задачами

- **SPRINT.md Beta-1 vision** згадує "Глибший linked tasks" — ця задача
  реалізує це раніше, бо проблема вже актуальна
- **Phase 3 (task 3.1)** — prompt integration використовує `ReviewContext.task`,
  потребує оновлення на `tasks`
