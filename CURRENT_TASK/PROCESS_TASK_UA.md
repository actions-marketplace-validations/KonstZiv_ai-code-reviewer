# Канвас прогресу Спрінту 1 (Розширений) — MVP Code Reviewer

**Початок спрінту:** 2026-01-20
**Мета спрінту:** MVP з GitHub + GitLab, Inline Comments, WOW-ефект
**Статус:** 🚧 В роботі

---

## 📊 Огляд спрінту

| Метрика | Ціль | Поточне | Статус |
|---------|------|---------|--------|
| **Завдань виконано** | 10/10 | 6/10 | 🏗️ |
| **Покриття тестами** | ≥80% | 93% | ✅ |
| **GitHub інтеграція** | ✅ Працює | ✅ GitProvider ABC | ✅ |
| **GitLab інтеграція** | ✅ Працює | ✅ GitLabClient готовий | ✅ |
| **Inline Comments** | ✅ Apply button | ✅ WOW-форматування готове | ✅ |
| **Мовна адаптивність** | ✅ Працює | ✅ ISO 639 + Proximity Rule | ✅ |
| **Метрики** | ✅ В footer | ✅ Tokens, latency, cost | ✅ |
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
**Статус:** ✅ **ЗАВЕРШЕНО** (2026-01-24)
**Призначено:** Claude Code (AI)
**Оцінка часу:** 4 години

**Чеклист:**
- [x] Створено `GitLabClient(GitProvider)` в `gitlab.py`
- [x] Реалізовано `get_merge_request()`
- [x] Реалізовано `get_linked_task()`
- [x] Реалізовано `submit_review()` через Discussions
- [x] Додано `GITLAB_TOKEN`, `GITLAB_URL` в Settings
- [x] Оновлено CLI для GitLab context
- [x] Написано інтеграційні тести

**Нотатки:**
```
- GitLabClient: повна імплементація GitProvider інтерфейсу
- get_merge_request(): отримання MR з notes та diffs
- get_linked_task(): пошук linked issues (Closes #123, Fixes #456)
- post_comment(): публікація notes до MR
- submit_review(): inline коментарі через Discussions API
- handle_gitlab_errors decorator для rate limiting (HTTP 429)
- CLI: extract_gitlab_context() для CI_PROJECT_PATH, CI_MERGE_REQUEST_IID
- Тести: 19 тестів для GitLabClient, 6 для config, 3 для CLI
- 222 тести, 92% coverage
```

---

### 🌍 Завдання 4a: Мовна адаптивність
**Статус:** ✅ **ЗАВЕРШЕНО** (2026-01-24)
**Призначено:** Claude Code (AI)
**Оцінка часу:** 3 години

**Чеклист:**
- [x] Додано залежність `python-iso639` для валідації ISO 639
- [x] Створено валідатор `_validate_language_code()` в config.py
- [x] Створено `utils/language.py` з алгоритмом "Proximity Rule"
- [x] Реалізовано `collect_text_samples()`, `build_language_instruction()`
- [x] Оновлено system prompt для адаптивності
- [x] Додано `detected_language` в `ReviewResult`
- [x] `LANGUAGE_MODE=fixed` працює
- [x] `LANGUAGE_MODE=adaptive` з fallback на англійську працює
- [x] Footer для російської мови ("Слава Украине!") в formatter.py
- [x] Тести написано (15 тестів для language.py + 8 для валідації + 10 для formatter)

**Нотатки:**
```
ISO 639 валідація:
- python-iso639 бібліотека для валідації всіх частин стандарту
- Нормалізація до ISO 639-1 (en, uk, de) де можливо
- Підтримка назв мов (Ukrainian → uk)

Алгоритм "Proximity Rule":
- Збирає тексти з коментарів (найновіші першими), MR description, task
- Фільтрує короткі тексти (<8 слів)
- Включає контекст в prompt для LLM визначення мови

Спеціальне повідомлення для ru:
- При LANGUAGE=ru до кожного review додається footer
- "каждый россиянин... Слава Украине!"

255 тестів, 93% coverage
```

---

### 🎨 Завдання 4b: Розширена структура ревʼю та WOW-форматування
**Статус:** ✅ **ЗАВЕРШЕНО** (2026-01-24)
**Призначено:** Claude Code (AI)
**Оцінка часу:** 4 години

**Чеклист:**
- [x] Оновлено `models.py` з CodeIssue, GoodPractice
- [x] Оновлено system prompt для менторського ревʼю
- [x] Переписано `formatter.py` з WOW-форматуванням
- [x] GitHub suggestion syntax працює
- [x] Collapsible sections працюють
- [x] Good practices відображаються
- [x] Before/After diff preview працює

**Нотатки:**
```
Нові моделі:
- CodeIssue: unified модель з category, severity, why_matters, learn_more_url
- GoodPractice: позитивний фідбек
- IssueSeverity: CRITICAL, WARNING, INFO
- IssueCategory: SECURITY, CODE_QUALITY, ARCHITECTURE, PERFORMANCE, TESTING

Оновлений ReviewResult:
- issues: tuple[CodeIssue, ...] замість vulnerabilities
- good_practices: tuple[GoodPractice, ...]
- Нові properties: critical_count, warning_count, info_count, good_practice_count

Форматування:
- Summary card з підрахунком issues
- Секції по категоріям (🔒 Security, 📝 Code Quality, etc.)
- Collapsible learning sections (<details>)
- Before/After diff preview
- ```suggestion syntax для Apply button
- format_inline_comment() - компактний формат для line comments

272 тести, 93% coverage
```

---

### 📈 Завдання 4c: Метрики виконання
**Статус:** ✅ **ЗАВЕРШЕНО** (2026-01-24)
**Призначено:** Claude Code (AI)
**Оцінка часу:** 2 години

**Чеклист:**
- [x] Створено `ReviewMetrics` модель
- [x] `GeminiClient` збирає метрики
- [x] Обчислюється estimated cost
- [x] Footer з метриками в output
- [x] Тести написано

**Нотатки:**
```
ReviewMetrics модель:
- model_name, prompt_tokens, completion_tokens, total_tokens
- api_latency_ms, estimated_cost_usd
- cost_formatted (4 десяткові при <$0.01, інакше 2)
- latency_formatted (ms при <1000, інакше секунди)

Gemini pricing (per 1M tokens):
- gemini-2.5-flash: $0.075 input, $0.30 output
- gemini-1.5-pro: $1.25 input, $5.00 output
- Fallback для невідомих моделей: $1.00/$3.00

GeminiClient оновлено:
- time.perf_counter() для вимірювання latency
- response.usage_metadata для token counts
- calculate_cost() для обчислення вартості
- ReviewResult тепер включає metrics

Footer з метриками:
_Model: gemini-2.5-flash | Tokens: 1,500 | Latency: 1.2s | Est. cost: $0.0002_

300 тестів, 93% coverage
```

---

### 🐳 Завдання 5: Контейнеризація та дистрибуція
**Статус:** 🎯 **НАСТУПНЕ**
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
| core/formatter.py | ≥80% | 96% | ✅ |
| integrations/base.py | ≥80% | 100% | ✅ |
| integrations/github.py | ≥80% | 88% | ✅ |
| integrations/gitlab.py | ≥80% | 88% | ✅ |
| integrations/gemini.py | ≥80% | 100% | ✅ |
| integrations/prompts.py | ≥80% | 100% | ✅ |
| utils/time.py | ≥80% | 91% | ✅ |
| utils/language.py | ≥80% | 100% | ✅ |
| utils/retry.py | ≥90% | 0% | ⏳ Новий файл |
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
Завдання 3 (GitLab)         ██████████  ✅ Завершено
    ↓
Завдання 4a (Language)      ██████████  ✅ Завершено
    ↓
Завдання 4b (WOW)           ██████████  ✅ Завершено
    ↓
Завдання 4c (Metrics)       ██████████  ✅ Завершено
    ↓
Завдання 5 (Docker)         ░░░░░░░░░░  🎯 Наступне
    ↓
Завдання 6 (Testing)        ░░░░░░░░░░  [Паралельно з 5]
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
Завдання 5: Контейнеризація та дистрибуція
- Створити multi-stage Dockerfile
- Створити action.yml для GitHub Action
- Приклади workflow для GitHub та GitLab CI
```

### Прогрес з останнього оновлення
```
✅ Завдання 4c (Metrics) - ЗАВЕРШЕНО (2026-01-24)
  - ReviewMetrics модель (tokens, latency, cost)
  - GeminiClient збирає usage_metadata з response
  - calculate_cost() з GEMINI_PRICING dictionary
  - Footer: "Model: gemini-2.5-flash | Tokens: 1,500 | Latency: 1.2s | Est. cost: $0.0002"
  - 300 тестів, 93% coverage
```

### Блокери
```
Немає
```

### Питання
```
Немає - готовий до виконання Завдання 5 (Docker)
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

### Рішення 7: 2026-01-24 — Міграція з Vulnerability на CodeIssue
**Питання:** Чи залишати старий Vulnerability model для backward compatibility?
**Рішення:** Повна міграція на CodeIssue, видалення Vulnerability
**Обґрунтування:** Internal API, немає зовнішніх споживачів, спрощує код
**Вплив:** ReviewResult.vulnerabilities → ReviewResult.issues

### Рішення 8: 2026-01-24 — Compact формат для inline comments
**Питання:** Чи потрібен окремий формат для inline comments?
**Рішення:** Так, format_inline_comment() — максимально стиснутий формат
**Обґрунтування:** Inline comments мають обмежений простір, не потрібен Before/After та collapsible
**Вплив:** Додано окрему функцію format_inline_comment()

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
- Завдань виконано: 6/10
- Покриття тестами: 93%
- Рядків коду: ~1100
- Нових файлів: 4 (base.py, time.py, gitlab.py, language.py)
- Тестів: 300
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
