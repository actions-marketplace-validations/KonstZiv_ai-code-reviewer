# Встановлення

Варіант встановлення залежить від моделі використання та мети.

---

## 1. CI/CD — автоматичний review {#ci-cd}

Найпоширеніший сценарій: AI Code Reviewer запускається автоматично при створенні або оновленні PR/MR.

Налаштуйте за 5 хвилин:

- :octicons-mark-github-16: **[Налаштування ревʼю для GitHub →](quick-start.md)**

    :point_right: [Приклади workflows →](examples/github-minimal.md) · [Детальний GitHub Guide →](github.md)

- :simple-gitlab: **[Налаштування ревʼю для GitLab →](quick-start.md)**

    :point_right: [Приклади workflows →](examples/gitlab-minimal.md) · [Детальний GitLab Guide →](gitlab.md)

Для тонкого налаштування див. [Конфігурація →](configuration.md)

---

## 2. Автономне розгортання: CLI/Docker {#standalone}

CLI та Docker image дозволяють запускати AI Code Reviewer поза стандартним CI pipeline.

### Сценарії використання

| Сценарій | Як реалізувати |
|----------|----------------|
| **Ручний запуск** | Локальний термінал — debugging, демо, оцінка |
| **Scheduled review** | GitLab Scheduled Pipeline / GitHub Actions `schedule` / cron |
| **Batch review** | Скрипт що ітерує по відкритих PR/MR |
| **Власний сервер** | Docker на сервері з доступом до Git API |
| **On-demand review** | Webhook → запуск контейнера |

### Обов'язкові змінні оточення

| Змінна | Опис | Коли потрібна | Як отримати |
|--------|------|---------------|-------------|
| `AI_REVIEWER_GOOGLE_API_KEY` | API ключ Gemini | **Завжди** | [Google AI Studio](https://aistudio.google.com/) |
| `AI_REVIEWER_GITHUB_TOKEN` | GitHub Personal Access Token | Для GitHub | [Інструкція](github.md#get-token) |
| `AI_REVIEWER_GITLAB_TOKEN` | GitLab Personal Access Token | Для GitLab | [Інструкція](gitlab.md#get-token) |

!!! tip "Fallback"
    Старі назви без префіксу (наприклад, `GOOGLE_API_KEY`) все ще працюють як fallback.

---

### Ручний запуск

Для debugging, демо, оцінки перед впровадженням, ретроспективного аналізу PR/MR.

#### Docker (рекомендовано)

Не потребує встановлення Python — все в контейнері.

**Крок 1: Завантажте image**

```bash
docker pull ghcr.io/konstziv/ai-code-reviewer:1
```

**Крок 2: Запустіть review**

=== "GitHub PR"

    ```bash
    docker run --rm \
      -e AI_REVIEWER_GOOGLE_API_KEY=your_api_key \
      -e AI_REVIEWER_GITHUB_TOKEN=your_token \
      ghcr.io/konstziv/ai-code-reviewer:1 \
      --repo owner/repo --pr 123
    ```

=== "GitLab MR"

    ```bash
    docker run --rm \
      -e AI_REVIEWER_GOOGLE_API_KEY=your_api_key \
      -e AI_REVIEWER_GITLAB_TOKEN=your_token \
      ghcr.io/konstziv/ai-code-reviewer:1 \
      --provider gitlab --repo owner/repo --pr 123
    ```

!!! tip "Docker images"
    Доступні з двох реєстрів:

    - `ghcr.io/konstziv/ai-code-reviewer:1` — GitHub Container Registry
    - `koszivdocker/ai-reviewbot:1` — DockerHub

#### pip / uv

Встановлення як Python пакету.

**Крок 1: Встановіть**

=== "pip"

    ```bash
    pip install ai-reviewbot
    ```

=== "uv"

    ```bash
    uv tool install ai-reviewbot
    ```

=== "pipx"

    ```bash
    pipx install ai-reviewbot
    ```

!!! note "Python версія"
    Потрібен Python **3.13+**

**Крок 2: Налаштуйте змінні**

```bash
export AI_REVIEWER_GOOGLE_API_KEY=your_api_key
export AI_REVIEWER_GITHUB_TOKEN=your_token  # або AI_REVIEWER_GITLAB_TOKEN для GitLab
```

**Крок 3: Запустіть**

=== "GitHub PR"

    ```bash
    ai-review --repo owner/repo --pr 123
    ```

=== "GitLab MR"

    ```bash
    ai-review --provider gitlab --repo owner/repo --pr 123
    ```

---

### Опціональні змінні

Для тонкого налаштування доступні додаткові змінні:

| Змінна | Default | Вплив |
|--------|---------|-------|
| `AI_REVIEWER_LANGUAGE` | `en` | Мова відповідей (ISO 639) |
| `AI_REVIEWER_LANGUAGE_MODE` | `adaptive` | Режим визначення мови |
| `AI_REVIEWER_GEMINI_MODEL` | `gemini-2.5-flash` | Модель Gemini |
| `AI_REVIEWER_LOG_LEVEL` | `INFO` | Рівень логування |

:point_right: [Повний список змінних →](configuration.md#optional)

---

### Scheduled reviews

Запуск ревʼю за розкладом — для економії ресурсів або коли не потрібен миттєвий фідбек.

=== "GitLab Scheduled Pipeline"

    ```yaml
    # .gitlab-ci.yml
    ai-review-scheduled:
      image: ghcr.io/konstziv/ai-code-reviewer:1
      script:
        - |
          # Отримати список відкритих MR
          MR_LIST=$(curl -s --header "PRIVATE-TOKEN: $AI_REVIEWER_GITLAB_TOKEN" \
            "$CI_SERVER_URL/api/v4/projects/$CI_PROJECT_ID/merge_requests?state=opened" \
            | jq -r '.[].iid')

          # Запустити ревʼю для кожного MR
          for MR_IID in $MR_LIST; do
            echo "Reviewing MR !$MR_IID"
            ai-review --provider gitlab --repo $CI_PROJECT_PATH --pr $MR_IID || true
          done
      rules:
        - if: $CI_PIPELINE_SOURCE == "schedule"
    ```

    **Налаштування розкладу:** Project → Build → Pipeline schedules → New schedule

=== "GitHub Actions Schedule"

    ```yaml
    # .github/workflows/scheduled-review.yml
    name: Scheduled AI Review

    on:
      schedule:
        - cron: '0 9 * * *'  # Щодня о 9:00 UTC

    jobs:
      review-open-prs:
        runs-on: ubuntu-latest
        steps:
          - name: Get open PRs and review
            env:
              AI_REVIEWER_GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
              AI_REVIEWER_GOOGLE_API_KEY: ${{ secrets.AI_REVIEWER_GOOGLE_API_KEY }}
            run: |
              # Отримати список відкритих PR
              PRS=$(gh pr list --repo ${{ github.repository }} --state open --json number -q '.[].number')

              for PR in $PRS; do
                echo "Reviewing PR #$PR"
                docker run --rm \
                  -e AI_REVIEWER_GOOGLE_API_KEY -e AI_REVIEWER_GITHUB_TOKEN \
                  ghcr.io/konstziv/ai-code-reviewer:1 \
                  --repo ${{ github.repository }} --pr $PR || true
              done
    ```

---

### Власний сервер / приватне середовище

Для розгортання на власній інфраструктурі з доступом до Git API.

**Варіанти:**

- **Docker на сервері** — запуск через cron, systemd timer, або як сервіс
- **Kubernetes** — CronJob для scheduled reviews
- **Self-hosted GitLab** — додайте змінну `GITLAB_URL` (див. приклад нижче)

**Приклад cron job:**

```bash
# /etc/cron.d/ai-review
# Щодня о 10:00 запускати ревʼю для всіх відкритих MR
0 10 * * * reviewer /usr/local/bin/review-all-mrs.sh
```

```bash
#!/bin/bash
# /usr/local/bin/review-all-mrs.sh
export AI_REVIEWER_GOOGLE_API_KEY="your_key"
export AI_REVIEWER_GITLAB_TOKEN="your_token"

MR_LIST=$(curl -s --header "PRIVATE-TOKEN: $AI_REVIEWER_GITLAB_TOKEN" \
  "https://gitlab.company.com/api/v4/projects/123/merge_requests?state=opened" \
  | jq -r '.[].iid')

for MR_IID in $MR_LIST; do
  docker run --rm \
    -e AI_REVIEWER_GOOGLE_API_KEY -e AI_REVIEWER_GITLAB_TOKEN \
    ghcr.io/konstziv/ai-code-reviewer:1 \
    --provider gitlab --repo group/repo --pr $MR_IID
done
```

!!! tip "Self-hosted GitLab"
    Для self-hosted GitLab додайте змінну `AI_REVIEWER_GITLAB_URL`:

    ```bash
    -e AI_REVIEWER_GITLAB_URL=https://gitlab.company.com
    ```

---

## 3. Контриб'ютори / розробка {#development}

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
