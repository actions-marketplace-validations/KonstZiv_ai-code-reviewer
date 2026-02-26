# Фаза 3: Integration

## Навігація

```
phase-3-integration/
├── EPIC.md                            ← ви тут
├── task-3.1-prompt-integration/       ProjectProfile → review prompt
├── task-3.2-reviewer-integration/     Discovery step в reviewer.py
└── task-3.3-discovery-comment/        Формат коментаря в MR
```

**Батьківський документ:** [../SPRINT.md](../SPRINT.md)

---

## 🔙 Контекст

### Що маємо після Фази 2

- Всі Discovery компоненти працюють ізольовано
- `DiscoveryOrchestrator.discover()` повертає `ProjectProfile`
- `ProjectProfile.to_prompt_context()` генерує compact text
- CI Analyzer, Config Collector, .reviewbot.md — протестовані

### Що залишилось

З'єднати Discovery з існуючим review flow: prompt, reviewer, comment.

---

## 🎯 Мета фази

Discovery підключається до review pipeline. Бот починає використовувати
знання про проєкт при рев'ю.

---

## Задачі

| # | Задача | Оцінка | Залежності |
|---|--------|--------|------------|
| 3.1 | Prompt Integration | 2-3 год | Фаза 2 |
| 3.2 | Reviewer Integration | 2-3 год | 3.1 |
| 3.3 | Discovery Comment | 1-2 год | 3.2 |

---

## ⚠️ Ревізія після завершення

Перед Фазою 4 перевірити:

1. Реальний output discovery comment — чи виглядає добре?
2. Review prompt з ProjectProfile — чи LLM реагує на guidance?
3. Чи потрібні додаткові edge case тести (Фаза 4)?

---

## 🔭 Далі

- Beta-1: framework-specific hints в to_prompt_context()
- Beta-2: Scout agent отримує ProjectProfile для пріоритизації
