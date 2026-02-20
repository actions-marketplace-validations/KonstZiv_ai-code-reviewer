# Roadmap: v1.0.0a6

## Overview

Three incremental PRs to improve the AI reviewer:
1. Update default Gemini model
2. Inline review comments (reply-able)
3. Dialogue support (threaded context)

---

## PR #1: Default model → `gemini-3-flash-preview`

**Branch:** `61-switch-default-model-gemini-3-flash`
**Status:** ✅ Done (tag `v1.0.0a6` pushed)

- [x] Update `DEFAULT_MODEL` in `gemini.py`
- [x] Add `gemini-3-flash-preview` to `GEMINI_PRICING`
- [x] Update default in `config.py` + docstrings
- [x] Update `action.yml` default
- [x] Version bump → `1.0.0a6` in `pyproject.toml`
- [x] Update tests (`test_config.py`, `test_gemini.py`)
- [x] Update docs (6 languages) — configuration.md, api.md, installation.md, github.md
- [x] Verify: pytest, ruff, mypy, mkdocs --strict
- [x] Create PR, review, merge

---

## PR #2: Inline comments + short summary + env var rename

**Branch:** `62-inline-review-comments`
**Status:** ⬜ Not started

> Key: `submit_review()` already implemented in both providers but not wired in.

### Inline comments
- [ ] Add `review_post_inline_comments` setting to `config.py`
- [ ] Create `format_review_summary()` in `formatter.py` (short summary without individual issues)
- [ ] Create `_build_review_submission()` in `reviewer.py` (partition issues → inline vs fallback)
- [ ] Wire `submit_review()` into `review_pull_request()` with fallback to old behavior
- [ ] Update duplicate detection (compare summary only)
- [ ] Add `action.yml` input + env passthrough
- [ ] Tests: `test_formatter.py`, `test_reviewer.py` (new), `test_review_flow.py` (update), `test_config.py`
- [ ] Update docs (6 languages) — `REVIEW_POST_INLINE_COMMENTS`

### Rename env vars (avoid org-level conflicts in GitLab)
- [ ] `GOOGLE_API_KEY` → `AI_REVIEWER_GOOGLE_API_KEY` (keep old as fallback/alias)
- [ ] `GITHUB_TOKEN` → `AI_REVIEWER_GITHUB_TOKEN` (keep old as fallback/alias)
- [ ] `GITLAB_TOKEN` → `AI_REVIEWER_GITLAB_TOKEN` (keep old as fallback/alias)
- [ ] `GEMINI_MODEL` → `AI_REVIEWER_GEMINI_MODEL` (keep old as fallback/alias)
- [ ] Update `config.py` — add `validation_alias` / `AliasChoices` for backward compat
- [ ] Update `action.yml` — new env var names
- [ ] Update docs (6 languages) — new env var names with migration note
- [ ] Update examples (github-workflow.yml, gitlab-ci.yml)

### Verification
- [ ] Verify: pytest, ruff, mypy, mkdocs --strict
- [ ] Manual test against real MR
- [ ] Create PR, review, merge

---

## PR #3: Dialogue support — threaded replies

**Branch:** `63-dialogue-support`
**Status:** ⬜ Not started

- [ ] Add `thread_id`, `in_reply_to_id`, `comment_id` to `Comment` model
- [ ] GitHub: capture threading fields from review comments
- [ ] GitLab: switch `mr.notes.list()` → `mr.discussions.list()` for thread structure
- [ ] Add `_group_comments_into_threads()` in `prompts.py`
- [ ] Add `_render_threaded_comments()` in `prompts.py`
- [ ] Update `_build_comments_section()` to use threaded rendering
- [ ] Update `SYSTEM_PROMPT` with dialogue-aware instructions
- [ ] Add `review_enable_dialogue` setting to `config.py`
- [ ] Add `action.yml` input + env passthrough
- [ ] Tests: models, prompts (threading), integration (GitHub/GitLab), config
- [ ] Update docs (6 languages) — `REVIEW_ENABLE_DIALOGUE`
- [ ] Verify: pytest, ruff, mypy, mkdocs --strict
- [ ] Create PR, review, merge

---

## Notes

- PRs are independent and can be merged in any order
- Version bump (`1.0.0a5` → `1.0.0a6`) goes in PR #1
- All 6 language docs (en, uk, de, es, it, sr) must be updated together
- `submit_review()` + `LineComment` + `ReviewSubmission` + `format_inline_comment()` already exist in codebase
