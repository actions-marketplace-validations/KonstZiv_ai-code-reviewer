# Канвас прогресу Спрінту 1 (Розширений) — MVP Code Reviewer

**Початок спрінту:** 2026-01-20
**Мета спрінту:** MVP з GitHub + GitLab, Inline Comments, WOW-ефект
**Статус:** 🚧 В роботі

---

## 📊 Огляд спрінту

| Метрика | Ціль | Поточне | Статус |
|---------|------|---------|--------|
| **Завдань виконано** | 10/10 | 8/10 | 🏗️ |
| **Покриття тестами** | ≥80% | 92% | ✅ |
| **GitHub інтеграція** | ✅ Працює | ✅ GitProvider ABC | ✅ |
| **GitLab інтеграція** | ✅ Працює | ✅ GitLabClient готовий | ✅ |
| **Inline Comments** | ✅ Apply button | ✅ WOW-форматування готове | ✅ |
| **Мовна адаптивність** | ✅ Працює | ✅ ISO 639 + Proximity Rule | ✅ |
| **Метрики** | ✅ В footer | ✅ Tokens, latency, cost | ✅ |
| **Docker image** | ✅ Опубліковано | ✅ Локально 325MB | 🏗️ Публікація в Task 8 |
| **GitHub Action** | ✅ Marketplace | ✅ action.yml готовий | 🏗️ Публікація в Task 8 |
| **PyPI package** | ✅ v0.1.0 | ⏳ Не опубліковано | ⏳ Task 8 |

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

Рефакторинг за ревʼю:
- DEFAULT_MODEL константа замість hardcoded string
- model_copy(update=...) замість model_dump() + model_validate()
- Тести оновлено для використання DEFAULT_MODEL

300 тестів, 93% coverage
```

---

### 🐳 Завдання 5: Контейнеризація та локальна підготовка
**Статус:** ✅ **ЗАВЕРШЕНО** (2026-01-24)
**Верифіковано:** ✅ (2026-01-25)
**Призначено:** Claude Code (AI)
**Оцінка часу:** 3 години

**Чеклист:**
- [x] Створено multi-stage `Dockerfile`
- [x] Створено `.dockerignore`
- [x] Створено `action.yml`
- [x] Створено `examples/github-workflow.yml`
- [x] Створено `examples/gitlab-ci.yml`
- [x] Створено `examples/README.md`
- [x] Docker image збирається локально
- [x] `action.yml` валідний

> **Примітка:** Публікація на GHCR, DockerHub та GitHub Marketplace перенесена в Завдання 8

**Верифікація (2026-01-25):**
| Перевірка | Результат |
|-----------|-----------|
| Docker build | ✅ Success, 325MB |
| `ai-review --help` | ✅ CLI працює |
| Non-root user | ✅ `appuser` |
| git CLI | ✅ `git version 2.39.5` |
| Health check | ✅ 30s interval |
| Файли examples/ | ✅ 3 файли |

**Нотатки:**
```
Dockerfile:
- Multi-stage build: builder + runtime
- Builder: ghcr.io/astral-sh/uv:python3.13-bookworm-slim (uv для швидкого встановлення)
- Runtime: python:3.13-slim-bookworm (мінімальний образ)
- Розмір образу: 325MB
- Non-root user (appuser) для безпеки
- Health check: ai-review --help
- git CLI включено (потрібен для GitPython)
- Editable install: .venv + src копіюються в runtime

.dockerignore:
- Виключає tests/, docs/, .git, IDE файли, __pycache__, тощо
- Мінімізує context для швидкої збірки

action.yml (GitHub Action):
- Inputs: github_token, google_api_key, language, language_mode, gemini_model, log_level
- Docker runner з Dockerfile
- Environment variables автоматично передаються

examples/:
- github-workflow.yml: повний приклад workflow для GitHub Actions
  - Concurrency group для prevent duplicate reviews
  - Skip if PR is from fork (no secrets)
  - Permissions: contents read, pull-requests write
- gitlab-ci.yml: шаблон для GitLab CI
  - Rules: only merge_request_event
  - CI_JOB_TOKEN автоматично доступний
  - allow_failure: true
- README.md: документація з Quick Start та Troubleshooting

Проблема вирішена:
- uv sync створює editable install (.pth файл → /app/src)
- Потрібно копіювати src в runtime stage
- COPY --from=builder /app/src /app/src
```

---

### 🧪 Завдання 6: Тестування та стійкість
**Статус:** ✅ **ЗАВЕРШЕНО** (2026-01-25)
**Призначено:** Claude Code (AI)
**Оцінка часу:** 4 години

**Чеклист:**
- [x] Створено `utils/retry.py`
- [x] Retry decorators додано до API clients
- [x] Error handling wrapper створено
- [x] Retry tests написано (33 тести)
- [x] Оновлено тести GitHub/GitLab/Gemini для нових exceptions
- [x] Логи структуровані (attempt, error_type, retry_in_ms)

**Exception Hierarchy:**
| Тип | Base | Retry? | HTTP Code |
|-----|------|--------|-----------|
| `RateLimitError` | `RetryableError` | ✅ | 429 |
| `ServerError` | `RetryableError` | ✅ | 5xx |
| `AuthenticationError` | `APIClientError` | ❌ Fail Fast | 401 |
| `ForbiddenError` | `APIClientError` | ❌ Fail Fast | 403 |
| `NotFoundError` | `APIClientError` | ❌ Fail Fast | 404 |

**Retry Configuration:**
- Max attempts: 5
- Backoff: exponential (2s → 30s)
- Logging: attempt, error_type, retry_in_ms

**Нотатки:**
```
Створено utils/retry.py:
- Ієрархія exceptions: RetryableError → RateLimitError, ServerError
- APIClientError → AuthenticationError, ForbiddenError, NotFoundError
- APIError з контекстом (provider, operation, original_error)
- @with_retry decorator з tenacity
- _log_retry_attempt() callback для логування
- raise_for_status(), is_retryable_status() helpers
- Новий синтаксис Python 3.12+ type parameters [**P, R]

Оновлено API clients:
- github.py: _convert_github_exception(), @with_retry на методах
- gitlab.py: _convert_gitlab_exception() з mapping dict, @with_retry
- gemini.py: _convert_google_exception(), @with_retry на generate_review()

Тести:
- tests/unit/test_retry.py: 33 нових тести
- tests/integration/test_github.py: оновлено для exceptions
- tests/integration/test_gitlab.py: оновлено для exceptions
- tests/integration/test_gemini.py: додано error handling тести

Виправлення ruff/mypy:
- Додано `-> None` до всіх __init__ методів
- Винесено f-string в змінні для exceptions
- Рефакторинг _convert_gitlab_exception з mapping dict
- Додано google.api_core.* до mypy overrides

343 тести, 92% coverage
```

---

### 📚 Завдання 7: Багатомовна документація
**Статус:** ⏳ Очікує Завдання 6
**Призначено:** Claude Code (AI) + Human (review)
**Оцінка часу:** 6 годин

---

**Фаза 0: Узгодження структури** (Claude + Human)
- [ ] Обговорити фінальну структуру docs/
- [ ] Визначити список файлів для MVP
- [ ] Узгодити i18n підхід (uk → en → інші)
- [ ] Затвердити структуру

**Фаза 1: Створення** (Claude)
- [ ] Налаштувати MkDocs + mkdocs-material
- [ ] Налаштувати i18n плагін
- [ ] Створити структуру директорій
- [ ] Написати документацію **українською** (uk/):
  - [ ] index.md (landing)
  - [ ] quick-start.md (GitHub + GitLab)
  - [ ] configuration.md (всі опції)
  - [ ] github.md (platform-specific)
  - [ ] gitlab.md (platform-specific)
  - [ ] troubleshooting.md (FAQ + errors)

**Фаза 2: Вичитка** (Human)
- [ ] Прочитати uk/ версію
- [ ] Внести правки/коментарі
- [ ] Затвердити фінальний текст

**Фаза 3: Переклад** (Claude)
- [ ] Перекласти на English (en/) — primary
- [ ] Перекласти на Deutsch (de/)
- [ ] Перекласти на Español (es/)
- [ ] Перекласти на Crnogorski (me/)
- [ ] Перекласти на Italiano (it/)

**Фаза 4: Деплой** (Claude)
- [ ] Перемикач мов працює
- [ ] GitHub Pages / GitLab Pages налаштовано
- [ ] Автодеплой працює

---

**Статус мов:**
| Мова | Код | Фаза 1 | Фаза 2 | Фаза 3 |
|------|-----|--------|--------|--------|
| 🇺🇦 Українська | uk | ⏳ | ⏳ | — |
| 🇬🇧 English | en | — | — | ⏳ |
| 🇩🇪 Deutsch | de | — | — | ⏳ |
| 🇪🇸 Español | es | — | — | ⏳ |
| 🇲🇪 Crnogorski | me | — | — | ⏳ |
| 🇮🇹 Italiano | it | — | — | ⏳ |

**Структура docs/ (MVP):**
```
docs/
  uk/                 ← Source of truth (пишеться першою)
    index.md
    quick-start.md
    configuration.md
    github.md
    gitlab.md
    troubleshooting.md
  en/                 ← Primary for international
  de/
  es/
  me/
  it/
mkdocs.yml
```

**Нотатки:**
```
Workflow:
1. UK пишеться першою — Human вичитує рідною мовою
2. Після затвердження — переклад на всі мови
3. EN стає "primary" для міжнародної аудиторії
4. Виправлення робляться один раз до перекладу

Ref: CURRENT_TASK/ai_reviewer_documentation_structure.md
```

---

### 🔄 Завдання 8: CI/CD Pipeline та публікація
**Статус:** ⏳ Очікує Завдання 6, 7
**Призначено:** Claude Code (AI) + Human (secrets)
**Оцінка часу:** 4 години

**Чеклист — Workflows:**
- [ ] `tests.yml` оновлено для CLI tests
- [ ] `release.yml` оновлено для повного pipeline
- [ ] `docker-publish.yml` створено

**Чеклист — Docker публікація:**
- [ ] GHCR публікація працює (`ghcr.io/konstziv/ai-code-reviewer`)
- [ ] DockerHub публікація працює (`konstziv/ai-code-reviewer`)
- [ ] Multi-platform build (linux/amd64, linux/arm64)
- [ ] `DOCKERHUB_README.md` створено
- [ ] DockerHub secrets налаштовано (DOCKERHUB_USERNAME, DOCKERHUB_TOKEN)

**Чеклист — GitHub Marketplace:**
- [ ] `action.yml` оновлено для Marketplace
- [ ] README.md містить документацію Action
- [ ] Release створено з тегом v1.0.0
- [ ] Action опублікований на Marketplace

**Чеклист — PyPI:**
- [ ] Trusted Publisher налаштовано на PyPI
- [ ] `release.yml` публікує на PyPI
- [ ] `pip install ai-code-reviewer` працює

**Workflows:**
| Workflow | Файл | Статус |
|----------|------|--------|
| Tests | `tests.yml` | ✅ Існує |
| AI Review | `ai-review.yml` | ✅ Існує |
| Release | `release.yml` | ✅ Існує, потрібно оновити |
| Docker | `docker-publish.yml` | ⏳ Потрібно створити |

**Secrets потрібні (Human task):**
| Secret | Де налаштувати | Статус |
|--------|----------------|--------|
| `DOCKERHUB_USERNAME` | GitHub Repo Settings | ⏳ |
| `DOCKERHUB_TOKEN` | GitHub Repo Settings | ⏳ |
| PyPI Trusted Publisher | pypi.org Settings | ⏳ |

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
| utils/retry.py | ≥90% | 87% | ✅ |
| cli.py | ≥80% | 88% | ✅ |
| reviewer.py | ≥80% | 94% | ✅ |
| **Загалом** | **≥80%** | **92%** | ✅ |

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
Завдання 5 (Docker)         ██████████  ✅ Завершено
    ↓
Завдання 6 (Testing)        ██████████  ✅ Завершено
    ↓
Завдання 7 (Docs)           ░░░░░░░░░░  🎯 Наступне
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
Завдання 7: Багатомовна документація
- Налаштувати i18n плагін для MkDocs
- Створити структуру директорій
- Написати документацію 6 мовами
```

### Прогрес з останнього оновлення
```
✅ Завдання 6 (Testing/Retry) - ЗАВЕРШЕНО (2026-01-25)
  - Створено utils/retry.py з повною ієрархією exceptions
  - RetryableError → RateLimitError, ServerError (retry з backoff)
  - APIClientError → AuthenticationError, ForbiddenError, NotFoundError (fail fast)
  - @with_retry decorator з tenacity (5 attempts, 2s-30s backoff)
  - Оновлено GitHub, GitLab, Gemini clients
  - 33 нових тести для retry module
  - Оновлено інтеграційні тести для нової поведінки
  - Виправлено всі ruff/mypy issues
  - 343 тести, 92% coverage
  - Всі pre-commit hooks проходять
```

### Блокери
```
Немає
```

### Питання
```
Немає - готовий до виконання Завдання 7 (Documentation)
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

### Рішення 9: 2026-01-24 — DEFAULT_MODEL константа
**Питання:** Як уникнути hardcoded model name в GeminiClient?
**Рішення:** Винести default model name в константу DEFAULT_MODEL
**Обґрунтування:** Краща читабельність, легше змінювати, тести використовують константу
**Вплив:** GeminiClient.__init__(model_name=DEFAULT_MODEL), тести оновлено

### Рішення 10: 2026-01-24 — Base image для Docker
**Питання:** Який базовий образ використовувати для Docker?
**Рішення:** ghcr.io/astral-sh/uv:python3.13-bookworm-slim (builder) + python:3.13-slim-bookworm (runtime)
**Обґрунтування:**
- Alpine не підходить (pydantic-core має Rust extension, потрібен manylinux)
- uv образ = швидке встановлення залежностей
- Slim bookworm = мінімальний розмір + glibc для wheels
**Вплив:** Образ 325MB, multi-stage build

### Рішення 11: 2026-01-25 — Перенесення публікації з Завдання 5 в Завдання 8
**Питання:** Чи має Завдання 5 включати публікацію на GHCR/DockerHub/Marketplace?
**Рішення:** Ні, публікацію перенесено в Завдання 8 (CI/CD Pipeline)
**Обґрунтування:**
- Завдання 5 фокусується на локальній підготовці (Dockerfile, action.yml, examples)
- Публікація логічно належить до CI/CD pipeline
- Потребує налаштування secrets (Human task)
- Завдання 8 вже включало docker-publish.yml
**Вплив:**
- Завдання 5: тільки локальна збірка та підготовка файлів
- Завдання 8: розширено з публікацією на GHCR, DockerHub, GitHub Marketplace, PyPI
- Оцінка часу Завдання 8: 2→4 години

### Рішення 12: 2026-01-25 — Ієрархія exceptions для retry
**Питання:** Яку структуру exceptions використовувати для retry logic?
**Рішення:** Дві гілки: RetryableError (retry) та APIClientError (fail fast)
**Обґрунтування:**
- RetryableError → RateLimitError (429), ServerError (5xx) — тимчасові помилки
- APIClientError → AuthenticationError (401), ForbiddenError (403), NotFoundError (404) — fail fast
- Чітке розділення: retry vs immediate failure
- tenacity retry_if_exception_type(RetryableError) для автоматичного retry
**Вплив:**
- Уніфікована обробка помилок у всіх API clients
- Максимум 5 спроб з exponential backoff (2s → 30s)
- Структуроване логування: attempt, error_type, retry_in_ms

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

### Проблема 3: Docker editable install — 2026-01-24
**Проблема:** `ModuleNotFoundError: No module named 'ai_reviewer'` при запуску контейнера
**Причина:** uv sync створює editable install (.pth файл вказує на /app/src), але src не копіюється в runtime stage
**Рішення:** Додано `COPY --from=builder /app/src /app/src` в runtime stage
**Статус:** ✅ Виправлено

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
- Pydantic model_copy(update=...) ефективніший за model_dump() + model_validate()
- Google GenAI SDK повертає usage_metadata з token counts
- uv sync створює editable install — потрібно копіювати src в runtime
- Multi-stage Docker: uv image для build, slim python для runtime
- GitPython потребує git CLI в контейнері
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
- Завдань виконано: 8/10
- Покриття тестами: 92%
- Рядків коду: ~1200
- Нових файлів: 10 (base.py, time.py, gitlab.py, language.py, retry.py, Dockerfile, action.yml, .dockerignore, examples/*.yml)
- Тестів: 343
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
