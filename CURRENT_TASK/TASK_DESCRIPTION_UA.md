# Спрінт 1 (Розширений): MVP Code Reviewer — GitHub, GitLab & WOW-ефект

**Мета спрінту:** Створити надійний, стійкий до помилок інструмент з підтримкою GitHub та GitLab, який вражає користувачів якістю та зручністю

**Тривалість:** 1 спрінт (гнучко)
**Статус:** 🚧 В роботі
**Тип:** Фундаментальний спрінт
**Пріоритет:** Критичний

---

## 🎯 Цілі спрінту

### Основна мета
Побудувати MVP, яке:
- ✅ Працює як з **GitHub**, так і з **GitLab**
- ✅ Використовує **Inline Comments** з кнопкою "Apply Suggestion" (WOW!)
- ✅ Надає корисні, "менторські" рев'ю з поясненнями **чому** це важливо
- ✅ Автоматично визначає мову та відповідає нею (адаптивність)
- ✅ Стійке до помилок мережі (Retry logic) та інформативне при помилках
- ✅ Показує прозорі метрики (час, токени, вартість)

### Вторинна мета (найважливіша!)
**Верифікація всього ланцюжка розробки:**
- ✅ Інструменти якості коду (ruff, mypy, pre-commit)
- ✅ Тестовий pipeline (pytest + покриття ≥80%)
- ✅ CI/CD pipeline (тести, документація, реліз)
- ✅ Багатомовна документація (6 мов)
- ✅ Публікація в PyPI + Docker + GitHub Action

---

## 🎆 WOW-ефект: Ключові фічі

### Must-Have (реалізуємо в MVP)

1. **"Apply Suggestion" кнопка** — GitHub автоматично рендерить як інтерактивну кнопку
2. **Severity Badges з емодзі** — візуально зрозуміло з першого погляду
3. **Collapsible Learning Sections** — чистий UI з глибиною для тих, хто хоче вчитися
4. **Before/After Diff Preview** — наочно показує що змінити
5. **Summary Card з метриками** — професійний вигляд
6. **Positive Feedback** — мотивує розробників, відзначає хороші практики

---

## 📊 Критерії успіху

### Функціональні вимоги
1. ✅ Працює на GitHub Actions та GitLab CI
2. ✅ Автоматично визначає провайдера (GitHub/GitLab)
3. ✅ Публікує **Inline Comments** з конкретними suggestions
4. ✅ Визначає мову з контексту (PR опис, task, коментарі)
5. ✅ Надає "менторські" пояснення з посиланнями на ресурси
6. ✅ Показує метрики (час виконання, токени, вартість)
7. ✅ Документація на 6 мовах (uk, en, de, es, me, it)

### Технічні вимоги
1. ✅ Всі інструменти працюють: ruff, mypy, pytest, pre-commit
2. ✅ CI проходить: якість, тести, збірка документації
3. ✅ CD працює: тег → PyPI + Docker + деплой документації
4. ✅ Покриття тестами ≥80%
5. ✅ Type hints на всіх функціях
6. ✅ Retry logic для 429/5xx помилок
7. ✅ Fail Fast з чіткими повідомленнями для 4xx помилок

---

## 🏗️ Архітектура

### Високорівневий потік
```
PR/MR створено/оновлено
    ↓
CI запущено (GitHub Actions / GitLab CI)
    ↓
Перевірки якості (ruff, mypy)
    ↓
Тести (pytest)
    ↓
AI Reviewer Job
    ↓
[Визначити провайдера] → [Отримати дані MR/PR] → [Отримати linked task]
    ↓
[Визначити мову] → [Побудувати контекст] → [Надіслати до Gemini]
    ↓
[Парсити відповідь] → [Форматувати WOW-output]
    ↓
[Опублікувати Inline Comments + Summary]
```

### Структура коду
```python
src/ai_reviewer/
├── core/
│   ├── models.py          # Pydantic моделі (CodeIssue, GoodPractice, etc.)
│   ├── config.py          # Settings + LanguageMode
│   └── formatter.py       # WOW-форматування Markdown
│
├── integrations/
│   ├── base.py            # GitProvider ABC + LineComment
│   ├── github.py          # GitHubClient(GitProvider)
│   ├── gitlab.py          # GitLabClient(GitProvider)
│   ├── gemini.py          # GeminiClient
│   └── prompts.py         # System prompt + prompt builder
│
├── utils/
│   ├── retry.py           # Retry decorators (tenacity)
│   ├── time.py            # ensure_timezone utility
│   └── language.py        # Language detection helpers
│
├── reviewer.py            # Основна логіка оркестрації
└── cli.py                 # Typer CLI + auto-detection
```

### Моделі даних

```python
# === Enums ===
class LanguageMode(str, Enum):
    ADAPTIVE = "adaptive"  # Визначає з контексту
    FIXED = "fixed"        # Завжди вказана мова

class IssueSeverity(str, Enum):
    CRITICAL = "critical"      # Must fix (security)
    WARNING = "warning"        # Should fix
    INFO = "info"              # Educational/minor

class IssueCategory(str, Enum):
    SECURITY = "security"
    CODE_QUALITY = "code_quality"
    ARCHITECTURE = "architecture"
    PERFORMANCE = "performance"
    TESTING = "testing"

# === Core Models ===
class CodeIssue(BaseModel):
    """Універсальна модель для всіх типів issues."""
    category: IssueCategory
    severity: IssueSeverity
    title: str
    description: str
    file_path: str | None = None
    line_number: int | None = None

    # Для inline suggestions
    existing_code: str | None = None
    proposed_code: str | None = None

    # Educational (для juniors)
    why_matters: str | None = None
    learn_more_url: str | None = None

class GoodPractice(BaseModel):
    """Позитивний фідбек для мотивації."""
    description: str
    file_path: str | None = None

class ReviewMetrics(BaseModel):
    """Метрики виконання ревʼю."""
    duration_seconds: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost_usd: float

class ReviewResult(BaseModel):
    """Результат AI ревʼю."""
    summary: str
    issues: tuple[CodeIssue, ...]
    good_practices: tuple[GoodPractice, ...]
    task_alignment: TaskAlignmentStatus
    task_alignment_reasoning: str
    metrics: ReviewMetrics
    detected_language: str

# === Git Provider Abstraction ===
@dataclass
class LineComment:
    """Коментар для публікації в Git."""
    path: str
    line: int
    body: str
    suggestion: str | None = None

class GitProvider(ABC):
    @abstractmethod
    def get_merge_request(self, mr_id: int) -> MergeRequest: ...

    @abstractmethod
    def get_linked_task(self, mr: MergeRequest) -> LinkedTask | None: ...

    @abstractmethod
    def submit_review(
        self,
        mr_id: int,
        summary: str,
        line_comments: list[LineComment]
    ) -> None: ...
```

---

## 📋 Беклог спрінту (10 завдань)

### Завдання 1: Фундамент та виправлення 🔧
**Мета:** Забезпечити стабільний запуск CLI та коректну роботу

**Статус:** ⏳ Очікує
**Оцінка часу:** 2 години

**Кроки:**
1. Виправити entry point в `pyproject.toml` (app замість main)
2. Створити `ensure_timezone()` утиліту для datetime
3. Додати `LanguageMode` enum в Settings
4. Додати `api_timeout` в Settings
5. Додати `@lru_cache` для `get_settings()`
6. Оновити залежності (tenacity, structlog)

**Критерії прийняття:**
- ✅ `ai-review --help` працює коректно
- ✅ Pydantic не падає при обробці дат
- ✅ Нові налаштування доступні через env vars

**Файли:**
- `pyproject.toml` (виправлення)
- `src/ai_reviewer/core/config.py` (оновлення)
- `src/ai_reviewer/utils/time.py` (новий)

---

### Завдання 2: Архітектура провайдерів (Adapter) 🔌
**Мета:** Уніфікувати інтерфейс для GitHub/GitLab з підтримкою Inline Comments

**Статус:** ⏳ Очікує
**Оцінка часу:** 3 години

**Кроки:**
1. Створити `GitProvider` ABC в `base.py`
2. Створити `LineComment` dataclass
3. Рефакторити `GitHubClient` для наслідування `GitProvider`
4. Реалізувати `submit_review()` з batch posting
5. Оновити `reviewer.py` для використання інтерфейсу

**Критерії прийняття:**
- ✅ `GitHubClient` імплементує `GitProvider`
- ✅ `reviewer.py` не імпортує конкретні клієнти напряму
- ✅ Inline comments публікуються через GitHub Review API

**Файли:**
- `src/ai_reviewer/integrations/base.py` (новий)
- `src/ai_reviewer/integrations/github.py` (рефакторинг)
- `src/ai_reviewer/reviewer.py` (оновлення)

---

### Завдання 3: Інтеграція GitLab 🦊
**Мета:** Реалізувати повну підтримку GitLab API

**Статус:** ⏳ Очікує
**Оцінка часу:** 4 години

**Кроки:**
1. Створити `GitLabClient(GitProvider)` в `gitlab.py`
2. Реалізувати `get_merge_request()` з маппінгом полів
3. Реалізувати `get_linked_task()` через regex
4. Реалізувати `submit_review()` через Discussions API
5. Додати `GITLAB_TOKEN`, `GITLAB_URL` в Settings
6. Оновити CLI для GitLab context extraction
7. Написати інтеграційні тести

**Критерії прийняття:**
- ✅ `ai-review --provider gitlab` працює
- ✅ Inline comments з'являються як Threads в GitLab
- ✅ Self-hosted GitLab підтримується через `GITLAB_URL`

**GitLab CI змінні:**
```bash
CI_MERGE_REQUEST_IID      # Номер MR
CI_PROJECT_PATH           # owner/repo
CI_SERVER_URL             # URL інстансу
GITLAB_TOKEN              # Access token
```

**Файли:**
- `src/ai_reviewer/integrations/gitlab.py` (новий, ~250 рядків)
- `src/ai_reviewer/core/config.py` (оновлення)
- `src/ai_reviewer/cli.py` (оновлення)
- `tests/integration/test_gitlab.py` (новий)

---

### Завдання 4a: Мовна адаптивність 🌍
**Мета:** Автоматичне визначення мови відповіді з валідацією ISO 639

**Статус:** ✅ Завершено
**Оцінка часу:** 3 години

**Алгоритм "Proximity Rule":**
1. Зібрати тексти: `[Task.desc, MR.desc, Comments...]`
2. Відфільтрувати короткі (< 20 слів)
3. Взяти останній достатньо довгий текст
4. Включити в prompt інструкцію для LLM визначити мову

**Валідація мовного коду (ISO 639):**
Використовуємо бібліотеку `python-iso639` для валідації параметра `LANGUAGE`:
- Приймаються всі валідні ISO 639 коди (639-1, 639-2, 639-3)
- Приймаються назви мов (English, Ukrainian, Deutsch...)
- Автоматична нормалізація до ISO 639-1 (дволітерний код)
- Для мов без ISO 639-1 зберігається ISO 639-3

```python
# Приклади нормалізації:
"en" → "en"           # ISO 639-1 залишається
"ukr" → "uk"          # ISO 639-3 → ISO 639-1
"Ukrainian" → "uk"    # Назва → ISO 639-1
"yue" → "yue"         # Cantonese (немає 639-1, залишається 639-3)
"invalid" → ValidationError  # Невалідний код
```

**Кроки:**
1. ✅ Додати залежність `python-iso639` в `pyproject.toml`
2. ✅ Створити валідатор `_validate_language_code()` в `config.py`
3. ✅ Застосувати валідатор до поля `language` в Settings
4. ✅ Написати тести для валідації мови
5. ✅ Створити `src/ai_reviewer/utils/language.py`
6. ✅ Реалізувати `collect_text_samples()`, `build_language_instruction()`
7. ✅ Оновити system prompt для адаптивності
8. ✅ Додати `detected_language` в `ReviewResult`
9. ✅ Інтегрувати в `reviewer.py`
10. ✅ Написати тести (15 нових тестів)

**Конфігурація:**
```bash
LANGUAGE=uk              # Мова за замовчуванням (ISO 639 код або назва)
LANGUAGE_MODE=adaptive   # adaptive | fixed
```

**Критерії прийняття:**
- ✅ Валідація мовного коду за ISO 639 (всі частини стандарту)
- ✅ Нормалізація до ISO 639-1 де можливо
- ✅ Чіткі повідомлення про помилки для невалідних кодів
- ✅ Бот відповідає українською, якщо PR description українською
- ✅ `LANGUAGE_MODE=fixed` примусово використовує `LANGUAGE`
- ✅ Fallback на англійську якщо не вдалося визначити

**🇺🇦 Спеціальне повідомлення для російської мови:**

При виборі російської мови (`ru`, `rus`, `Russian`) до кожного issue review додається footer:

```markdown
<sub>каждый россиянин, имеющий честь, должен делать все для возвращения
украденного/уничтоженного его страной в других странах и учить этому своих детей.
Слава Украине!</sub>
```

Це реалізується в `formatter.py` при форматуванні inline comments та summary.

**Файли:**
- `pyproject.toml` (залежність python-iso639) ✅
- `src/ai_reviewer/core/config.py` (валідатор ISO 639) ✅
- `src/ai_reviewer/utils/language.py` (новий) ✅
- `src/ai_reviewer/integrations/prompts.py` (оновлення) ✅
- `src/ai_reviewer/core/models.py` (detected_language) ✅
- `src/ai_reviewer/core/formatter.py` (footer для російської) ✅
- `src/ai_reviewer/reviewer.py` (інтеграція) ✅
- `tests/unit/test_language.py` (новий, 15 тестів) ✅

---

### Завдання 4b: Розширена структура ревʼю та WOW-форматування 🎨
**Мета:** Створити візуально привабливий, інформативний output

**Статус:** ⏳ Очікує
**Оцінка часу:** 4 години

**Включає:**
1. Unified `CodeIssue` модель з категоріями
2. `GoodPractice` для позитивного фідбеку
3. `why_matters` + `learn_more_url` для навчання
4. WOW-форматування в Markdown

**Структура output:**
```markdown
# 🤖 AI Code Review

## 📊 Summary
Brief overview + metrics table

## 🔒 Security Issues (if any)
Critical issues with Apply Suggestion buttons

## 📝 Code Quality
Suggestions with Before/After diffs

## 💡 Learning Points
<details>
<summary>Why is this important?</summary>
Explanation + resources
</details>

## ✨ Good Practices
Positive feedback to motivate!

## 📋 Task Alignment
Does code match requirements?

---
⏱️ 2.3s | 🪙 1540 tokens | 💰 ~$0.003
```

**Кроки:**
1. Оновити моделі в `models.py`
2. Оновити system prompt в `prompts.py`
3. Переписати `formatter.py` з WOW-форматуванням
4. Додати GitHub suggestion syntax
5. Додати collapsible sections

**Критерії прийняття:**
- ✅ Inline comments мають "Apply suggestion" кнопку
- ✅ Learning sections є collapsible
- ✅ Good practices відображаються
- ✅ Summary містить метрики

**Файли:**
- `src/ai_reviewer/core/models.py` (оновлення)
- `src/ai_reviewer/core/formatter.py` (переписати)
- `src/ai_reviewer/integrations/prompts.py` (оновлення)

---

### Завдання 4c: Метрики виконання 📈
**Мета:** Відображати час, токени та вартість

**Статус:** ⏳ Очікує
**Оцінка часу:** 2 години

**Кроки:**
1. Створити `ReviewMetrics` модель
2. Інструментувати `GeminiClient` для збору метрик
3. Обчислювати estimated cost (Gemini pricing)
4. Додати footer з метриками в output

**Pricing (Gemini Flash):**
```python
GEMINI_FLASH_PRICING = {
    "input": 0.075 / 1_000_000,   # $0.075 per 1M tokens
    "output": 0.30 / 1_000_000,   # $0.30 per 1M tokens
}
```

**Критерії прийняття:**
- ✅ Метрики збираються під час ревʼю
- ✅ Footer показує: ⏱️ Xs | 🪙 N tokens | 💰 ~$X.XXX
- ✅ Вартість обчислюється коректно

**Файли:**
- `src/ai_reviewer/core/models.py` (ReviewMetrics)
- `src/ai_reviewer/integrations/gemini.py` (інструментація)
- `src/ai_reviewer/core/formatter.py` (footer)

---

### Завдання 5: Контейнеризація та локальна підготовка 🐳
**Мета:** Підготувати Docker image та GitHub Action для подальшої публікації

**Статус:** ⏳ Очікує
**Оцінка часу:** 3 години

**Кроки:**
1. Створити multi-stage `Dockerfile`
2. Створити `action.yml` для GitHub Action
3. Створити приклади CI конфігурацій
4. Створити `.dockerignore` для оптимізації збірки

**Dockerfile:**
```dockerfile
# Stage 1: Builder
FROM python:3.13-slim as builder
WORKDIR /app
RUN pip install uv
COPY pyproject.toml uv.lock ./
RUN uv export > requirements.txt
RUN pip install --target=/deps -r requirements.txt

# Stage 2: Runtime
FROM python:3.13-slim
COPY --from=builder /deps /usr/local/lib/python3.13/site-packages
COPY src/ /app/src/
WORKDIR /app
ENTRYPOINT ["python", "-m", "ai_reviewer.cli"]
```

**GitHub Action (action.yml):**
```yaml
name: 'AI Code Reviewer'
description: 'AI-powered code review with inline suggestions'
branding:
  icon: 'eye'
  color: 'purple'
inputs:
  google_api_key:
    description: 'Google Gemini API Key'
    required: true
  language:
    description: 'Response language (en, uk, de, etc.)'
    default: 'en'
  language_mode:
    description: 'adaptive or fixed'
    default: 'adaptive'
runs:
  using: 'composite'
  steps:
    - uses: actions/setup-python@v5
      with:
        python-version: '3.13'
    - run: pip install ai-reviewbot
      shell: bash
    - run: ai-review
      shell: bash
      env:
        GITHUB_TOKEN: ${{ github.token }}
        GOOGLE_API_KEY: ${{ inputs.google_api_key }}
        LANGUAGE: ${{ inputs.language }}
        LANGUAGE_MODE: ${{ inputs.language_mode }}
```

**Використання (GitHub):**
```yaml
# .github/workflows/review.yml
- uses: KonstZiv/ai-code-reviewer@v1
  with:
    google_api_key: ${{ secrets.GOOGLE_API_KEY }}
    language: uk
```

**Використання (GitLab):**
```yaml
# .gitlab-ci.yml
ai-review:
  image: ghcr.io/konstziv/ai-reviewbot:latest
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  variables:
    GITLAB_TOKEN: $CI_JOB_TOKEN
    GOOGLE_API_KEY: $GOOGLE_API_KEY
```

**Критерії прийняття:**
- ✅ Docker image збирається локально та працює
- ✅ `action.yml` створено та валідний
- ✅ Приклади CI конфігурацій готові

**Файли:**
- `Dockerfile` (новий)
- `.dockerignore` (новий)
- `action.yml` (новий)
- `examples/github-workflow.yml` (новий)
- `examples/gitlab-ci.yml` (новий)
- `examples/README.md` (новий)

> **Примітка:** Публікація Docker image на GHCR/DockerHub та GitHub Marketplace винесена в Завдання 8 (CI/CD Pipeline)

---

### Завдання 6: Тестування та стійкість 🧪
**Мета:** Graceful degradation та comprehensive testing

**Статус:** ⏳ Очікує
**Оцінка часу:** 4 години

**Retry Logic (з tenacity):**
```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(
    retry=retry_if_exception_type((RateLimitError, ServerError)),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(5),
    before_sleep=log_retry_attempt
)
def api_call(): ...
```

**Fail Fast (без retry):**
- `401 Unauthorized` → Exit("❌ Invalid Token")
- `403 Forbidden` → Exit("❌ Permission Denied")
- `404 Not Found` → Exit("❌ PR/Repo not found")

**CLI Tests:**
```python
# tests/unit/test_cli.py
def test_detect_provider_github():
    with mock.patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}):
        assert detect_provider() == Provider.GITHUB

def test_extract_github_context():
    # Mock GITHUB_EVENT_PATH with PR payload
    ...

def test_main_missing_config():
    # Should exit with clear error message
    ...
```

**Кроки:**
1. Створити `src/ai_reviewer/utils/retry.py`
2. Додати retry decorators до API clients
3. Створити error handling wrapper
4. Написати unit tests для CLI (≥80% coverage)
5. Написати integration tests для retry logic

**Критерії прийняття:**
- ✅ Бот робить retry при 429/5xx (до 5 спроб)
- ✅ Бот виходить з чітким повідомленням при 4xx
- ✅ CLI має ≥80% test coverage
- ✅ Логи структуровані (для CI парсингу)

**Файли:**
- `src/ai_reviewer/utils/retry.py` (новий)
- `tests/unit/test_cli.py` (новий)
- `tests/integration/test_retry.py` (новий)

---

### Завдання 7: Багатомовна документація 📚
**Мета:** Документація на 6 мовах

**Статус:** ⏳ Очікує
**Оцінка часу:** 4 години

**Структура:**
```
docs/
├── index.md              # Redirect to /en/
├── en/
│   ├── index.md          # Overview
│   ├── quick-start.md    # 5-minute setup
│   ├── configuration.md  # All env vars
│   ├── github-setup.md   # GitHub Actions guide
│   └── gitlab-setup.md   # GitLab CI guide
├── uk/                   # Ukrainian
├── de/                   # German
├── es/                   # Spanish
├── me/                   # Montenegrin
└── it/                   # Italian
```

**mkdocs.yml:**
```yaml
plugins:
  - i18n:
      default_language: en
      languages:
        en: English
        uk: Українська
        de: Deutsch
        es: Español
        me: Crnogorski
        it: Italiano
```

**Критерії прийняття:**
- ✅ Перемикач мов працює
- ✅ Всі мови мають базову документацію
- ✅ Документація автоматично деплоїться

**Файли:**
- `docs/*/` (6 мов × 5 документів)
- `mkdocs.yml` (оновлення)

---

### Завдання 8: CI/CD Pipeline та публікація 🔄
**Мета:** Повна автоматизація release процесу + публікація на всіх платформах

**Статус:** 🚧 В роботі
**Оцінка часу:** 4 години
**Версія релізу:** `1.0.0a1`

---

#### Очікувані артефакти релізу

| Артефакт | Платформа | Опис |
|----------|-----------|------|
| README.md | GitHub | Якісний опис з badges, quick start, посиланнями |
| PyPI package | pypi.org | `pip install ai-reviewbot` |
| Docker image | DockerHub | `konstziv/ai-reviewbot` |
| Docker image | GHCR | `ghcr.io/konstziv/ai-reviewbot` |
| GitHub Action | Marketplace | `uses: KonstZiv/ai-code-reviewer@v1` |
| Documentation | GitHub Pages | 6 мов, детальна документація |

---

#### Архітектура workflows

**Структура файлів:**
```
.github/workflows/
├── tests.yml           # PR/push → тести + quality checks
├── docs.yml            # push to main → GitHub Pages
├── release.yml         # tag v*.*.* → PyPI + GitHub Release
├── docker-publish.yml  # після release → GHCR + DockerHub
└── ai-review.yml       # PR → self-review (dogfooding)
```

**Послідовність при релізі:**
```
git push --tags (v1.0.0a1)
    │
    ▼
┌─────────────────────────────────────┐
│  release.yml                        │
│  ├─ test (quality + pytest)         │
│  ├─ build (uv build → dist/)        │
│  ├─ publish-to-pypi                 │
│  └─ github-release                  │
└─────────────────────────────────────┘
    │ workflow_call (on success)
    ▼
┌─────────────────────────────────────┐
│  docker-publish.yml                 │
│  ├─ build multi-arch (amd64+arm64)  │
│  ├─ push to GHCR                    │
│  └─ push to DockerHub               │
└─────────────────────────────────────┘

push to main (окремо)
    │
    ▼
┌─────────────────────────────────────┐
│  docs.yml                           │
│  └─ deploy to GitHub Pages          │
└─────────────────────────────────────┘
```

**Рішення:**
- Docs deploy: тільки на push to main (завжди актуальна документація)
- Docker publish: **послідовно після PyPI** (консистентність артефактів)
- action.yml: **pre-built image** (швидкість для користувачів)

---

#### 8.1 Docker публікація (GHCR + DockerHub)

**docker-publish.yml:**
```yaml
name: Docker Publish

on:
  workflow_call:  # Викликається з release.yml після успіху
  workflow_dispatch:  # Ручний запуск для тестування

env:
  REGISTRY_GHCR: ghcr.io
  REGISTRY_DOCKER: docker.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - uses: actions/checkout@v4

      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY_GHCR }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Log in to DockerHub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: |
            ${{ env.REGISTRY_GHCR }}/${{ env.IMAGE_NAME }}
            ${{ env.REGISTRY_DOCKER }}/konstziv/ai-reviewbot
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=semver,pattern={{major}}
            type=raw,value=latest,enable=${{ !contains(github.ref, 'alpha') && !contains(github.ref, 'beta') && !contains(github.ref, 'rc') }}

      - name: Build and push
        uses: docker/build-push-action@v6
        with:
          context: .
          platforms: linux/amd64,linux/arm64
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

**DOCKERHUB_README.md:**
- Короткий опис проєкту
- Quick start з `docker run`
- Посилання на повну документацію
- Badges (version, pulls, size)

**Secrets потрібні:**
- `DOCKERHUB_USERNAME` — username на DockerHub
- `DOCKERHUB_TOKEN` — Access Token (не пароль!)

---

#### 8.2 GitHub Marketplace публікація

**Вимоги для Marketplace:**
1. Репозиторій має бути **публічним** ✅
2. `action.yml` в корені репозиторію ✅
3. Створити **Release** з semantic version tag
4. Детальний **README.md** з прикладами використання

**action.yml з pre-built image:**
```yaml
name: 'AI Code Reviewer'
description: 'AI-powered code review with inline suggestions and Apply button'
author: 'Kostyantin Zivenko'

branding:
  icon: 'code'
  color: 'blue'

inputs:
  github_token:
    description: 'GitHub token for API access (usually secrets.GITHUB_TOKEN)'
    required: true
  google_api_key:
    description: 'Google API key for Gemini'
    required: true
  language:
    description: 'Response language (ISO 639 code, e.g., en, uk, de)'
    required: false
    default: 'en'
  language_mode:
    description: 'Language mode: adaptive (detect from PR) or fixed'
    required: false
    default: 'adaptive'
  gemini_model:
    description: 'Gemini model to use'
    required: false
    default: 'gemini-2.5-flash'
  log_level:
    description: 'Log level (DEBUG, INFO, WARNING, ERROR)'
    required: false
    default: 'INFO'

runs:
  using: 'docker'
  image: 'docker://ghcr.io/konstziv/ai-reviewbot:latest'  # Pre-built для швидкості
  env:
    GITHUB_TOKEN: ${{ inputs.github_token }}
    GOOGLE_API_KEY: ${{ inputs.google_api_key }}
    LANGUAGE: ${{ inputs.language }}
    LANGUAGE_MODE: ${{ inputs.language_mode }}
    GEMINI_MODEL: ${{ inputs.gemini_model }}
    LOG_LEVEL: ${{ inputs.log_level }}
    GITHUB_ACTIONS: 'true'
```

**Кроки публікації на Marketplace:**
1. Створити Release з тегом `v1.0.0a1`
2. Поставити галочку "Publish this Action to the GitHub Marketplace"
3. Обрати категорії: `Code quality`, `Code review`

---

#### 8.3 PyPI публікація

**Trusted Publishing (без API token):**
1. pypi.org → Settings → Publishing → Add trusted publisher
2. Налаштування:
   - Owner: `KonstZiv`
   - Repository: `ai-code-reviewer`
   - Workflow: `release.yml`
   - Environment: `pypi`

**release.yml (вже існує, потрібні зміни):**
- Видалити `deploy-docs` job (переноситься в docs.yml)
- Додати виклик `docker-publish.yml` після успішного релізу

---

#### План виконання

**Фаза 1: Підготовка файлів (Claude)**

| # | Файл | Дія |
|---|------|-----|
| 1.1 | `pyproject.toml` | Версія `0.1.0` → `1.0.0a1` |
| 1.2 | `release.yml` | Видалити `deploy-docs`, додати виклик docker-publish |
| 1.3 | `docker-publish.yml` | Створити (GHCR + DockerHub, multi-arch) |
| 1.4 | `action.yml` | Pre-built image замість Dockerfile |
| 1.5 | `DOCKERHUB_README.md` | Створити |
| 1.6 | `README.md` | Створити (фінальний крок документації) |

**Фаза 2: Налаштування (Human)**

| # | Платформа | Дія |
|---|-----------|-----|
| 2.1 | PyPI | Trusted Publisher |
| 2.2 | GitHub | Secrets: `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN` |
| 2.3 | GitHub | Settings → Pages → gh-pages branch |

**Фаза 3: Реліз (Human)**

| # | Дія |
|---|-----|
| 3.1 | Merge to main |
| 3.2 | `git tag v1.0.0a1 && git push --tags` |
| 3.3 | GitHub Release + ✅ "Publish to Marketplace" |
| 3.4 | Верифікація всіх артефактів |

---

**Критерії прийняття:**
- ✅ Всі workflows зелені
- ✅ PyPI: `pip install ai-reviewbot` працює
- ✅ DockerHub: `docker pull konstziv/ai-reviewbot` працює
- ✅ GHCR: `docker pull ghcr.io/konstziv/ai-reviewbot` працює
- ✅ Marketplace: `uses: KonstZiv/ai-code-reviewer@v1` працює
- ✅ GitHub Pages: документація доступна на 6 мовах
- ✅ README.md: якісний опис з badges

**Файли:**
- `pyproject.toml` (версія)
- `.github/workflows/release.yml` (оновлення)
- `.github/workflows/docker-publish.yml` (новий)
- `action.yml` (pre-built image)
- `DOCKERHUB_README.md` (новий)
- `README.md` (новий)

---

### Завдання 9: Фінальна інтеграція та QA 🔍
**Мета:** End-to-end перевірка всього функціоналу

**Статус:** ⏳ Очікує
**Оцінка часу:** 3 години

**Кроки:**
1. Створити тестовий PR на GitHub з різними issues
2. Запустити AI reviewer вручну
3. Перевірити inline comments з Apply button
4. Перевірити мовну адаптивність
5. Створити тестовий MR на GitLab
6. Повторити перевірки для GitLab
7. Виправити знайдені баги

**Test Scenarios:**
- [ ] PR з security issue → Critical inline comment
- [ ] PR з code quality issues → Suggestions
- [ ] PR з хорошим кодом → Good practices
- [ ] PR українською → Відповідь українською
- [ ] PR без linked task → Appropriate messaging
- [ ] Network timeout → Retry та успіх
- [ ] Invalid token → Clear error message

**Критерії прийняття:**
- ✅ Всі test scenarios проходять
- ✅ UX відповідає очікуванням
- ✅ Метрики відображаються коректно

---

### Завдання 10: Реліз v0.1.0 🚀
**Мета:** Офіційний реліз MVP

**Статус:** ⏳ Очікує
**Оцінка часу:** 1 година

**Кроки:**
1. Оновити версію в `pyproject.toml`
2. Написати CHANGELOG.md
3. Створити тег `v0.1.0`
4. Перевірити PyPI publish
5. Перевірити Docker image в GHCR
6. Перевірити GitHub Release
7. Анонсувати реліз

**Критерії прийняття:**
- ✅ `pip install ai-reviewbot` працює
- ✅ Docker image доступний
- ✅ GitHub Action доступний через `uses:`
- ✅ Документація задеплоєна
- ✅ Release notes опубліковані

---

## 🧪 Стратегія тестування

### Покриття по модулях

| Модуль | Ціль | Тип тестів |
|--------|------|------------|
| `core/models.py` | ≥90% | Unit |
| `core/config.py` | ≥90% | Unit |
| `core/formatter.py` | ≥80% | Unit |
| `integrations/github.py` | ≥80% | Integration (mocked) |
| `integrations/gitlab.py` | ≥80% | Integration (mocked) |
| `integrations/gemini.py` | ≥80% | Integration (mocked) |
| `utils/retry.py` | ≥90% | Unit |
| `cli.py` | ≥80% | Unit + Integration |
| `reviewer.py` | ≥80% | E2E (mocked) |

### Тестові сценарії

**Unit Tests:**
- Валідація моделей
- Форматування output
- Language detection logic
- Retry logic

**Integration Tests:**
- GitHub API (mocked)
- GitLab API (mocked)
- Gemini API (mocked)

**E2E Tests:**
- Повний workflow з моками
- CLI запуск з env vars

---

## 📚 Довідкові матеріали

### API Documentation
- **GitHub REST API:** https://docs.github.com/en/rest
- **GitHub Review API:** https://docs.github.com/en/rest/pulls/reviews
- **GitLab API:** https://docs.gitlab.com/ee/api/
- **GitLab Discussions:** https://docs.gitlab.com/ee/api/discussions.html
- **Google Gemini:** https://ai.google.dev/docs

### Libraries
- **PyGithub:** https://pygithub.readthedocs.io/
- **python-gitlab:** https://python-gitlab.readthedocs.io/
- **tenacity:** https://tenacity.readthedocs.io/
- **Typer:** https://typer.tiangolo.com/

### GitHub Suggestion Syntax
```markdown
```suggestion
proposed code here
```⁣```
```

---

## 🎯 Визначення завершеності (Definition of Done)

Спрінт завершено коли:
1. ✅ Всі 10 завдань виконано
2. ✅ Покриття тестами ≥80%
3. ✅ CI/CD pipeline повністю зелений
4. ✅ GitHub + GitLab інтеграції працюють
5. ✅ Inline Comments з "Apply" кнопкою працюють
6. ✅ Мовна адаптивність працює
7. ✅ Метрики відображаються
8. ✅ Документація на 6 мовах задеплоєна
9. ✅ PyPI package опубліковано
10. ✅ Docker image опубліковано
11. ✅ GitHub Action доступний
12. ✅ Тег v0.1.0 створено

---

## 📌 Наступні кроки після спрінту

**Спрінт 2: Intelligence & Learning**
- Контекст репозиторію (історія, conventions)
- Multi-LLM router для оптимізації вартості
- Кешування та інкрементальні ревʼю
- Накопичувальна статистика
- Auto-fix PR creation

---

## 🤝 Нотатки для співпраці

**Для AI асистента (Claude):**
- Читай цей документ перед кожною сесією
- Оновлюй PROCESS_TASK_UA.md по мірі виконання
- Приоритизуй WOW-ефект у форматуванні
- Тестуй inline comments ретельно

**Для розробника:**
- Переглядай пропозиції AI
- Тестуй на реальних PR/MR
- Давай фідбек щодо UX
- Оновлюй документи за потреби

---

**Будуємо щось вражаюче! 🚀**
