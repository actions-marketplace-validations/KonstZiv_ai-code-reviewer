# Task 4.2: Discovery Verbose Mode

## Тип: Feature | Пріоритет: MEDIUM | Estimate: 30min

## Для борди

Зараз discovery comment поститься ТІЛЬКИ при наявності gaps. Користувач не знає що бот проаналізував проєкт. Додати `discovery_verbose` mode для always-post.

**Acceptance Criteria:**
- [ ] `AI_REVIEWER_DISCOVERY_VERBOSE=true` → discovery comment поститься завжди
- [ ] Default: `false` (поточна поведінка — silent mode)
- [ ] Comment відрізняється від звичайного (немає "Questions" секції якщо gaps немає)
- [ ] `action.yml` оновлений з новим input

---

# Implementation Guide

## Settings

```python
# core/config.py
discovery_verbose: bool = Field(
    default=False,
    validation_alias=AliasChoices("AI_REVIEWER_DISCOVERY_VERBOSE", "DISCOVERY_VERBOSE"),
    description="Always post discovery comment (even without gaps)",
)
```

## `discovery/comment.py` — оновити `should_post_discovery_comment()`

```python
def should_post_discovery_comment(
    profile: ProjectProfile,
    existing_comments: tuple[str, ...] = (),
    *,
    verbose: bool = False,  # ← NEW parameter
) -> bool:
    # .reviewbot.md present -> silent ALWAYS
    if _REVIEWBOT_MD_PATH in profile.platform_data.file_tree:
        return False

    # Duplicate detection
    if any(DISCOVERY_COMMENT_HEADING in body for body in existing_comments):
        return False

    # Verbose mode: always post
    if verbose:
        return True

    # Default: only when gaps exist
    return bool(profile.gaps)
```

## `reviewer.py` — передати verbose

```python
# В _post_discovery_comment():
if not should_post_discovery_comment(
    profile, existing_comments, verbose=settings.discovery_verbose
):
    ...
```

## `action.yml`

```yaml
discovery_verbose:
  description: 'Always post discovery comment (even without gaps)'
  required: false
  default: 'false'
```

## Checklist

- [ ] `discovery_verbose` в Settings
- [ ] `should_post_discovery_comment()` з verbose param
- [ ] Передати в reviewer.py
- [ ] `action.yml` input
- [ ] Unit test: verbose=True → always post
- [ ] `make check` passes
