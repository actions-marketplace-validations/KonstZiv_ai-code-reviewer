# Task 1.3: File Tree Truncation Handling

## Тип: Reliability | Пріоритет: MEDIUM | Estimate: 30min

## Опис (для борди)

GitHub Git Trees API повертає max ~10,000 files. Для великих monorepo tree truncated — `getattr(tree, "truncated", False)`. Warning логується, але `PlatformData` не має flag. Orchestrator може пропустити CI файли.

**Acceptance Criteria:**
- [ ] `PlatformData` має поле `file_tree_truncated: bool = False`
- [ ] GitHub/GitLab implementations встановлюють flag при truncation
- [ ] Orchestrator логує warning і додає Gap якщо truncated
- [ ] Unit test для truncated scenario

---

# Implementation Guide

## Зміни

### `discovery/models.py` — додати поле

```python
class PlatformData(BaseModel):
    # ... existing fields ...
    file_tree_truncated: bool = Field(
        default=False,
        description="True if file tree was truncated by platform API"
    )
```

### `integrations/github.py` — `get_file_tree()`

```python
# В GitHubClient.get_file_tree():
tree = repo.get_git_tree(branch, recursive=True)
truncated = getattr(tree, "truncated", False)
if truncated:
    logger.warning("Git tree for %s truncated (>10,000 files)", repo_name)
# Повертати truncated flag... але метод повертає tuple[str, ...]
# Варіант: повернути через side effect або змінити return type
```

**Рішення щодо API:** Метод `get_file_tree()` повертає `tuple[str, ...]`. Щоб не ламати ABC, найпростіший підхід — додати окремий метод або property. АЛЕ простіше: orchestrator вже робить `_collect_platform_data()` де має доступ до provider. Додати `is_file_tree_truncated()` метод або передавати через return type зміну.

**Рекомендований підхід (мінімальні зміни):** Orchestrator перевіряє розмір file_tree. Якщо >9000 files — вважати truncated.

```python
# orchestrator.py — _collect_platform_data()
_TREE_TRUNCATION_THRESHOLD = 9_000

file_tree = self._repo.get_file_tree(repo_name)
file_tree_truncated = len(file_tree) >= _TREE_TRUNCATION_THRESHOLD

return PlatformData(
    # ...existing...
    file_tree_truncated=file_tree_truncated,
)
```

### `discovery/orchestrator.py` — gap для truncated tree

```python
# В _detect_gaps() або в discover():
if platform_data.file_tree_truncated:
    logger.warning("File tree truncated — CI files may be missed")
    # Додати gap тільки якщо CI files не знайдено
    if not platform_data.ci_config_paths:
        gaps.append(Gap(
            observation="Repository has >10,000 files, file tree may be incomplete",
            question="Where is your CI configuration located?",
            default_assumption="Standard CI paths checked",
        ))
```

## Checklist

- [ ] Додати `file_tree_truncated` поле в `PlatformData`
- [ ] Встановити flag в orchestrator по threshold
- [ ] Gap для truncated tree без CI files
- [ ] Unit test
- [ ] `make check` passes
