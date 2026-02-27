# Project Discovery

AI ReviewBot includes an automatic **Project Discovery** system that analyzes your repository before each code review. Discovery learns your stack, CI pipeline, and conventions so the reviewer can provide smarter, less noisy feedback.

---

## How It Works

Discovery runs a **4-layer pipeline** on the first PR/MR:

| Layer | Source | Cost |
|-------|--------|------|
| **Layer 0** — Platform API | Languages, file tree, topics from GitHub/GitLab API | Free (API only) |
| **Layer 1** — CI Analysis | Parse GitHub Actions / GitLab CI / Makefile for tools | Free (local parsing) |
| **Layer 2** — Config Files | Read `pyproject.toml`, `package.json`, linter configs | Free (file reads) |
| **Layer 3** — LLM Interpretation | AI interprets ambiguous data (only when Layers 0-2 are insufficient) | ~50-200 tokens |

Each layer degrades gracefully — if one fails, the pipeline continues with what it has.

---

## Attention Zones

Discovery classifies each quality area into one of three **Attention Zones** based on your CI/tooling coverage:

| Zone | Emoji | Meaning | Reviewer behavior |
|------|-------|---------|-------------------|
| **Well Covered** | ✅ | CI tools handle this area | Reviewer **skips** it |
| **Weakly Covered** | ⚠️ | Partial coverage, room for improvement | Reviewer **pays attention** + suggests improvements |
| **Not Covered** | ❌ | No automation detected | Reviewer **focuses** on this area |

### Example zones

| Area | Status | Reason |
|------|--------|--------|
| Formatting | ✅ Well Covered | ruff format in CI |
| Type checking | ✅ Well Covered | mypy --strict in CI |
| Security scanning | ❌ Not Covered | No security scanner in CI |
| Test coverage | ⚠️ Weakly Covered | pytest runs but no coverage threshold |

---

## What Happens Automatically

1. **Discovery analyzes** your repo (languages, CI tools, config files).
2. **Attention Zones are computed** — each quality area is classified as well-covered, weakly-covered, or not-covered.
3. **Review prompt is enriched** with zone-driven instructions (~200-400 tokens).
4. **The reviewer skips** well-covered areas and **focuses** on not-covered ones.

### Discovery Comment

If Discovery finds **gaps** or uncovered zones, it posts a one-time summary comment on the PR/MR:

> ## 🔍 AI ReviewBot: Project Analysis
>
> **Stack:** Python (FastAPI) 3.13, uv
>
> **CI:** ✅ .github/workflows/tests.yml — ruff, mypy, pytest
>
> ### Not Covered (focusing in review)
> - ❌ **Security scanning** — No security scanner detected in CI
>   💡 Consider adding bandit or safety to your pipeline
>
> ### Could Be Improved
> - ⚠️ **Test coverage** — pytest runs but no coverage threshold enforced
>   💡 Add `--cov-fail-under=80` to enforce minimum coverage
>
> **Questions / Gaps:**
> - No security scanner detected in CI
>   *Question:* Do you use any security scanning tools?
>   *Assumption:* Will check for common vulnerabilities manually
>
> ---
> 💡 *Create `.reviewbot.md` in your repo root to customize.*

In **verbose mode** (`discovery_verbose=true`), the comment also includes well-covered zones:

> ### Well Covered (skipping in review)
> - ✅ **Formatting** — ruff format in CI
> - ✅ **Type checking** — mypy --strict in CI

---

## Watch-Files & Caching

Discovery uses **watch-files** to avoid re-running LLM analysis when project configuration hasn't changed.

### How it works

1. **First run:** Discovery runs the full pipeline, LLM returns a `watch_files` list (e.g., `pyproject.toml`, `.github/workflows/tests.yml`).
2. **Subsequent runs:** Discovery hashes each watch-file and compares with the cached snapshot.
3. **If unchanged:** cached result is used — **0 LLM tokens** consumed.
4. **If changed:** LLM re-analyzes the project.

This means repeated PRs on the same branch cost **zero additional tokens** for discovery, as long as the watched configuration files haven't changed.

!!! tip "Token savings"
    On a typical project, the second and subsequent PRs use 0 tokens for discovery. Only changes to CI config, `pyproject.toml`, `package.json`, or similar files trigger a new LLM call.

---

## `discover` CLI Command

You can run discovery standalone (without creating a review) using the `discover` command:

```bash
ai-review discover owner/repo
```

### Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--provider` | `-p` | Git provider | `github` |
| `--json` | | Output as JSON | `false` |
| `--verbose` | `-v` | Show all details (conventions, CI tools, watch-files) | `false` |

### Examples

```bash
# Basic discovery
ai-review discover owner/repo

# JSON output for scripting
ai-review discover owner/repo --json

# Verbose with all details
ai-review discover owner/repo --verbose

# GitLab project
ai-review discover group/project -p gitlab
```

!!! info "Backward compatibility"
    `ai-review` (without subcommand) still runs a review as before. The `discover` subcommand is new.

---

## `.reviewbot.md`

Create a `.reviewbot.md` file in your repository root to provide explicit project context. When this file exists, Discovery **skips the automated pipeline** and uses your configuration directly.

### Format

```markdown
<!-- Auto-generated by AI ReviewBot. Feel free to edit. -->
# .reviewbot.md

## Stack
- **Language:** Python 3.13
- **Framework:** FastAPI
- **Package manager:** uv
- **Layout:** src

## Automated Checks
- **Linting:** ruff
- **Formatting:** ruff
- **Type checking:** mypy
- **Testing:** pytest
- **Security:** bandit
- **CI:** github_actions

## Review Guidance

### Skip (CI handles these)
- Import ordering (ruff handles isort rules)
- Code formatting and style (ruff format in CI)
- Type annotation completeness (mypy --strict in CI)

### Focus
- SQL injection and other OWASP Top 10 vulnerabilities
- API backward compatibility
- Business logic correctness

### Conventions
- All endpoints must return Pydantic response models
- Use dependency injection for database sessions
```

### Sections

| Section | Purpose |
|---------|---------|
| **Stack** | Primary language, version, framework, package manager, layout |
| **Automated Checks** | Tools already running in CI (the reviewer will skip these areas) |
| **Review Guidance → Skip** | Specific areas the reviewer should not comment on |
| **Review Guidance → Focus** | Areas you want extra attention on |
| **Review Guidance → Conventions** | Project-specific rules the reviewer should enforce |

!!! tip "Auto-generation"
    You can let Discovery run once, then copy its findings into `.reviewbot.md` and adjust as needed. The bot includes a footer link suggesting this workflow.

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_REVIEWER_DISCOVERY_ENABLED` | `true` | Enable or disable project discovery |
| `AI_REVIEWER_DISCOVERY_VERBOSE` | `false` | Always post discovery comment (default: only on gaps/uncovered zones) |
| `AI_REVIEWER_DISCOVERY_TIMEOUT` | `30` | Discovery pipeline timeout in seconds (1-300) |

Set `AI_REVIEWER_DISCOVERY_ENABLED` to `false` to skip discovery entirely. The reviewer will still work, but without project-specific context.

```yaml
# GitHub Actions — disable discovery
- uses: KonstZiv/ai-code-reviewer@v1
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    google_api_key: ${{ secrets.GOOGLE_API_KEY }}
    discovery_enabled: 'false'
```

---

## Silent Mode

The discovery comment is **not posted** when:

1. **`.reviewbot.md` exists** in the repository — the bot assumes you've already configured it.
2. **No gaps and no uncovered zones** — everything is well-covered, no questions to ask.
3. **Duplicate detection** — a discovery comment was already posted on this PR/MR.

In all three cases, discovery still runs and enriches the review prompt — it just doesn't post a visible comment.

---

## FAQ

### Can I disable discovery?

Yes. Set `AI_REVIEWER_DISCOVERY_ENABLED=false`. The reviewer will work without project context, the same as before the Discovery feature was added.

### Does discovery cost extra LLM tokens?

On the **first run**: Layers 0-2 are free (API calls and local parsing). Layer 3 (LLM interpretation) is only invoked when the first three layers don't provide enough data — typically 50-200 tokens, which is negligible compared to the review itself (~1,500 tokens).

On **subsequent runs**: if your watch-files haven't changed, discovery uses the **cached result** and costs **0 tokens**.

### Can I edit the auto-generated `.reviewbot.md`?

Yes, absolutely. The file is designed to be human-editable. Change anything you need — the parser is tolerant of extra content and missing sections.

### Does discovery run on every PR?

Discovery enriches the review prompt on every PR. The **LLM call** is cached via watch-files (0 tokens when unchanged). The **discovery comment** is posted only once (duplicate detection prevents repeated posts).

### How do I see all zones including well-covered?

Set `AI_REVIEWER_DISCOVERY_VERBOSE=true`. This forces the discovery comment to always be posted and includes all zones (well-covered, weakly-covered, not-covered).

### What if discovery takes too long?

Set `AI_REVIEWER_DISCOVERY_TIMEOUT` to a higher value (default: 30 seconds, max: 300). If discovery exceeds the timeout, the review proceeds without discovery context.

---

## Next Step

- [Configuration →](configuration.md)
- [GitHub integration →](github.md)
- [GitLab integration →](gitlab.md)
