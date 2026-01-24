# Канвас прогресу Спрінту 1 (Розширений) — MVP Code Reviewer

**Початок спрінту:** 2026-01-20
**Мета спрінту:** MVP з GitHub + GitLab, Inline Comments, WOW-ефект
**Статус:** 🚧 В роботі

---

## 📊 Огляд спрінту

| Метрика | Ціль | Поточне | Статус |
|---------|------|---------|--------|
| **Завдань виконано** | 10/10 | 8/10 | 🏗️ |
| **Покриття тестами** | ≥80% | 93% | ✅ |
| **GitHub інтеграція** | ✅ Працює | ✅ GitProvider ABC | ✅ |
| **GitLab інтеграція** | ✅ Працює | ⏳ Не почато | ⏳ |
| **Inline Comments** | ✅ Apply button | ✅ submit_review() готовий | 🔄 |
| **Мовна адаптивність** | ✅ Працює | ⏳ Не почато | ⏳ |
| **Docker image** | ✅ Опубліковано | ⏳ Не почато | ⏳ |
| **PyPI package** | ✅ v0.1.0 | ⏳ Не опубліковано | ⏳ |

---

## 🎯 Беклог спрінту

### ✅ Раніше виконані завдання (з попередньої версії спрінту)

Наступні компоненти були створені раніше і потребують **рефакторингу/розширення**:

| Компонент | Статус | Потрібні зміни |
|-----------|--------|----------------|
| `core/models.py` | ✅ Базовий | Додати CodeIssue, GoodPractice, ReviewMetrics |
| `core/config.py` | ✅ Базовий | Додати LanguageMode, GitLab settings |
| `core/formatter.py` | ✅ Базовий | Переписати з WOW-форматуванням |
| `integrations/github.py` | ✅ Базовий | Рефакторинг на GitProvider, Inline Comments |
| `integrations/gemini.py` | ✅ Базовий | Додати метрики |
| `integrations/prompts.py` | ✅ Базовий | Оновити для менторського ревʼю |
| `reviewer.py` | ✅ Базовий | Оновити для нової архітектури |
| `cli.py` | ✅ Базовий | Виправити entry point, GitLab support |

---

### 🔧 Завдання 1: Фундамент та виправлення
**Статус:** ✅ **ЗАВЕРШЕНО** (2026-01-23)
**Призначено:** Claude Code (AI)
**Оцінка часу:** 2 години

**Чеклист:**
- [x] Виправлено entry point в `pyproject.toml`
- [x] Створено `ensure_timezone()` в `utils/time.py`
- [x] Додано `LanguageMode` enum в Settings
- [x] Додано `api_timeout` в Settings
- [x] Додано `@lru_cache` для `get_settings()`
- [x] Додано `tenacity` в залежності
- [x] `ai-review --help` працює

**Нотатки:**
```
- Entry point: змінено main → app (Typer вимагає app object)
- Додано clear_settings_cache() для тестів
- api_timeout: 5-300 сек, default 30
- LanguageMode: ADAPTIVE (default), FIXED
- 173 тестів пройшли після Task 1
```

---

### 🔌 Завдання 2: Архітектура провайдерів (Adapter)
**Статус:** ✅ **ЗАВЕРШЕНО** (2026-01-23)
**Призначено:** Claude Code (AI)
**Оцінка часу:** 3 години

**Чеклист:**
- [x] Створено `GitProvider` ABC в `base.py`
- [x] Створено `LineComment` dataclass
- [x] `GitHubClient` наслідує `GitProvider`
- [x] Реалізовано `submit_review()` з batch posting
- [x] `reviewer.py` використовує інтерфейс
- [x] Inline comments через GitHub Review API
- [x] Тести оновлено

**Нотатки:**
```
- Створено base.py: GitProvider ABC, LineComment, ReviewSubmission
- GitHubClient тепер наслідує GitProvider
- reviewer.py абстраговано від провайдера (dependency injection)
- CLI створює GitHubClient і передає в review_pull_request()
- Два методи для коментарів: post_comment() і submit_review()
- submit_review() використовує GitHub PR Review API для inline comments
- LineComment підтримує suggestions (→ кнопка "Apply suggestion")
- 196 тестів, 93% coverage
```

---

### 🦊 Завдання 3: Інтеграція GitLab
**Статус:** 🎯 **НАСТУПНЕ**
**Призначено:** Claude Code (AI)
**Оцінка часу:** 4 години

**Чеклист:**
- [ ] Створено `GitLabClient(GitProvider)` в `gitlab.py`
- [ ] Реалізовано `get_merge_request()`
- [ ] Реалізовано `get_linked_task()`
- [ ] Реалізовано `submit_review()` через Discussions
- [ ] Додано `GITLAB_TOKEN`, `GITLAB_URL` в Settings
- [ ] Оновлено CLI для GitLab context
- [ ] Написано інтеграційні тести

**Нотатки:**
```
[Додавай нотатки під час роботи]
```

---

### 🌍 Завдання 4a: Мовна адаптивність
**Статус:** ⏳ Очікує Завдання 1
**Призначено:** Claude Code (AI)
**Оцінка часу:** 2 години

**Чеклист:**
- [ ] Створено `utils/language.py`
- [ ] Реалізовано `detect_context_language()`
- [ ] Оновлено system prompt для адаптивності
- [ ] Додано `detected_language` в `ReviewResult`
- [ ] `LANGUAGE_MODE=fixed` працює
- [ ] Fallback на англійську працює
- [ ] Тести написано

**Нотатки:**
```
[Додавай нотатки під час роботи]
```

---

### 🎨 Завдання 4b: Розширена структура ревʼю та WOW-форматування
**Статус:** ⏳ Очікує Завдання 4a
**Призначено:** Claude Code (AI)
**Оцінка часу:** 4 години

**Чеклист:**
- [ ] Оновлено `models.py` з CodeIssue, GoodPractice
- [ ] Оновлено system prompt для менторського ревʼю
- [ ] Переписано `formatter.py` з WOW-форматуванням
- [ ] GitHub suggestion syntax працює
- [ ] Collapsible sections працюють
- [ ] Good practices відображаються
- [ ] Before/After diff preview працює

**Приклад очікуваного output:**
```markdown
# 🤖 AI Code Review

## 📊 Summary
| 🔴 Critical | 🟡 Warnings | 💡 Suggestions | ✨ Good |
|-------------|-------------|----------------|---------|
| 1           | 2           | 3              | 2       |

## 🔒 Security Issues
### 🔴 SQL Injection Vulnerability
**File:** `db/queries.py:42`

```suggestion
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
```⁣

<details>
<summary>💡 Why is this important?</summary>
SQL injection allows attackers...
📚 [OWASP Guide](https://owasp.org/...)
</details>

## ✨ Good Practices Noticed
- ✨ Excellent use of type hints in `models.py`
- ✨ Comprehensive error handling in `api.py`

---
⏱️ 2.3s | 🪙 1540 tokens | 💰 ~$0.003
```

**Нотатки:**
```
[Додавай нотатки під час роботи]
```

---

### 📈 Завдання 4c: Метрики виконання
**Статус:** ⏳ Очікує Завдання 4b
**Призначено:** Claude Code (AI)
**Оцінка часу:** 2 години

**Чеклист:**
- [ ] Створено `ReviewMetrics` модель
- [ ] `GeminiClient` збирає метрики
- [ ] Обчислюється estimated cost
- [ ] Footer з метриками в output
- [ ] Тести написано

**Нотатки:**
```
[Додавай нотатки під час роботи]
```

---

### 🐳 Завдання 5: Контейнеризація та дистрибуція
**Статус:** ⏳ Очікує Завдання 3
**Призначено:** Claude Code (AI)
**Оцінка часу:** 3 години

**Чеклист:**
- [ ] Створено multi-stage `Dockerfile`
- [ ] Створено `action.yml`
- [ ] Створено `examples/github-workflow.yml`
- [ ] Створено `examples/gitlab-ci.yml`
- [ ] Docker image збирається локально
- [ ] GitHub Action працює
- [ ] GitLab template працює

**Нотатки:**
```
[Додавай нотатки під час роботи]
```

---

### 🧪 Завдання 6: Тестування та стійкість
**Статус:** ⏳ Очікує Завдання 2
**Призначено:** Claude Code (AI)
**Оцінка часу:** 4 години

**Чеклист:**
- [ ] Створено `utils/retry.py`
- [ ] Retry decorators додано до API clients
- [ ] Error handling wrapper створено
- [ ] CLI tests написано (≥80% coverage)
- [ ] Retry tests написано
- [ ] Логи структуровані

**CLI Test Coverage:**
| Функція | Покриття |
|---------|----------|
| `detect_provider()` | ⏳ |
| `extract_github_context()` | ⏳ |
| `extract_gitlab_context()` | ⏳ |
| `main()` | ⏳ |

**Нотатки:**
```
[Додавай нотатки під час роботи]
```

---

### 📚 Завдання 7: Багатомовна документація
**Статус:** ⏳ Очікує Завдання 5
**Призначено:** Claude Code (AI)
**Оцінка часу:** 4 години

**Чеклист:**
- [ ] Налаштовано i18n плагін
- [ ] Створено структуру директорій
- [ ] Англійська документація:
  - [ ] index.md
  - [ ] quick-start.md
  - [ ] configuration.md
  - [ ] github-setup.md
  - [ ] gitlab-setup.md
- [ ] Український переклад
- [ ] Німецький переклад
- [ ] Іспанський переклад
- [ ] Чорногорський переклад
- [ ] Італійський переклад
- [ ] Перемикач мов працює
- [ ] Автодеплой працює

**Статус мов:**
- [ ] 🇬🇧 English (en) — Primary
- [ ] 🇺🇦 Українська (uk)
- [ ] 🇩🇪 Deutsch (de)
- [ ] 🇪🇸 Español (es)
- [ ] 🇲🇪 Crnogorski (me)
- [ ] 🇮🇹 Italiano (it)

**Нотатки:**
```
[Додавай нотатки під час роботи]
```

---

### 🔄 Завдання 8: CI/CD Pipeline
**Статус:** ⏳ Очікує Завдання 5
**Призначено:** Claude Code (AI)
**Оцінка часу:** 2 години

**Чеклист:**
- [ ] `tests.yml` оновлено
- [ ] `release.yml` оновлено для Docker
- [ ] `docker-publish.yml` створено
- [ ] PyPI trusted publishing налаштовано
- [ ] Всі workflows зелені

**Workflows:**
| Workflow | Файл | Статус |
|----------|------|--------|
| Tests | `tests.yml` | ✅ Існує |
| AI Review | `ai-review.yml` | ✅ Існує |
| Release | `release.yml` | ✅ Існує |
| Docker | `docker-publish.yml` | ⏳ Потрібно створити |

**Нотатки:**
```
[Додавай нотатки під час роботи]
```

---

### 🔍 Завдання 9: Фінальна інтеграція та QA
**Статус:** ⏳ Очікує всі попередні
**Призначено:** Human + AI
**Оцінка часу:** 3 години

**Test Scenarios:**
- [ ] PR з security issue → Critical inline comment
- [ ] PR з code quality issues → Suggestions with Apply
- [ ] PR з хорошим кодом → Good practices
- [ ] PR українською → Відповідь українською
- [ ] PR англійською → Відповідь англійською
- [ ] PR без linked task → Appropriate messaging
- [ ] Network timeout → Retry та успіх
- [ ] Invalid token → Clear error message
- [ ] GitLab MR → Full workflow works

**Нотатки:**
```
[Додавай нотатки під час роботи]
```

---

### 🚀 Завдання 10: Реліз v0.1.0
**Статус:** ⏳ Очікує Завдання 9
**Призначено:** Human
**Оцінка часу:** 1 година

**Чеклист:**
- [ ] Версія оновлена в `pyproject.toml`
- [ ] CHANGELOG.md написано
- [ ] Тег `v0.1.0` створено
- [ ] PyPI publish перевірено
- [ ] Docker image в GHCR
- [ ] GitHub Release створено
- [ ] Документація задеплоєна
- [ ] Анонс опубліковано

**Нотатки:**
```
[Додавай нотатки під час роботи]
```

---

## 🧪 Прогрес тестування

### Покриття тестами по модулях

| Модуль | Ціль | Поточне | Статус |
|--------|------|---------|--------|
| core/models.py | ≥90% | 100% | ✅ |
| core/config.py | ≥90% | 100% | ✅ |
| core/formatter.py | ≥80% | 98% | ✅ |
| integrations/base.py | ≥80% | 100% | ✅ NEW |
| integrations/github.py | ≥80% | 88% | ✅ |
| integrations/gitlab.py | ≥80% | 0% | ⏳ Новий файл |
| integrations/gemini.py | ≥80% | 96% | ✅ |
| utils/time.py | ≥80% | 91% | ✅ NEW |
| utils/retry.py | ≥90% | 0% | ⏳ Новий файл |
| utils/language.py | ≥80% | 0% | ⏳ Новий файл |
| cli.py | ≥80% | 88% | ✅ |
| reviewer.py | ≥80% | 94% | ✅ |
| **Загалом** | **≥80%** | **93%** | ✅ |

---

## 📅 Графік виконання

```
Завдання 1 (Foundation)     ██████████  ✅ Завершено
    ↓
Завдання 2 (Adapter)        ██████████  ✅ Завершено
    ↓
Завдання 3 (GitLab)         ████░░░░░░  🎯 Наступне
    ↓
Завдання 4a (Language)      ░░░░░░░░░░  [Паралельно з 3]
    ↓
Завдання 4b (WOW)           ░░░░░░░░░░
    ↓
Завдання 4c (Metrics)       ░░░░░░░░░░
    ↓
Завдання 5 (Docker)         ░░░░░░░░░░
    ↓
Завдання 6 (Testing)        ░░░░░░░░░░  [Паралельно з 3-5]
    ↓
Завдання 7 (Docs)           ░░░░░░░░░░
    ↓
Завдання 8 (CI/CD)          ░░░░░░░░░░
    ↓
Завдання 9 (QA)             ░░░░░░░░░░
    ↓
Завдання 10 (Release)       ░░░░░░░░░░
```

---

## 🎯 Щоденний стендап

### Фокус на сьогодні
```
Завдання 3: Інтеграція GitLab
- Створити GitLabClient(GitProvider)
- Реалізувати get_merge_request()
- Реалізувати submit_review() через Discussions
```

### Прогрес з останнього оновлення
```
✅ Завдання 1 (Foundation) - ЗАВЕРШЕНО
  - Entry point виправлено (main → app)
  - ensure_timezone() створено
  - LanguageMode, api_timeout додано
  - lru_cache для get_settings()
  - tenacity в залежностях

✅ Завдання 2 (Adapter) - ЗАВЕРШЕНО
  - GitProvider ABC створено
  - LineComment, ReviewSubmission dataclasses
  - GitHubClient наслідує GitProvider
  - submit_review() з GitHub Review API
  - reviewer.py абстраговано (DI)
  - 196 тестів, 93% coverage
```

### Блокери
```
Немає
```

### Питання
```
Немає - готовий до виконання Завдання 3
```

---

## 📝 Журнал рішень

### Рішення 1: 2026-01-23 — Inline Comments як пріоритет
**Питання:** Чи є inline comments критичними для MVP?
**Рішення:** Так, це пріоритет для WOW-ефекту
**Обґрунтування:** Apply Suggestion кнопка — killer feature для UX
**Вплив:** Потребує GitHub Review API замість Issue Comments

### Рішення 2: 2026-01-23 — Без накопичувальної статистики
**Питання:** Чи потрібна stats persistence в MVP?
**Рішення:** Ні, тільки поточні метрики
**Обґрунтування:** CI не має persistence, реалізуємо в Спрінті 2
**Вплив:** Спрощує MVP, фокус на core functionality

### Рішення 3: 2026-01-23 — Без Rating системи
**Питання:** Чи потрібен Rating (A-F) в MVP?
**Рішення:** Ні, додамо пізніше
**Обґрунтування:** Потребує визначення критеріїв, не блокує цінність
**Вплив:** Спрощує ReviewResult модель

### Рішення 4: 2026-01-23 — LanguageMode.FIXED замість STRICT
**Питання:** Як назвати режим фіксованої мови?
**Рішення:** `FIXED` замість `STRICT`
**Обґрунтування:** Семантично точніше, "strict" може сприйматися як суворий режим
**Вплив:** Зміна в config.py

### Рішення 5: 2026-01-23 — Два методи для коментарів
**Питання:** Чи замінити Issue Comments на PR Review API?
**Рішення:** Зберегти обидва як окремі інструменти
**Обґрунтування:** Різні use cases — post_comment() для summary/errors, submit_review() для inline з suggestions
**Вплив:** GitProvider має два методи: post_comment() і submit_review()

### Рішення 6: 2026-01-23 — Dependency Injection в reviewer.py
**Питання:** Як абстрагувати reviewer від конкретного провайдера?
**Рішення:** Provider передається як параметр (DI), CLI створює конкретний client
**Обґрунтування:** Чиста архітектура, легко тестувати, легко додати GitLab
**Вплив:** review_pull_request(provider, repo_name, mr_id, settings)

---

## 🐛 Проблеми та рішення

### Проблема 1: Entry Point — 2026-01-23
**Проблема:** `ai-review = "ai_reviewer.cli:main"` не працює з Typer
**Рішення:** Змінено на `ai-review = "ai_reviewer.cli:app"`
**Статус:** ✅ Виправлено в Завданні 1

### Проблема 2: CLI тести — 0% coverage
**Проблема:** CLI модуль не має тестів
**Рішення:** Додано unit tests для CLI
**Статус:** ✅ Виправлено (88% coverage)

---

## 💡 Висновки та інсайти

### Технічні висновки
```
- GitHub Review API потрібен для Apply Suggestion (не Issue Comments)
- GitLab використовує Discussions API для inline comments
- Мовна адаптивність краще через LLM prompt, ніж бібліотеку
```

### Процесні висновки
```
- WOW-ефект важливіший за кількість фіч
- Inline comments = головний диференціатор від конкурентів
```

### Інсайти про інструменти
```
- tenacity — стандарт для retry logic в Python
- GitHub suggestion syntax автоматично рендерить Apply кнопку
```

---

## ✅ Чеклист завершення спрінту

### Функціональність
- [ ] GitHub інтеграція з Inline Comments
- [ ] GitLab інтеграція з Discussions
- [ ] Мовна адаптивність працює
- [ ] WOW-форматування виглядає добре
- [ ] Метрики відображаються
- [ ] Retry logic працює
- [ ] Error messages зрозумілі

### Якість коду
- [ ] Всі тести проходять
- [ ] Покриття ≥80%
- [ ] Ruff check проходить
- [ ] Mypy проходить
- [ ] Pre-commit хуки працюють

### Дистрибуція
- [ ] Docker image збирається
- [ ] GitHub Action працює
- [ ] GitLab template працює
- [ ] PyPI package опубліковано

### Документація
- [ ] 6 мов документації
- [ ] Перемикач мов працює
- [ ] Автодеплой працює

### Реліз
- [ ] Тег v0.1.0 створено
- [ ] GitHub Release опубліковано
- [ ] CHANGELOG.md написано

---

## 🎊 Ретроспектива спрінту

**Що пішло добре:**
```
[Заповнити в кінці спрінту]
```

**Що можна покращити:**
```
[Заповнити в кінці спрінту]
```

**Дії для наступного спрінту:**
```
[Заповнити в кінці спрінту]
```

---

## 📊 Фінальні метрики спрінту

**Заповнити при завершенні:**

- Дата початку: 2026-01-20
- Дата завершення: [Дата]
- Тривалість: [Днів]
- Завдань виконано: 6/10 → 8/10 → [X]/10
- Покриття тестами: 94% → 93% → [X]%
- Рядків коду: ~600 → ~680 → [X]
- Нових файлів: 2 (base.py, time.py)
- Тестів: 196
- Коммітів: [X]

---

## 🚀 Попередній перегляд Спрінту 2

**Спрінт 2: Intelligence & Learning**
- Контекст репозиторію (conventions, patterns)
- Multi-LLM router (Claude, GPT, Gemini)
- Кешування результатів
- Накопичувальна статистика
- Auto-fix PR creation
- Rating система (A-F)
- Interactive commands (@ai-reviewer explain)

---

**Памʼятай:** Оновлюй цей документ під час роботи! 📝

**WOW-ефект понад усе! 🎆**
