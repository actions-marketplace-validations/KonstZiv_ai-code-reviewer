# Task 4.2: Edge Cases

| Поле | Значення |
|------|----------|
| **Фаза** | 4 — Polish |
| **Оцінка** | 2-3 години |

## Що робимо

Граничні випадки: великі repos, monorepos, API failures, second run.

## Сценарії

- Monorepo з 3+ мовами
- File tree >5000 файлів → truncation
- CI з custom GitHub Actions (не прямі run:)
- Repository API rate limit → graceful degradation
- Second run: бот бачить відповіді на попередні питання
- .reviewbot.md з неповним/зламаним форматом
