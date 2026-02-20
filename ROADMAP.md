# Roadmap: v1.0.0a8

## Overview

Three incremental PRs to improve the AI reviewer:
1. Update default Gemini model
2. Inline review comments (reply-able)
3. Dialogue support (threaded context)

---

## PR #1: Default model → `gemini-3-flash-preview`

**Branch:** `61-switch-default-model-gemini-3-flash`
**Status:** ✅ Done (tag `v1.0.0a6`)

- [x] Update `DEFAULT_MODEL` in `gemini.py`
- [x] Add `gemini-3-flash-preview` to `GEMINI_PRICING`
- [x] Update default in `config.py` + docstrings
- [x] Update `action.yml` default
- [x] Version bump → `1.0.0a6` in `pyproject.toml`
- [x] Update tests (`test_config.py`, `test_gemini.py`)
- [x] Update docs (6 languages) — configuration.md, api.md, installation.md
- [x] Verify: pytest, ruff, mypy, mkdocs --strict
- [x] Create PR, review, merge

---

## PR #2: Inline comments + short summary

**Branch:** direct to `main`
**Status:** ✅ Done (tag `v1.0.0a7`)

### Inline comments
- [x] Add `review_post_inline_comments` setting to `config.py`
- [x] Create `format_review_summary()` in `formatter.py` (short summary without individual issues)
- [x] Create `_build_review_submission()` in `reviewer.py` (partition issues → inline vs fallback)
- [x] Wire `submit_review()` into `review_pull_request()` with fallback to old behavior
- [x] Update duplicate detection (compare summary only)
- [x] Add `action.yml` input + env passthrough
- [x] Tests: `test_formatter.py`, `test_reviewer.py` (new), `test_review_flow.py` (update), `test_config.py`
- [x] Update docs (6 languages) — `REVIEW_POST_INLINE_COMMENTS`

### Rename env vars (avoid org-level conflicts in GitLab)
- [x] All 14 fields: `AI_REVIEWER_*` prefix via `AliasChoices` + `populate_by_name=True`
- [x] Update `config.py`, `cli.py`, `gemini.py` error messages
- [x] Update `action.yml` — new env var names
- [x] Update docs (6 languages × 6 files) — new env var names with migration note
- [x] Update examples (github-workflow.yml, gitlab-ci.yml)

### Verification
- [x] 417 tests passed, ruff clean, mypy clean, mkdocs --strict OK
- [x] `v1` tag updated to point to `v1.0.0a7`

---

## PR #3: Dialogue support — threaded replies

**Branch:** direct to `main`
**Status:** ✅ Done (tag `v1.0.0a8`)

- [x] Add `comment_id`, `parent_comment_id`, `thread_id` to `Comment` model
- [x] GitHub: capture threading fields from review comments
- [x] GitLab: switch `mr.notes.list()` → `mr.discussions.list()` for thread structure
- [x] Add `_group_comments_into_threads()` in `prompts.py`
- [x] Add `_format_thread_for_prompt()`, `_render_*_threaded()` in `prompts.py`
- [x] Update `_build_comments_section()` to use threaded rendering
- [x] Update `SYSTEM_PROMPT` with dialogue-aware instructions
- [x] Add `review_enable_dialogue` setting to `config.py`
- [x] Add `action.yml` input + env passthrough
- [x] Fix duplicate suggestion block in inline comments
- [x] Tests: 434 total (+17 new) — models, prompts (threading), integration (GitHub/GitLab), config
- [x] Update docs (6 languages) — `REVIEW_ENABLE_DIALOGUE`
- [x] Verify: pytest, ruff, mypy, mkdocs --strict
- [x] `v1` tag updated to point to `v1.0.0a8`

---

## Notes

- All 6 language docs (en, uk, de, es, it, sr) must be updated together
- After each release: update `v1` major tag (`git tag -f v1 v{version} && git push origin v1 --force`)
