# Task 4.2: Edge Cases — Implementation Guide

## Тести

### Monorepo

```python
def test_monorepo_multiple_languages():
    languages = {"Python": 45.0, "TypeScript": 35.0, "Go": 20.0}
    # primary_language should be Python (highest)
    # CI tools from all languages should be detected
```

### Large file tree

```python
def test_large_file_tree_truncation():
    tree = tuple(f"src/file_{i}.py" for i in range(10_000))
    # Should not crash, should be truncated or handled
```

### Second run with answers

```python
def test_second_run_reads_answers():
    # Setup: BotThread with ANSWERED status
    # Verify: profile enriched from answers
    # Verify: same question NOT asked again
```

### Broken .reviewbot.md

```python
def test_partial_reviewbot_md():
    content = """# .reviewbot.md
    ## Stack
    - **Language:** Python
    # Missing other sections
    """
    profile = parse_reviewbot_md(content)
    assert profile.platform_data.primary_language == "Python"
    # Should not crash on missing sections
```

---

## Чеклист

- [ ] Monorepo test
- [ ] Large file tree test
- [ ] API failure graceful degradation test
- [ ] Second run answers test
- [ ] Broken .reviewbot.md test
- [ ] `make check` проходить
