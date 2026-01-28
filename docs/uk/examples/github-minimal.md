# GitHub: Мінімальний приклад

Найпростіша конфігурація для GitHub Actions.

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
    types: [opened, synchronize]

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

---

## Крок 3: Створіть PR

Готово! AI review з'явиться автоматично.

---

## Що включено

| Функція | Статус |
|---------|--------|
| Inline comments | :white_check_mark: |
| Apply Suggestion кнопка | :white_check_mark: |
| Мовна адаптивність | :white_check_mark: (adaptive) |
| Метрики | :white_check_mark: |

---

## Обмеження

| Обмеження | Рішення |
|-----------|---------|
| Fork PRs не працюють | Очікувана поведінка |
| Немає concurrency | Див. [розширений приклад](github-advanced.md) |
| Мова англійська за замовчуванням | Додайте `language: uk` |

---

## Наступний крок

:point_right: [Розширений приклад →](github-advanced.md)
