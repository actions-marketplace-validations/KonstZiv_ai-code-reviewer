# Epic: Housekeeping & Safety

## 🔙 Контекст

Codebase Audit (Beta-0) виявив: мертві dependencies, misleading config files, security concern з raw_yaml. Ці проблеми не блокують функціональність, але:
- Збільшують Docker image
- Вводять в оману користувачів
- Створюють потенційний security risk

## 🎯 Мета

Чистий, безпечний, не misleading codebase готовий до публікації.

## Tasks

| Task | Опис | Estimate |
|------|------|----------|
| 2.1 Dead Deps | Видалити `all-providers`, порожній `agents/` | 20min |
| 2.2 Env Cleanup | Почистити `.env.example` + відповідність action.yml | 15min |
| 2.3 ROADMAP Fix | Повернути ROADMAP.md в root або оновити README links | 20min |
| 2.4 raw_yaml Sanitize | Прибрати `raw_yaml` з `CIInsights` або strip secrets | 30min |

## Вплив на користувача

- **Docker image** менший (без langchain/anthropic/openai optional deps)
- **`.env.example`** показує тільки працюючі settings — менше confusion
- **README** → ROADMAP link працює
- **Логи** не містять CI secrets

## Review Gate

Після Phase 2:
- [ ] `pip install ai-code-reviewer[all-providers]` → помилка (group видалений)
- [ ] `docker build` працює
- [ ] `.env.example` тільки Google + GitHub/GitLab keys
- [ ] `raw_yaml` не зберігається в CIInsights
- [ ] `make check` passes
