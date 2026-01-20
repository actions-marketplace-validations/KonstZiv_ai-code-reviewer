# Sprint 1: MVP Code Reviewer - Tool Verification & First Release

**Sprint Goal:** Create minimal working code reviewer to verify entire development workflow and toolchain

**Duration:** 1 sprint (flexible)
**Status:** 🎯 Ready to Start
**Type:** Foundation Sprint
**Priority:** Critical (blocks all other work)

---

## 🎯 Sprint Objectives

### Primary Goal
Build the simplest possible working code reviewer that:
- Analyzes GitHub MR for critical vulnerabilities
- Checks if code changes match task description
- Posts review as MR comment
- Uses free Google Gemini API

### Secondary Goal (Most Important!)
**Verify entire development workflow:**
- ✅ Code quality tools (ruff, mypy)
- ✅ Testing pipeline (pytest + coverage)
- ✅ Pre-commit hooks
- ✅ CI/CD pipeline (tests, docs, release)
- ✅ Multi-language documentation
- ✅ PyPI publishing
- ✅ LLM integration

---

## 📊 Success Criteria

### Functional Requirements
1. ✅ Reviewer runs on GitHub Actions after quality checks
2. ✅ Retrieves: MR title, description, comments, linked task, code changes
3. ✅ Analyzes using Google Gemini (free tier)
4. ✅ Posts comment with:
   - Critical vulnerabilities (if any)
   - Alignment with task description
   - OR "Insufficient data to answer"
5. ✅ Documentation in 6 languages (uk, en, de, es, me, it)

### Technical Requirements
1. ✅ All tools working: ruff, mypy, pytest, pre-commit
2. ✅ CI passes: quality, tests, docs build
3. ✅ CD works: tag → PyPI + docs deployment
4. ✅ Test coverage ≥80%
5. ✅ Type hints on all functions
6. ✅ Multi-language docs auto-deploy

---

## 🏗️ Architecture

### High-Level Flow
```
GitHub MR Created/Updated
    ↓
CI Triggered
    ↓
Quality Checks (ruff, mypy)
    ↓
Tests (pytest)
    ↓
AI Reviewer Job
    ↓
[Fetch MR Data] → [Get Linked Task] → [Build Context]
    ↓
[Send to Gemini] → [Parse Response]
    ↓
[Post Review Comment]
```

### Components to Build

```python
# Minimal structure
src/ai_reviewer/
├── core/
│   ├── models.py          # Pydantic models for MR, Task, Review
│   └── config.py          # Config management
│
├── integrations/
│   ├── github.py          # Fetch MR data
│   └── gemini.py          # Google Gemini client
│
├── reviewer.py            # Main review logic
└── cli.py                 # Entry point: ai-review command
```

### Data Models

```python
# Simplified models
class MergeRequest:
    title: str
    description: str
    comments: List[Comment]
    changes: List[FileChange]

class LinkedTask:
    title: str
    description: str

class ReviewContext:
    mr: MergeRequest
    task: LinkedTask | None

class ReviewResult:
    has_critical_vulnerabilities: bool
    vulnerabilities: List[str]
    matches_task: bool | None  # None = can't determine
    reasoning: str
```

---

## 📋 Sprint Backlog (8 Tasks)

### Task 1: Development Environment Setup ⚙️
**Goal:** Set up and verify all development tools

**Steps:**
1. Verify `uv` installation and `uv.lock`
2. Test `make install` → all deps install
3. Run `make quick` → ruff + mypy pass on empty modules
4. Add dummy test → `make test` passes
5. Verify pre-commit hooks work
6. Document tooling in README

**Acceptance Criteria:**
- ✅ `make install` works
- ✅ `make quick` passes
- ✅ `make test` shows coverage
- ✅ Pre-commit blocks bad commits
- ✅ All commands documented

**Time Estimate:** 1-2 hours

---

### Task 2: Core Data Models 📐
**Goal:** Define Pydantic models for all data structures

**Steps:**
1. Create `src/ai_reviewer/core/models.py`
2. Define models: `MergeRequest`, `LinkedTask`, `ReviewContext`, `ReviewResult`
3. Add validation and examples
4. Write unit tests for models
5. Type hints everywhere
6. Add docstrings (Google style)

**Acceptance Criteria:**
- ✅ All models have type hints
- ✅ Models validate input
- ✅ Unit tests cover edge cases
- ✅ Coverage ≥90% for models.py
- ✅ Mypy passes strict mode

**Files:**
- `src/ai_reviewer/core/models.py` (~200 lines)
- `tests/unit/test_models.py` (~150 lines)

**Time Estimate:** 2-3 hours

---

### Task 3: Configuration Management ⚙️
**Goal:** Load and validate configuration from environment

**Steps:**
1. Create `src/ai_reviewer/core/config.py`
2. Use pydantic-settings for env vars
3. Support: GITHUB_TOKEN, GOOGLE_API_KEY
4. Add validation and defaults
5. Write tests

**Acceptance Criteria:**
- ✅ Loads from environment
- ✅ Validates required fields
- ✅ Clear error messages
- ✅ Unit tests
- ✅ Type hints

**Files:**
- `src/ai_reviewer/core/config.py` (~100 lines)
- `tests/unit/test_config.py` (~80 lines)

**Time Estimate:** 1-2 hours

---

### Task 4: GitHub Integration 🔗
**Goal:** Fetch MR data from GitHub API

**Steps:**
1. Create `src/ai_reviewer/integrations/github.py`
2. Use PyGithub library
3. Implement functions:
   - `get_pull_request(repo, pr_number) -> MergeRequest`
   - `get_linked_task(pr) -> LinkedTask | None`
   - `post_review_comment(pr, comment)`
4. Handle errors gracefully
5. Write integration tests (mock GitHub API)
6. Add retry logic

**Acceptance Criteria:**
- ✅ Fetches PR data correctly
- ✅ Extracts linked task from PR body
- ✅ Posts comments to PR
- ✅ Handles API errors
- ✅ Integration tests with mocks
- ✅ Type hints

**Files:**
- `src/ai_reviewer/integrations/github.py` (~250 lines)
- `tests/integration/test_github.py` (~200 lines)

**Time Estimate:** 3-4 hours

---

### Task 5: Google Gemini Integration 🤖
**Goal:** Connect to Google Gemini API for analysis

**Steps:**
1. Create `src/ai_reviewer/integrations/gemini.py`
2. Use google-generativeai library
3. Implement:
   - `analyze_code_changes(context) -> ReviewResult`
   - Prompt engineering for vulnerability detection
   - Prompt for task alignment check
4. Parse structured output from LLM
5. Handle API errors and rate limits
6. Write tests with mock responses

**Acceptance Criteria:**
- ✅ Connects to Gemini API
- ✅ Sends proper prompts
- ✅ Parses responses into ReviewResult
- ✅ Handles errors gracefully
- ✅ Tests with mocked API
- ✅ Type hints

**Files:**
- `src/ai_reviewer/integrations/gemini.py` (~200 lines)
- `tests/integration/test_gemini.py` (~150 lines)

**Time Estimate:** 3-4 hours

---

### Task 6: Review Logic Implementation 🧠
**Goal:** Implement main review workflow

**Steps:**
1. Create `src/ai_reviewer/reviewer.py`
2. Implement `review_pull_request()`:
   - Fetch PR data from GitHub
   - Get linked task if exists
   - Build ReviewContext
   - Send to Gemini
   - Format review comment
   - Post to PR
3. Add logging
4. Error handling
5. Write end-to-end test

**Acceptance Criteria:**
- ✅ Complete workflow works
- ✅ Proper error handling
- ✅ Logging at key steps
- ✅ E2E test (mocked)
- ✅ Type hints

**Files:**
- `src/ai_reviewer/reviewer.py` (~150 lines)
- `tests/e2e/test_review_flow.py` (~100 lines)

**Time Estimate:** 2-3 hours

---

### Task 7: CLI & GitHub Action 🎮
**Goal:** Create command-line interface and GitHub Action

**Steps:**
1. Create `src/ai_reviewer/cli.py`
2. Use typer for CLI
3. Add command: `ai-review github --pr <number> --repo <owner/name>`
4. Create `.github/workflows/ai-review.yml`
5. Configure to run after tests
6. Test manually on real PR

**Acceptance Criteria:**
- ✅ CLI works: `ai-review github --pr 1 --repo user/repo`
- ✅ GitHub Action configured
- ✅ Runs after tests pass
- ✅ Posts review comment
- ✅ Help text clear

**Files:**
- `src/ai_reviewer/cli.py` (~100 lines)
- `.github/workflows/ai-review.yml` (~50 lines)

**Time Estimate:** 2 hours

---

### Task 8: Multi-Language Documentation 📚
**Goal:** Create documentation in 6 languages

**Steps:**
1. Setup i18n plugin for MkDocs
2. Create documentation structure:
   ```
   docs/
   ├── en/  # English (primary)
   ├── uk/  # Ukrainian
   ├── de/  # German
   ├── es/  # Spanish
   ├── me/  # Montenegrin
   └── it/  # Italian
   ```
3. Write core docs (English first):
   - index.md - Overview
   - quick-start.md - 5-minute setup
   - configuration.md - Config reference
   - github-actions.md - CI/CD setup
4. Translate to other languages (can use Claude/ChatGPT)
5. Configure mkdocs.yml for i18n
6. Test docs build locally
7. Verify auto-deploy on push

**Acceptance Criteria:**
- ✅ Docs in 6 languages
- ✅ Language switcher works
- ✅ All languages have core docs
- ✅ Builds without errors
- ✅ Auto-deploys to GitHub Pages
- ✅ Each language accessible

**Files:**
- `docs/*/` (6 languages × 4 docs = 24 files)
- `mkdocs.yml` updated

**Time Estimate:** 4-5 hours (with translation help)

---

## 🧪 Testing Strategy

### Unit Tests
- **Target:** All pure functions
- **Coverage:** ≥90% for each module
- **Location:** `tests/unit/`

### Integration Tests
- **Target:** GitHub API, Gemini API
- **Mocking:** All external APIs
- **Coverage:** Happy path + error cases

### E2E Test
- **Target:** Full review workflow
- **Mocking:** GitHub and Gemini
- **Scenario:** Real PR structure → Review comment

### Manual Testing
1. Create test PR on GitHub
2. Trigger CI manually
3. Verify review posted
4. Check comment quality
5. Test error scenarios

---

## 🚀 CI/CD Pipeline

### On Push/PR (tests.yml)
```yaml
jobs:
  quality:
    - ruff check
    - ruff format --check
    - mypy src/

  test:
    - pytest --cov=ai_reviewer
    - Upload coverage

  ai-review:  # NEW
    needs: [quality, test]
    - Run ai-review on PR
```

### On Tag (release.yml)
```yaml
# Tag: v0.1.0
jobs:
  test: [run all tests]
  build: [build package]
  publish-pypi: [publish to PyPI]
  github-release: [create GitHub release]
  deploy-docs: [deploy multi-lang docs]
```

### Docs Deployment (docs.yml)
```yaml
# On push to main
- Build all language variants
- Deploy to GitHub Pages
```

---

## 📝 Documentation Structure

```
docs/
├── en/
│   ├── index.md              # "AI Code Reviewer"
│   ├── quick-start.md        # 5-minute setup
│   ├── configuration.md      # Environment vars
│   └── github-actions.md     # CI/CD guide
│
├── uk/  # Same structure, Ukrainian
├── de/  # Same structure, German
├── es/  # Same structure, Spanish
├── me/  # Same structure, Montenegrin
└── it/  # Same structure, Italian
```

**Note:** Start with English, then translate. Can use AI for initial translation, then review.

---

## 🎓 Learning Outcomes

After this sprint, you'll have verified:
- ✅ Complete Python project setup
- ✅ Quality tools (ruff, mypy, pytest)
- ✅ Pre-commit hooks workflow
- ✅ GitHub Actions CI/CD
- ✅ PyPI publishing process
- ✅ Multi-language documentation
- ✅ LLM integration basics
- ✅ Real-world testing

---

## 🚧 Known Limitations (by design)

This MVP intentionally has limitations:
- ❌ No cost tracking
- ❌ No LLM routing (only Gemini)
- ❌ No repository context
- ❌ Simple analysis (not comprehensive)
- ❌ No caching
- ❌ No agent system
- ❌ No architecture/QA checks

**These are features for later sprints!**

---

## 📚 Reference Materials

### APIs
- **GitHub API:** https://docs.github.com/en/rest
- **PyGithub:** https://pygithub.readthedocs.io/
- **Google Gemini:** https://ai.google.dev/docs

### Tools
- **MkDocs i18n:** https://github.com/ultrabug/mkdocs-static-i18n
- **Pydantic:** https://docs.pydantic.dev/
- **Typer:** https://typer.tiangolo.com/

---

## 🎯 Definition of Done

Sprint is complete when:
1. ✅ All 8 tasks completed
2. ✅ All tests pass (coverage ≥80%)
3. ✅ CI/CD pipeline green
4. ✅ Manual test on real PR successful
5. ✅ Documentation deployed in 6 languages
6. ✅ Tag v0.1.0 created → PyPI published
7. ✅ GitHub release created with notes
8. ✅ All team members can run locally

---

## 📌 Next Steps After Sprint

After completing MVP:
1. Collect feedback from first review
2. Identify pain points
3. Plan Sprint 2: Enhanced Analysis
   - Multiple agents (security, architecture, QA)
   - LLM routing for cost optimization
   - Repository context
   - Better prompt engineering

---

## 🤝 Collaboration Notes

**For AI Assistant (Claude):**
- Read this task description before each work session
- Update PROCESS_TASK.md as you complete steps
- Ask clarifying questions before implementation
- Run tests after each component
- Keep code simple and well-documented

**For Human Developer:**
- Review AI's implementation proposals
- Test manually on real PRs
- Provide feedback on review quality
- Approve before moving to next task
- Update process docs as needed

---

**Let's build this! 🚀**
