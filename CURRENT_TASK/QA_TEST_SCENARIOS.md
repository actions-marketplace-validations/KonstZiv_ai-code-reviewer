# QA Test Scenarios — AI Code Reviewer v1.0.0a3

**Дата створення:** 2026-01-30
**Версія:** 1.0.0a3
**Статус:** Draft

---

## Загальні вимоги

### Передумови для всіх тестів

| Ресурс | Як отримати |
|--------|-------------|
| Google Gemini API Key | [Google AI Studio](https://aistudio.google.com/) → Get API Key |
| GitHub Personal Access Token | Settings → Developer settings → Personal access tokens → Fine-grained |
| GitLab Project Access Token | Project → Settings → Access Tokens (потрібна роль **Maintainer**) |

### Тестовий код для PR/MR

Використовуйте цей Python файл з навмисними проблемами:

```python
# test_code.py
import os
import pickle

def process_user_data(user_input):
    # SQL injection vulnerability
    query = f"SELECT * FROM users WHERE id = {user_input}"

    # Hardcoded credentials
    password = "admin123"
    api_key = "sk-1234567890abcdef"

    # Unsafe deserialization
    data = pickle.loads(user_input)

    # Missing input validation
    eval(user_input)

    return query

# Good practice: type hints
def calculate_total(items: list[float]) -> float:
    return sum(items)
```

### Формат звіту тестувальника

```markdown
## Тест: [Назва сценарію]
**Тестувальник:** [Ім'я]
**Дата:** [YYYY-MM-DD]
**Результат:** ✅ Passed / ❌ Failed / ⚠️ Partial

### Кроки виконання
| # | Крок | Очікуваний результат | Фактичний результат | Статус |
|---|------|---------------------|---------------------|--------|
| 1 | ... | ... | ... | ✅/❌ |

### Скріншоти
[Додати якщо потрібно]

### Знайдені проблеми
- [ ] Issue #X: Опис проблеми

### Коментарі
[Додаткові спостереження]
```

---

## Сценарій 1: GitHub Actions

**Мета:** Перевірити роботу AI Code Reviewer як GitHub Action (standalone та як частина CI).

**Документація:** [docs/uk/quick-start.md](../docs/uk/quick-start.md), [docs/uk/github.md](../docs/uk/github.md)

### Передумови
- [ ] GitHub репозиторій (публічний або приватний)
- [ ] `GOOGLE_API_KEY` додано в Repository Secrets
- [ ] Права на створення workflows

### Частина A: Standalone Workflow

| # | Крок | Дія | Очікуваний результат |
|---|------|-----|---------------------|
| 1 | Створити workflow | Створити `.github/workflows/ai-review.yml` (див. нижче) | Файл створено |
| 2 | Закомітити | Push workflow до main/master | Workflow з'явився в Actions |
| 3 | Створити PR | Створити branch, додати `test_code.py`, створити PR | PR створено |
| 4 | Дочекатись Action | Перевірити вкладку Actions | Workflow "AI Code Review" запустився |
| 5 | Перевірити результат | Перейти до PR → Conversation | AI залишив коментар з review |
| 6 | Перевірити inline | PR → Files changed | Є inline коментарі на проблемних рядках |
| 7 | Перевірити Apply | Клікнути "Apply suggestion" | Код змінився відповідно до suggestion |

**Standalone Workflow:**
```yaml
# .github/workflows/ai-review.yml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - name: AI Code Review
        uses: KonstZiv/ai-code-reviewer@v1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          google_api_key: ${{ secrets.GOOGLE_API_KEY }}
```

### Частина B: Останній крок CI

| # | Крок | Дія | Очікуваний результат |
|---|------|-----|---------------------|
| 1 | Оновити CI | Додати AI Review як останній job з `needs` | Workflow оновлено |
| 2 | Створити PR | PR з тестовим кодом | PR створено |
| 3 | Перевірити послідовність | Actions → Jobs | AI Review запускається після тестів |
| 4 | Перевірити залежність | Зробити тести fail | AI Review не запускається |
| 5 | Перевірити результат | При успішних тестах | AI залишає коментарі |

**CI Pipeline Workflow:**
```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: |
          echo "Running tests..."
          # pytest tests/

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run linter
        run: |
          echo "Running linter..."
          # ruff check .

  ai-review:
    runs-on: ubuntu-latest
    needs: [test, lint]  # Запускається тільки після успішних test і lint
    permissions:
      contents: read
      pull-requests: write
    steps:
      - name: AI Code Review
        uses: KonstZiv/ai-code-reviewer@v1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          google_api_key: ${{ secrets.GOOGLE_API_KEY }}
```

### Частина C: Тести конфігурації

| # | Тест | Конфігурація | Очікуваний результат |
|---|------|--------------|---------------------|
| C1 | Українська мова | `language: uk` | Review українською |
| C2 | Фіксована мова | `language: en`, `language_mode: fixed` | Review англійською, ігноруючи контекст PR |
| C3 | Інша модель | `gemini_model: gemini-1.5-pro` | Використовується Pro модель |
| C4 | Debug логи | `log_level: DEBUG` | Детальні логи в Actions |

**Workflow з конфігурацією:**
```yaml
- name: AI Code Review
  uses: KonstZiv/ai-code-reviewer@v1
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    google_api_key: ${{ secrets.GOOGLE_API_KEY }}
    language: uk
    language_mode: adaptive
    gemini_model: gemini-2.5-flash
    log_level: INFO
```

### Критерії успіху

- [ ] Workflow запускається автоматично при створенні PR
- [ ] Workflow завершується успішно (зелена галочка)
- [ ] В PR з'являється загальний коментар з review
- [ ] В "Files changed" є inline коментарі
- [ ] Коментарі вказують на реальні проблеми (SQL injection, hardcoded credentials)
- [ ] Кнопка "Apply suggestion" працює
- [ ] Конфігурація `language` впливає на мову review
- [ ] `needs` працює — AI Review чекає на попередні jobs

### Можливі помилки

| Помилка | Причина | Рішення |
|---------|---------|---------|
| "Resource not accessible by integration" | Немає прав `pull-requests: write` | Додати `permissions` блок |
| "GOOGLE_API_KEY not set" | Secret не створено | Settings → Secrets → New |
| Action показує `--help` | `github_token` не передано | Додати `github_token: ${{ secrets.GITHUB_TOKEN }}` |

---

## Сценарій 2: GitLab CI

**Мета:** Перевірити роботу AI Code Reviewer в GitLab CI pipeline.

**Документація:** [docs/uk/quick-start.md](../docs/uk/quick-start.md), [docs/uk/gitlab.md](../docs/uk/gitlab.md)

### Передумови
- [ ] GitLab репозиторій (gitlab.com або self-hosted)
- [ ] Project Access Token з scope `api` (роль **Maintainer**)
- [ ] `GOOGLE_API_KEY` та `GITLAB_TOKEN` в CI/CD Variables

### Налаштування токена

1. Project → Settings → Access Tokens
2. Token name: `ai-reviewer`
3. Role: **Maintainer** (обов'язково!)
4. Scopes: `api` (обов'язково!)
5. Create → скопіювати токен
6. Settings → CI/CD → Variables:
   - `GITLAB_TOKEN` = створений токен (Masked)
   - `GOOGLE_API_KEY` = ваш Gemini API key (Masked)

### Частина A: Standalone Job

| # | Крок | Дія | Очікуваний результат |
|---|------|-----|---------------------|
| 1 | Створити .gitlab-ci.yml | Додати конфігурацію нижче | Файл створено |
| 2 | Закомітити | Push до main | Pipeline налаштовано |
| 3 | Створити MR | Нова гілка + `test_code.py` + MR | MR створено |
| 4 | Перевірити pipeline | CI/CD → Pipelines | Job `ai-review` запустився |
| 5 | Перевірити результат | MR → Activity | AI залишив коментар |
| 6 | Перевірити threads | MR → Changes | Inline discussions на проблемних рядках |

**Standalone Job:**
```yaml
# .gitlab-ci.yml
ai-review:
  image: ghcr.io/konstziv/ai-code-reviewer:1
  script:
    - ai-review --provider gitlab --project $CI_PROJECT_PATH --mr-iid $CI_MERGE_REQUEST_IID
  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
    GITLAB_TOKEN: $GITLAB_TOKEN
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  allow_failure: true
```

### Частина B: Останній крок CI

| # | Крок | Дія | Очікуваний результат |
|---|------|-----|---------------------|
| 1 | Оновити CI | Додати stages та `needs` | Pipeline оновлено |
| 2 | Створити MR | MR з тестовим кодом | MR створено |
| 3 | Перевірити послідовність | CI/CD → Pipeline | AI Review після test |
| 4 | Перевірити залежність | Зробити test fail | AI Review пропускається |

**CI Pipeline:**
```yaml
# .gitlab-ci.yml
stages:
  - test
  - review

test:
  stage: test
  image: python:3.13-slim
  script:
    - echo "Running tests..."
    # - pytest tests/
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"

ai-review:
  stage: review
  image: ghcr.io/konstziv/ai-code-reviewer:1
  needs: [test]
  script:
    - ai-review --provider gitlab --project $CI_PROJECT_PATH --mr-iid $CI_MERGE_REQUEST_IID
  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
    GITLAB_TOKEN: $GITLAB_TOKEN
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  allow_failure: true
```

### Частина C: Тести конфігурації

| # | Тест | Конфігурація | Очікуваний результат |
|---|------|--------------|---------------------|
| C1 | Українська мова | `LANGUAGE: uk` | Review українською |
| C2 | Фіксована мова | `LANGUAGE: en`, `LANGUAGE_MODE: fixed` | Review англійською |
| C3 | Інша модель | `GEMINI_MODEL: gemini-1.5-pro` | Використовується Pro модель |
| C4 | Debug логи | `LOG_LEVEL: DEBUG` | Детальні логи в job output |

**Job з конфігурацією:**
```yaml
ai-review:
  stage: review
  image: ghcr.io/konstziv/ai-code-reviewer:1
  script:
    - ai-review --provider gitlab --project $CI_PROJECT_PATH --mr-iid $CI_MERGE_REQUEST_IID
  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
    GITLAB_TOKEN: $GITLAB_TOKEN
    LANGUAGE: uk
    LANGUAGE_MODE: adaptive
    GEMINI_MODEL: gemini-2.5-flash
    LOG_LEVEL: INFO
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  allow_failure: true
```

### Критерії успіху

- [ ] Pipeline запускається при створенні MR
- [ ] Job `ai-review` виконується успішно
- [ ] В MR Activity з'являється коментар з review
- [ ] В MR Changes є inline discussions
- [ ] Discussions можна resolve/reply
- [ ] Конфігурація `LANGUAGE` впливає на мову review
- [ ] `needs` працює — AI Review чекає на test job

### Можливі помилки

| Помилка | Причина | Рішення |
|---------|---------|---------|
| "401 Unauthorized" | Невірний токен | Перевірити GITLAB_TOKEN |
| "403 Forbidden" | Недостатні права токена | Токен потребує scope `api` та роль Maintainer |
| "404 Not Found" | Невірний project path | Перевірити CI_PROJECT_PATH |
| Немає коментарів | Job failed | Перевірити логи job |

---

## Сценарій 3: Локальний запуск — pip

**Мета:** Перевірити встановлення та запуск через pip/uv.

**Документація:** [docs/uk/installation.md](../docs/uk/installation.md)

### Передумови
- [ ] Python 3.13+
- [ ] pip або uv встановлено
- [ ] GitHub/GitLab токен
- [ ] Gemini API key
- [ ] Існуючий PR/MR для тестування

### Частина A: Встановлення та базовий запуск

| # | Крок | Дія | Очікуваний результат |
|---|------|-----|---------------------|
| 1 | Встановити | `pip install ai-reviewbot` | Встановлено без помилок |
| 2 | Перевірити версію | `ai-review --version` | `1.0.0a3` |
| 3 | Перевірити help | `ai-review --help` | Показує usage та всі опції |
| 4 | Експортувати змінні | `export GOOGLE_API_KEY=...` | Змінні встановлено |
| 5 | Запустити GitHub | `ai-review --repo owner/repo --pr-number 123` | Review опубліковано |
| 6 | Запустити GitLab | `ai-review --provider gitlab --project group/repo --mr-iid 456` | Review опубліковано |

**Команди встановлення:**
```bash
# pip
pip install ai-reviewbot

# uv
uv tool install ai-code-reviewer

# pipx
pipx install ai-code-reviewer
```

**Базовий запуск:**
```bash
# Змінні оточення
export GOOGLE_API_KEY="your_gemini_api_key"
export GITHUB_TOKEN="your_github_token"      # для GitHub
export GITLAB_TOKEN="your_gitlab_token"      # для GitLab

# Запуск для GitHub PR
ai-review --repo KonstZiv/ai-code-reviewer --pr-number 48

# Запуск для GitLab MR
ai-review --provider gitlab --project mygroup/myrepo --mr-iid 123
```

### Частина B: Тести конфігурації

| # | Тест | Команда | Очікуваний результат |
|---|------|---------|---------------------|
| B1 | Українська мова | `ai-review --repo owner/repo --pr 123 --language uk` | Review українською |
| B2 | Фіксована мова | `ai-review --repo owner/repo --pr 123 --language en --language-mode fixed` | Review англійською, ігноруючи контекст |
| B3 | Інша модель | `ai-review --repo owner/repo --pr 123 --model gemini-1.5-pro` | Використовується Pro модель |
| B4 | Debug логи | `LOG_LEVEL=DEBUG ai-review --repo owner/repo --pr 123` | Детальні логи в терміналі |

**Команди з конфігурацією:**
```bash
# Українська мова
ai-review --repo owner/repo --pr-number 123 --language uk

# Фіксована мова (ігнорує контекст PR)
ai-review --repo owner/repo --pr-number 123 --language uk --language-mode fixed

# Інша модель Gemini
ai-review --repo owner/repo --pr-number 123 --model gemini-1.5-pro

# Debug логи
LOG_LEVEL=DEBUG ai-review --repo owner/repo --pr-number 123

# Комбінація
ai-review --repo owner/repo --pr-number 123 \
  --language uk \
  --language-mode adaptive \
  --model gemini-2.5-flash
```

### Критерії успіху

- [ ] `pip install` завершується без помилок
- [ ] `ai-review --help` показує всі опції
- [ ] `ai-review --version` показує `1.0.0a3`
- [ ] Review публікується в PR/MR
- [ ] Логи показують процес (INFO рівень)
- [ ] `--language` впливає на мову review
- [ ] `--language-mode fixed` ігнорує контекст

---

## Сценарій 4: Локальний запуск — Docker

**Мета:** Перевірити запуск через Docker без встановлення Python.

**Документація:** [docs/uk/installation.md](../docs/uk/installation.md)

### Передумови
- [ ] Docker 20.10+
- [ ] GitHub/GitLab токен
- [ ] Gemini API key
- [ ] Існуючий PR/MR для тестування

### Частина A: Базовий запуск

| # | Крок | Дія | Очікуваний результат |
|---|------|-----|---------------------|
| 1 | Pull image | `docker pull ghcr.io/konstziv/ai-code-reviewer:1` | Image завантажено |
| 2 | Перевірити image | `docker images \| grep ai-code-reviewer` | Image присутній |
| 3 | Перевірити help | `docker run --rm ghcr.io/konstziv/ai-code-reviewer:1 --help` | Показує usage |
| 4 | Перевірити version | `docker run --rm ghcr.io/konstziv/ai-code-reviewer:1 --version` | `1.0.0a3` |
| 5 | Запустити GitHub | Команда з env vars (див. нижче) | Review опубліковано |
| 6 | Запустити GitLab | Команда з env vars (див. нижче) | Review опубліковано |

**Команди:**
```bash
# Pull image (GHCR)
docker pull ghcr.io/konstziv/ai-code-reviewer:1

# Або з DockerHub
docker pull koszivdocker/ai-reviewbot:1

# Перевірка
docker run --rm ghcr.io/konstziv/ai-code-reviewer:1 --help
docker run --rm ghcr.io/konstziv/ai-code-reviewer:1 --version

# Запуск для GitHub PR
docker run --rm \
  -e GOOGLE_API_KEY=your_api_key \
  -e GITHUB_TOKEN=your_token \
  ghcr.io/konstziv/ai-code-reviewer:1 \
  --repo owner/repo --pr-number 123

# Запуск для GitLab MR
docker run --rm \
  -e GOOGLE_API_KEY=your_api_key \
  -e GITLAB_TOKEN=your_token \
  ghcr.io/konstziv/ai-code-reviewer:1 \
  --provider gitlab --project group/repo --mr-iid 456
```

### Частина B: Тести конфігурації

| # | Тест | Env var | Очікуваний результат |
|---|------|---------|---------------------|
| B1 | Українська мова | `-e LANGUAGE=uk` | Review українською |
| B2 | Фіксована мова | `-e LANGUAGE=en -e LANGUAGE_MODE=fixed` | Review англійською |
| B3 | Інша модель | `-e GEMINI_MODEL=gemini-1.5-pro` | Використовується Pro модель |
| B4 | Debug логи | `-e LOG_LEVEL=DEBUG` | Детальні логи в терміналі |

**Команди з конфігурацією:**
```bash
# Українська мова
docker run --rm \
  -e GOOGLE_API_KEY=your_api_key \
  -e GITHUB_TOKEN=your_token \
  -e LANGUAGE=uk \
  ghcr.io/konstziv/ai-code-reviewer:1 \
  --repo owner/repo --pr-number 123

# Фіксована мова
docker run --rm \
  -e GOOGLE_API_KEY=your_api_key \
  -e GITHUB_TOKEN=your_token \
  -e LANGUAGE=en \
  -e LANGUAGE_MODE=fixed \
  ghcr.io/konstziv/ai-code-reviewer:1 \
  --repo owner/repo --pr-number 123

# Інша модель + Debug
docker run --rm \
  -e GOOGLE_API_KEY=your_api_key \
  -e GITHUB_TOKEN=your_token \
  -e GEMINI_MODEL=gemini-1.5-pro \
  -e LOG_LEVEL=DEBUG \
  ghcr.io/konstziv/ai-code-reviewer:1 \
  --repo owner/repo --pr-number 123
```

### Альтернативні registry

| Registry | Image |
|----------|-------|
| GHCR | `ghcr.io/konstziv/ai-code-reviewer:1` |
| DockerHub | `koszivdocker/ai-reviewbot:1` |
| Specific version | `ghcr.io/konstziv/ai-code-reviewer:1.0.0a3` |

### Критерії успіху

- [ ] Image pull успішний
- [ ] `--help` працює
- [ ] `--version` показує `1.0.0a3`
- [ ] Review публікується в PR/MR
- [ ] Environment variables передаються коректно
- [ ] `-e LANGUAGE=uk` впливає на мову review
- [ ] Обидва registry працюють (GHCR та DockerHub)

---

## Чеклист фінального тестування

### Функціональність

| Тест | Сценарій 1 | Сценарій 2 | Сценарій 3 | Сценарій 4 |
|------|------------|------------|------------|------------|
| Базовий запуск | ⬜ | ⬜ | ⬜ | ⬜ |
| Inline comments | ⬜ | ⬜ | ⬜ | ⬜ |
| Apply suggestion (GitHub) | ⬜ | — | ⬜ | ⬜ |
| Discussions (GitLab) | — | ⬜ | ⬜ | ⬜ |
| `needs` / dependencies | ⬜ | ⬜ | — | — |

### Конфігурація

| Тест | Сценарій 1 | Сценарій 2 | Сценарій 3 | Сценарій 4 |
|------|------------|------------|------------|------------|
| `LANGUAGE=uk` | ⬜ | ⬜ | ⬜ | ⬜ |
| `LANGUAGE_MODE=fixed` | ⬜ | ⬜ | ⬜ | ⬜ |
| `GEMINI_MODEL` | ⬜ | ⬜ | ⬜ | ⬜ |
| `LOG_LEVEL=DEBUG` | ⬜ | ⬜ | ⬜ | ⬜ |

### Якість Review

- [ ] Знаходить security issues (SQL injection, hardcoded creds)
- [ ] Знаходить code quality issues
- [ ] Пропонує конкретні виправлення
- [ ] Відзначає good practices
- [ ] Мова коментарів відповідає налаштуванням

---

## Звіт про тестування

**Заповнити після тестування:**

| Сценарій | Тестувальник | Дата | Результат | Issues |
|----------|--------------|------|-----------|--------|
| 1. GitHub Actions | | | | |
| 2. GitLab CI | | | | |
| 3. pip install | | | | |
| 4. Docker | | | | |

**Загальний результат:** ⏳ Pending

---

## Історія версій документа

| Версія | Дата | Автор | Зміни |
|--------|------|-------|-------|
| 1.0 | 2026-01-30 | Claude | Initial version |
| 1.1 | 2026-01-30 | Claude | Merged configuration tests into scenarios 1-4 |
