# Task 4.2: Edge Cases — Implementation Guide

## ⚠️ Revision Note (Phase 3 → Phase 4)

New knowledge from Phase 3:
- **Silent mode**: `should_post_discovery_comment()` returns False when no gaps.
  Basic tests already added (Phase 3 revision). Needs edge case verification.
- **Language support**: `format_discovery_comment(profile, language=...)` supports
  Russian disclaimer. Edge cases for `language="rus"` (ISO 639-3) covered.
- **BOT_NAME constant**: all user-facing strings now use `core.config.BOT_NAME`.
- **Debug logging**: orchestrator logs `file_tree` size, CI paths, content fetch,
  tools detected — can use `caplog` for verification.
- Mock approach: use `_fetch_threads()` + `_enrich_from_threads()` directly,
  not the full reviewer flow, for conversation tests.

---

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
    # Mock _fetch_threads() → BotThread(status=ThreadStatus.ANSWERED)
    # Mock _enrich_from_threads() to verify gap removal
    # Verify: profile enriched from answers
    # Verify: same question NOT asked again (_post_questions_if_needed)
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

### Discovery with Russian language

```python
def test_discovery_comment_russian_disclaimer():
    # Profile with gaps + language="ru"
    # Verify comment body contains Russian disclaimer
    # Also test language="rus" (ISO 639-3)
```

### Silent mode edge cases

```python
def test_no_discovery_comment_noise_empty_gaps():
    # Profile without gaps → should_post returns False
    # Verify post_comment NOT called in reviewer flow

def test_reviewbot_md_suppresses_even_with_gaps():
    # .reviewbot.md in file_tree + gaps present
    # Verify should_post returns False (already covered in unit tests)
```

---

## Чеклист

- [ ] Monorepo test
- [ ] Large file tree test
- [ ] API failure graceful degradation test
- [ ] Second run answers test (mock `_fetch_threads` + `_enrich_from_threads`)
- [ ] Broken .reviewbot.md test
- [ ] Russian disclaimer edge case test
- [ ] Debug logging verification (caplog)
- [ ] `make check` проходить
