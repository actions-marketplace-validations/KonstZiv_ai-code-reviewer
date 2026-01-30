# Швидкий старт

Запустіть AI Code Reviewer за 1 хвилину.

---

## GitHub Actions

### Крок 1: Додайте секрет

`Settings → Secrets and variables → Actions → New repository secret`

| Назва | Значення |
|-------|----------|
| `GOOGLE_API_KEY` | Ваш Gemini API ключ |

:point_right: [Отримати ключ](https://aistudio.google.com/)

### Крок 2: Створіть workflow

в корні Вашого проекту створіть файл `.github/workflows/ai-review.yml`

`.github/workflows/ai-review.yml`:

```yaml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

concurrency:
  group: ai-review-${{ github.event.pull_request.number }}
  cancel-in-progress: true

jobs:
  review:
    runs-on: ubuntu-latest
    # Не запускати для fork PRs (немає доступу до secrets)
    if: github.event.pull_request.head.repo.full_name == github.repository
    permissions:
      contents: read
      pull-requests: write

    steps:
      - uses: KonstZiv/ai-code-reviewer@v1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          google_api_key: ${{ secrets.GOOGLE_API_KEY }}
```

### Крок 3: Створіть PR

Готово! AI review з'явиться автоматично.

---

## GitLab CI

### Крок 1: Додайте змінну

`Settings → CI/CD → Variables`

| Назва | Значення | Опції |
|-------|----------|-------|
| `GOOGLE_API_KEY` | Ваш Gemini API ключ | Masked, Protected |


:point_right: [Отримати ключ](https://aistudio.google.com/)


### Крок 2: Додайте job

в корні Вашого проєкту створіть файл `.gitlab-ci.yml`

`.gitlab-ci.yml`:

```yaml
ai-review:
  image: ghcr.io/konstziv/ai-code-reviewer:1
  stage: test
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  allow_failure: true
  variables:
    GITLAB_TOKEN: $CI_JOB_TOKEN
    GOOGLE_API_KEY: $GOOGLE_API_KEY
```

!!! note "Для inline коментарів"
    `CI_JOB_TOKEN` має обмеження. Для повного функціоналу використовуйте [Personal Access Token](gitlab.md#personal-access-token).

### Крок 3: Створіть MR

Готово! AI review з'явиться як коментарі до MR.

---

## Локальний запуск

Для тестування локально вам потрібні:

- **GOOGLE_API_KEY** — [отримати в Google AI Studio](https://aistudio.google.com/)
- **GITHUB_TOKEN** або **GITLAB_TOKEN** — залежно від платформи:
    - GitHub: [як отримати PAT](github.md#get-token)
    - GitLab: [як отримати PAT](gitlab.md#get-token)

=== "GitHub"

    ```bash
    # Встановити
    pip install ai-reviewbot

    # Налаштувати
    export GOOGLE_API_KEY=your_key
    export GITHUB_TOKEN=your_github_pat

    # Запустити для GitHub PR
    ai-review --repo owner/repo --pr-number 123
    ```

=== "GitLab"

    ```bash
    # Встановити
    pip install ai-reviewbot

    # Налаштувати
    export GOOGLE_API_KEY=your_key
    export GITLAB_TOKEN=your_gitlab_pat

    # Запустити для GitLab MR
    ai-review --provider gitlab --project owner/repo --mr-iid 123
    ```

---

## Що далі?

| Задача | Документ |
|--------|----------|
| Налаштувати мову | [Конфігурація](configuration.md) |
| Оптимізувати для GitHub | [GitHub Guide](github.md) |
| Оптимізувати для GitLab | [GitLab Guide](gitlab.md) |
| Подивитися приклади | [Приклади](examples/index.md) |

---

## Приклад результату

Після запуску ви побачите inline comments:

![AI Review Example](https://via.placeholder.com/800x400?text=AI+Review+Inline+Comment)

Кожен коментар містить:

- :red_circle: / :yellow_circle: / :blue_circle: Severity badge
- Опис проблеми
- Кнопку **"Apply suggestion"**
- Collapsible пояснення "Чому це важливо?"

---

## Troubleshooting

### Review не з'являється?

1. Перевірте логи CI job
2. Перевірте що `GOOGLE_API_KEY` коректний
3. Для GitHub: перевірте `permissions: pull-requests: write`
4. Для fork PRs: секрети недоступні

### Rate limit?

Gemini free tier: 15 RPM. Зачекайте хвилину.

:point_right: [Всі проблеми →](troubleshooting.md)
