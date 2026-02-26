# Task 3.1: Prompt Integration

| Поле | Значення |
|------|----------|
| **Фаза** | 3 — Integration |
| **Оцінка** | 2-3 години |
| **Залежності** | Фаза 2 |
| **Блокує** | 3.2 |
| **Файли** | `core/models.py`, `integrations/prompts.py` |

## Що робимо

Додаємо `project_profile` в `ReviewContext` і секцію "Project Context" в review prompt.

## Очікуваний результат

- `ReviewContext` має `project_profile: ProjectProfile | None`
- `build_review_prompt()` включає `profile.to_prompt_context()` якщо є
- `SYSTEM_PROMPT` оновлений: "respect automated checks"
