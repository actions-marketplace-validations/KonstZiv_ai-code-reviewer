# Task 3.1: Prompt Integration — Implementation Guide

## Актуальний стан коду (після Phase 2)

- `ReviewContext` в `core/models.py:205` має `tasks: tuple[LinkedTask, ...]` (не `task: LinkedTask | None`)
- `build_review_prompt()` в `integrations/prompts.py` приймає `(context: ReviewContext, settings: Settings)`
- `SYSTEM_PROMPT` в `integrations/prompts.py:24`
- `ProjectProfile.to_prompt_context()` в `discovery/models.py:223` — готовий метод

## 1. Додати `project_profile` в ReviewContext

```python
# core/models.py

from ai_reviewer.discovery.models import ProjectProfile  # noqa: TC001

class ReviewContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    mr: MergeRequest = Field(..., description="The merge request to review")
    tasks: tuple[LinkedTask, ...] = Field(default=(), description="Linked tasks")
    repository: str = Field(..., min_length=1, description="Repository name (owner/repo)")
    project_profile: ProjectProfile | None = Field(
        default=None, description="Discovery profile for project context",
    )
```

## 2. Оновити build_review_prompt()

```python
# integrations/prompts.py

def build_review_prompt(context: ReviewContext, settings: Settings) -> str:
    parts = []

    # NEW: Project Context (before existing sections)
    if context.project_profile:
        parts.append("## Project Context")
        parts.append(context.project_profile.to_prompt_context())
        parts.append("")

    # Existing sections (MR info, files, linked tasks, etc.)...
```

## 3. Оновити SYSTEM_PROMPT

Додати блок після існуючих інструкцій:

```
## Project Context Awareness

If a "Project Context" section is provided:
- Respect automated checks. Do NOT comment on issues that CI tools handle.
- If "Skip" items are listed, do not comment on those categories.
- Focus review effort on "Focus" items.
- Follow listed "Conventions".
```

---

## Чеклист

- [ ] `ReviewContext.project_profile` field додано
- [ ] `build_review_prompt()` includes Project Context section
- [ ] `SYSTEM_PROMPT` updated з Project Context Awareness
- [ ] Existing tests still pass (ReviewContext тести потребують update)
- [ ] `uv run pytest -x -q && uv run ruff check && uv run mypy`
