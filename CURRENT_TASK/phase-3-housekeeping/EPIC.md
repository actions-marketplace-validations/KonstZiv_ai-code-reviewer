# Epic: Housekeeping & Safety

## 🔙 Контекст

Codebase Audit (Beta-0) виявив: мертві dependencies, misleading config, security concern.
Ці проблеми не блокують функціональність, але заважають публікації.

## 🎯 Мета

Чистий, безпечний, не misleading codebase. Одна задача, чотири дрібні зміни.

## Task 3.1: Cleanup Bundle

### A) Dead Dependencies (20 min)

**Проблема:** `all-providers` optional deps включає langchain, anthropic, openai (+50MB).
Також порожній `agents/` package.

**Що робити:**
- Видалити `[project.optional-dependencies]` → `all-providers` group
- Видалити порожній `agents/` package
- Перевірити що `github` і `gitlab` optional groups залишились
- `pip install ai-code-reviewer` → працює без зайвих deps

### B) .env.example Cleanup (15 min)

**Проблема:** Містить `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` — ці providers не підтримуються.

**Що робити:**
- Видалити unsupported provider keys
- Залишити: `GOOGLE_API_KEY`, `GITHUB_TOKEN` (або `GITLAB_TOKEN`), `LOG_LEVEL`
- Перевірити відповідність з `action.yml` inputs

### C) ROADMAP.md Fix (15 min)

**Проблема:** README посилається на ROADMAP.md якого немає в root.

**Що робити:**
- Перевірити чи ROADMAP.md існує (можливо в docs/)
- Або створити в root з поточним планом (Beta-0.5 → Beta-1 → ...)
- Або оновити README link

### D) raw_yaml Sanitize (30 min)

**Проблема:** `CIInsights.raw_yaml` зберігає повний YAML включно з secrets.
Pydantic repr може показати їх у логах.

**Що робити:**

Варіант 1 (preferred): Видалити `raw_yaml` з `CIInsights`, зберігати тільки parsed data.
```python
class CIInsights(BaseModel):
    # Видалити:
    # raw_yaml: str | None = None

    # Замість цього зберігати parsed CI file content
    # в RawProjectData.ci_files (task 1.1)
    pass
```

Варіант 2: Strip secrets pattern before storing.

## Tests

- [ ] `pip install .` → без langchain/anthropic/openai
- [ ] `.env.example` → тільки робочі keys
- [ ] README → ROADMAP link працює
- [ ] `CIInsights` → немає raw_yaml
- [ ] `make check` passes
- [ ] Docker build працює

## Definition of Done

- [ ] Немає dead deps в pyproject.toml
- [ ] `.env.example` не misleading
- [ ] ROADMAP доступний
- [ ] Немає security concern з raw_yaml
- [ ] `make check` passes

## Estimate: 1.5h total
