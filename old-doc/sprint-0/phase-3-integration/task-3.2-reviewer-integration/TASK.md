# Task 3.2: Reviewer Integration

| Поле | Значення |
|------|----------|
| **Фаза** | 3 — Integration |
| **Оцінка** | 2-3 години |
| **Залежності** | 3.1 |
| **Блокує** | 3.3 |
| **Файли** | `reviewer.py`, `core/config.py`, `cli.py` |

## Що робимо

Додаємо Discovery step в `review_pull_request()`.
Нові settings: `discovery_enabled`.
Fail-open: якщо Discovery fails → review continues.

## Очікуваний результат

- Discovery запускається перед рев'ю
- `ProjectProfile` передається в `ReviewContext`
- Можна вимкнути через `AI_REVIEWER_DISCOVERY_ENABLED=false`
