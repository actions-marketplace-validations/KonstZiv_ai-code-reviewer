# Task 3.1: Prompt Integration — Implementation Guide

## 1. Оновити ReviewContext

```python
# core/models.py

class ReviewContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    mr: MergeRequest
    task: LinkedTask | None = None
    repository: str = ""
    project_profile: ProjectProfile | None = None  # NEW
```

## 2. Оновити build_review_prompt()

```python
# integrations/prompts.py

def build_review_prompt(context: ReviewContext, settings: Settings) -> str:
    parts = []

    # NEW: Project Context
    if context.project_profile:
        parts.append("## Project Context")
        parts.append(context.project_profile.to_prompt_context())
        parts.append("")

    # Existing sections...
    parts.append("## Language")
    # ...
```

## 3. Оновити SYSTEM_PROMPT

Додати блок:

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

- [ ] `ReviewContext.project_profile` field
- [ ] `build_review_prompt()` includes Project Context
- [ ] `SYSTEM_PROMPT` updated
- [ ] Existing tests still pass
- [ ] `make check` проходить
