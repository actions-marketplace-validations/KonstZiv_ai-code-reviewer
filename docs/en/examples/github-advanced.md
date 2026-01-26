# GitHub: Розширений приклад

Production-ready конфігурація з усіма best practices.

---

## Крок 1: Додайте секрет

`Settings → Secrets and variables → Actions → New repository secret`

| Назва | Значення |
|-------|----------|
| `GOOGLE_API_KEY` | Ваш Gemini API ключ |

---

## Крок 2: Створіть файл

`.github/workflows/ai-review.yml`:

```yaml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]
    # Опціонально: фільтр по файлах
    # paths:
    #   - '**.py'
    #   - '**.js'
    #   - '**.ts'

# Скасувати попередній run при новому коміті
concurrency:
  group: ai-review-${{ github.event.pull_request.number }}
  cancel-in-progress: true

jobs:
  review:
    name: AI Review
    runs-on: ubuntu-latest

    # Не запускати для fork PRs (секрети недоступні)
    if: github.event.pull_request.head.repo.full_name == github.repository

    # Не блокувати PR якщо review failed
    continue-on-error: true

    # Timeout захист
    timeout-minutes: 10

    permissions:
      contents: read
      pull-requests: write

    steps:
      - name: Run AI Code Review
        uses: KonstZiv/ai-code-reviewer@v1
        with:
          google_api_key: ${{ secrets.GOOGLE_API_KEY }}
          language: uk
          language_mode: adaptive
          log_level: INFO
```

---

## Що включено

| Функція | Статус | Опис |
|---------|--------|------|
| Inline comments | :white_check_mark: | З Apply Suggestion |
| Concurrency | :white_check_mark: | Скасовує старі runs |
| Fork filter | :white_check_mark: | Пропускає fork PRs |
| Timeout | :white_check_mark: | 10 хвилин максимум |
| Non-blocking | :white_check_mark: | PR не блокується |
| Українська мова | :white_check_mark: | `language: uk` |

---

## Варіації

### З фільтром по файлах

```yaml
on:
  pull_request:
    paths:
      - 'src/**'
      - '**.py'
    paths-ignore:
      - '**.md'
      - 'docs/**'
```

### З фільтром по гілках

```yaml
on:
  pull_request:
    branches:
      - main
      - develop
```

### З кастомною моделлю

```yaml
- uses: KonstZiv/ai-code-reviewer@v1
  with:
    google_api_key: ${{ secrets.GOOGLE_API_KEY }}
    gemini_model: gemini-1.5-pro  # Потужніша модель
```

### З DEBUG логами

```yaml
- uses: KonstZiv/ai-code-reviewer@v1
  with:
    google_api_key: ${{ secrets.GOOGLE_API_KEY }}
    log_level: DEBUG
```

---

## Опції action

| Input | Опис | Default |
|-------|------|---------|
| `google_api_key` | Gemini API ключ | **required** |
| `github_token` | GitHub токен | `${{ github.token }}` |
| `language` | Мова відповідей | `en` |
| `language_mode` | `adaptive` / `fixed` | `adaptive` |
| `gemini_model` | Модель Gemini | `gemini-2.0-flash` |
| `log_level` | Рівень логів | `INFO` |

---

## Troubleshooting

### Review не з'являється

1. Перевірте логи workflow
2. Перевірте що це не fork PR
3. Перевірте `permissions: pull-requests: write`

### Rate limit

Concurrency автоматично скасовує старі runs, що зменшує навантаження.

---

## Наступний крок

:point_right: [GitLab приклади →](gitlab-minimal.md)
