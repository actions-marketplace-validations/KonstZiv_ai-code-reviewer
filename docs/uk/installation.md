# Встановлення

Варіант встановлення залежить від моделі використання та мети.

---

## 1. CI/CD — автоматичний review {#ci-cd}

Найпоширеніший сценарій: AI Code Reviewer запускається автоматично при створенні або оновленні PR/MR.

### GitHub Actions

Найпростіший спосіб для GitHub — використання готового GitHub Action:

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
      - uses: KonstZiv/ai-code-reviewer@v1
        with:
          google_api_key: ${{ secrets.GOOGLE_API_KEY }}
```

**Необхідні налаштування:**

| Що потрібно | Де налаштувати |
|-------------|----------------|
| `GOOGLE_API_KEY` | Repository → Settings → Secrets → Actions |

:point_right: [Повний приклад з concurrency та фільтрацією →](quick-start.md#github-actions)

:point_right: [Детальний GitHub Guide →](github.md)

---

### GitLab CI

Для GitLab використовуйте Docker image в `.gitlab-ci.yml`:

```yaml
# .gitlab-ci.yml
ai-review:
  image: ghcr.io/konstziv/ai-code-reviewer:1
  stage: test
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  allow_failure: true
  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
```

**Необхідні налаштування:**

| Що потрібно | Де налаштувати |
|-------------|----------------|
| `GOOGLE_API_KEY` | Project → Settings → CI/CD → Variables (Masked) |
| `GITLAB_TOKEN` | Опціонально, для inline comments ([детальніше](gitlab.md#tokens)) |

:point_right: [Повний приклад →](quick-start.md#gitlab-ci)

:point_right: [Детальний GitLab Guide →](gitlab.md)

---

## 2. Локальне тестування / оцінка {#local}

### Навіщо це потрібно?

1. **Оцінка перед впровадженням** — спробувати на реальному PR перш ніж додавати в CI
2. **Debugging** — якщо в CI щось не працює, запустити локально з `--log-level DEBUG`
3. **Ретроспективний review** — проаналізувати старий PR/MR
4. **Демо** — показати команді/менеджменту як це працює

### Як це працює

```
Локальний термінал
       │
       ▼
   ai-review CLI
       │
       ├──► GitHub/GitLab API (читає PR/MR, diff, linked issues)
       │
       ├──► Gemini API (отримує review)
       │
       └──► GitHub/GitLab API (публікує коментарі)
```

### Обов'язкові змінні оточення

| Змінна | Опис | Коли потрібна | Як отримати |
|--------|------|---------------|-------------|
| `GOOGLE_API_KEY` | API ключ Gemini | **Завжди** | [Google AI Studio](https://aistudio.google.com/) |
| `GITHUB_TOKEN` | GitHub Personal Access Token | Для GitHub | [Інструкція](github.md#get-token) |
| `GITLAB_TOKEN` | GitLab Personal Access Token | Для GitLab | [Інструкція](gitlab.md#get-token) |

---

### Варіант A: Docker (рекомендовано)

Не потребує встановлення Python — все в контейнері.

**Крок 1: Завантажте image**

```bash
docker pull ghcr.io/konstziv/ai-code-reviewer:1
```

**Крок 2: Запустіть review**

=== "GitHub PR"

    ```bash
    docker run --rm \
      -e GOOGLE_API_KEY=your_api_key \
      -e GITHUB_TOKEN=your_token \
      ghcr.io/konstziv/ai-code-reviewer:1 \
      --repo owner/repo --pr-number 123
    ```

=== "GitLab MR"

    ```bash
    docker run --rm \
      -e GOOGLE_API_KEY=your_api_key \
      -e GITLAB_TOKEN=your_token \
      ghcr.io/konstziv/ai-code-reviewer:1 \
      --provider gitlab --project owner/repo --mr-iid 123
    ```

!!! tip "Docker images"
    Доступні з двох реєстрів:

    - `ghcr.io/konstziv/ai-code-reviewer:1` — GitHub Container Registry
    - `koszivdocker/ai-reviewbot:1` — DockerHub

---

### Варіант B: pip / uv

Встановлення як Python пакету.

**Крок 1: Встановіть**

=== "pip"

    ```bash
    pip install ai-reviewbot
    ```

=== "uv"

    ```bash
    uv tool install ai-code-reviewer
    ```

=== "pipx"

    ```bash
    pipx install ai-code-reviewer
    ```

!!! note "Python версія"
    Потрібен Python **3.13+**

**Крок 2: Налаштуйте змінні**

```bash
export GOOGLE_API_KEY=your_api_key
export GITHUB_TOKEN=your_token  # або GITLAB_TOKEN для GitLab
```

**Крок 3: Запустіть**

=== "GitHub PR"

    ```bash
    ai-review --repo owner/repo --pr-number 123
    ```

=== "GitLab MR"

    ```bash
    ai-review --provider gitlab --project owner/repo --mr-iid 123
    ```

---

### Опціональні змінні

Для тонкого налаштування доступні додаткові змінні:

| Змінна | Default | Вплив |
|--------|---------|-------|
| `LANGUAGE` | `en` | Мова відповідей (ISO 639) |
| `LANGUAGE_MODE` | `adaptive` | Режим визначення мови |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Модель Gemini |
| `LOG_LEVEL` | `INFO` | Рівень логування |

:point_right: [Повний список змінних →](configuration.md#optional)

---

## 3. Корпоративне середовище (air-gapped) {#airgapped}

Для середовищ з обмеженим доступом до інтернету.

### Обмеження

!!! warning "Потрібен доступ до Gemini API"
    AI Code Reviewer використовує Google Gemini API для аналізу коду.

    **Потрібен доступ до:** `generativelanguage.googleapis.com`

    Наразі підтримка локально розгорнутих LLM моделей **не реалізована**.

### Розгортання Docker image

**Крок 1: На машині з доступом до інтернету**

```bash
# Завантажити image
docker pull ghcr.io/konstziv/ai-code-reviewer:1

# Зберегти в файл
docker save ghcr.io/konstziv/ai-code-reviewer:1 > ai-code-reviewer.tar
```

**Крок 2: Перенести файл у закрите середовище**

**Крок 3: Завантажити в internal registry**

```bash
# Завантажити з файлу
docker load < ai-code-reviewer.tar

# Перетегувати для internal registry
docker tag ghcr.io/konstziv/ai-code-reviewer:1 \
    registry.internal.company.com/devops/ai-code-reviewer:1

# Опублікувати
docker push registry.internal.company.com/devops/ai-code-reviewer:1
```

**Крок 4: Використати в GitLab CI**

```yaml
ai-review:
  image: registry.internal.company.com/devops/ai-code-reviewer:1
  script:
    - ai-review
  variables:
    GITLAB_URL: https://gitlab.internal.company.com
    GOOGLE_API_KEY: $GOOGLE_API_KEY
```

---

## 4. Контриб'ютори / розробка {#development}

Якщо ви маєте час і натхнення допомогти в розвитку пакета, або бажаєте використати його як основу для власних розробок — ми щиро вітаємо і заохочуємо до таких дій!

### Встановлення для розробки

```bash
# Клонувати репозиторій
git clone https://github.com/KonstZiv/ai-code-reviewer.git
cd ai-code-reviewer

# Встановити залежності (використовуємо uv)
uv sync

# Перевірити
uv run ai-review --help

# Запустити тести
uv run pytest

# Запустити перевірки якості
uv run ruff check .
uv run mypy .
```

!!! info "uv"
    Ми використовуємо [uv](https://github.com/astral-sh/uv) для керування залежностями.

    Встановити: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Структура проєкту

```
ai-code-reviewer/
├── src/ai_reviewer/      # Вихідний код
│   ├── core/             # Моделі, конфіг, форматування
│   ├── integrations/     # GitHub, GitLab, Gemini
│   └── utils/            # Утиліти
├── tests/                # Тести
├── docs/                 # Документація
└── examples/             # Приклади CI конфігурацій
```

:point_right: [Як зробити внесок →](https://github.com/KonstZiv/ai-code-reviewer/blob/main/CONTRIBUTING.md)

---

## Вимоги {#requirements}

### Системні вимоги

| Компонент | Вимога |
|-----------|--------|
| Python | 3.13+ (для pip install) |
| Docker | 20.10+ (для Docker) |
| OS | Linux, macOS, Windows |
| RAM | 256MB+ |
| Мережа | Доступ до `generativelanguage.googleapis.com` |

### API ключі

| Ключ | Обов'язковий | Як отримати |
|------|--------------|-------------|
| Google Gemini API | **Так** | [Google AI Studio](https://aistudio.google.com/) |
| GitHub PAT | Для GitHub | [Інструкція](github.md#get-token) |
| GitLab PAT | Для GitLab | [Інструкція](gitlab.md#get-token) |

### Ліміти Gemini API

!!! info "Free tier"
    Google Gemini має безкоштовний tier:

    | Ліміт | Значення |
    |-------|----------|
    | Requests per minute | 15 RPM |
    | Tokens per day | 1M |
    | Requests per day | 1500 |

    Для більшості проєктів цього достатньо.

---

## Наступний крок

:point_right: [Швидкий старт →](quick-start.md)
