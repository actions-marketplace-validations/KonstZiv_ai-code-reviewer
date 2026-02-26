# Epic: User Experience

## 🔙 Контекст

Discovery працює, але користувач не може:
1. Побачити що бот дізнався про проєкт (silent mode при відсутності gaps)
2. Протестувати Discovery без створення MR
3. Дізнатись що Discovery взагалі запускався (якщо все добре — нічого не поститься)

## 🎯 Мета

Користувач має **контроль** і **visibility** над Discovery:
- `ai-review discover owner/repo` — подивитись що бот знає
- `discovery_verbose=true` — завжди бачити discovery comment
- Документація синхронізована з кодом

## Tasks

| Task | Опис | Estimate |
|------|------|----------|
| 4.1 Discover CLI | `ai-review discover` standalone command | 1-1.5h |
| 4.2 Verbose Mode | Env var для always-post discovery comment | 30min |
| 4.3 Review Gate + Docs | Фінальна перевірка і sync документації | 30min-1h |

## Вплив на користувача

**Discover CLI** — найбільший wow-фактор:
```bash
$ ai-review discover owner/repo
🔍 Discovering project context...

📋 Project Profile:
  Language: Python (Django) 3.13
  Package manager: uv
  Layout: src

🔧 CI Tools (4):
  ✅ ruff (linting)
  ✅ ruff (formatting)
  ✅ mypy (type_checking)
  ✅ pytest (testing)

📝 Review Guidance:
  Skip: Code style, formatting, basic type errors (CI handles these)
  Focus: Security vulnerabilities, business logic

💡 Create .reviewbot.md to customize.
```

## Review Gate

Після Phase 4 (фінальний):
- [ ] `ai-review discover` працює з mock або real repo
- [ ] `discovery_verbose=true` → comment поститься
- [ ] Docs відповідають коду
- [ ] README links працюють
- [ ] `make check` passes
- [ ] Sprint DONE
