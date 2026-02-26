# Task 1.3: ConversationProvider ABC + GitHub/GitLab

| Поле | Значення |
|------|----------|
| **Фаза** | 1 — Abstractions |
| **Оцінка** | 5-7 годин |
| **Залежності** | Немає |
| **Блокує** | 2.6, 3.3 |
| **Файли** | `integrations/conversation.py`, `github.py`, `gitlab.py` |

---

## Що робимо

Створюємо ABC для двосторонньої комунікації: бот ставить структуровані питання,
читає відповіді, відповідає в threads. Це фундамент діалогу для всього Beta.

## Навіщо

- Discovery ставить питання → "Не бачу CI, як перевіряєте код?"
- Наступний запуск читає відповіді → оновлює ProfileProfile
- Beta-2: бот бере участь у review threads
- Beta-3: повноцінний інтерактивний режим

## Очікуваний результат

- `ConversationProvider` ABC з 4 методами
- `BotQuestion`, `BotThread`, `ThreadStatus` models
- Реалізації для GitHub і GitLab
- Формат питань з `question_id` і `default_assumption`
- Розпізнавання відповідей на попередні питання

## Як перевірити

```bash
make check
pytest tests/unit/test_conversation_provider.py
```

## Особливості

Це найскладніша задача Фази 1. Ключові складності:

- GitHub і GitLab мають різну модель threading
- Потрібно розпізнавати відповіді на конкретні питання (pattern matching)
- `get_linked_tasks_deep()` — розширення існуючого `get_linked_task()`
- Формат питань має бути human-readable і machine-parseable одночасно
