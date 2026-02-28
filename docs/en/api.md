# CLI Reference

AI Code Reviewer command reference.

---

## Main Command

```bash
ai-review [OPTIONS]
```

**Behavior:**

- In CI (GitHub Actions / GitLab CI) — automatically detects context
- Manually — need to specify `--provider`, `--repo`, `--pr`

!!! info "Subcommands"
    `ai-review` (without subcommand) runs a review — backward-compatible. Use `ai-review discover` to run discovery standalone.

---

## Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--provider` | `-p` | CI provider | Auto-detect |
| `--repo` | `-r` | Repository (owner/repo) | Auto-detect |
| `--pr` | | PR/MR number | Auto-detect |
| `--help` | | Show help | |
| `--version` | | Show version | |

---

## Providers

| Value | Description |
|-------|-------------|
| `github` | GitHub (GitHub Actions) |
| `gitlab` | GitLab (GitLab CI) |

---

## Usage Examples

### In CI (automatic)

```bash
# GitHub Actions — everything automatic
ai-review

# GitLab CI — everything automatic
ai-review
```

### Manual for GitHub

```bash
export AI_REVIEWER_GOOGLE_API_KEY=your_key
export AI_REVIEWER_GITHUB_TOKEN=your_token

ai-review --provider github --repo owner/repo --pr 123
```

<small>
**Where to get values:**

- `--repo` — from repository URL: `github.com/owner/repo` → `owner/repo`
- `--pr` — number from URL: `github.com/owner/repo/pull/123` → `123`
</small>

### Manual for GitLab

```bash
export AI_REVIEWER_GOOGLE_API_KEY=your_key
export AI_REVIEWER_GITLAB_TOKEN=your_token

ai-review --provider gitlab --repo owner/repo --pr 456
```

<small>
**Where to get values:**

- `--repo` — project path from URL: `gitlab.com/group/project` → `group/project`
- `--pr` — MR number from URL: `gitlab.com/group/project/-/merge_requests/456` → `456`
</small>

### Short Syntax

```bash
ai-review -p github -r owner/repo --pr 123
```

---

## Environment Variables

CLI reads configuration from environment variables:

### Required

| Variable | Description |
|----------|-------------|
| `AI_REVIEWER_GOOGLE_API_KEY` | Gemini API key |
| `AI_REVIEWER_GITHUB_TOKEN` | GitHub token (for GitHub) |
| `AI_REVIEWER_GITLAB_TOKEN` | GitLab token (for GitLab) |

!!! tip "Fallback"
    Old names without prefix (e.g., `GOOGLE_API_KEY`) still work as fallback.

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `AI_REVIEWER_LANGUAGE` | Response language | `en` |
| `AI_REVIEWER_LANGUAGE_MODE` | Language mode | `adaptive` |
| `AI_REVIEWER_GEMINI_MODEL` | Gemini model | `gemini-2.5-flash` |
| `AI_REVIEWER_LOG_LEVEL` | Log level | `INFO` |
| `AI_REVIEWER_GITLAB_URL` | GitLab URL | `https://gitlab.com` |

:point_right: [Full list →](configuration.md)

---

## Auto-detection

### GitHub Actions

CLI automatically uses:

| Variable | Description |
|----------|-------------|
| `GITHUB_ACTIONS` | Environment detection |
| `GITHUB_REPOSITORY` | owner/repo |
| `GITHUB_EVENT_PATH` | JSON with PR details |
| `GITHUB_REF` | Fallback for PR number |

### GitLab CI

CLI automatically uses:

| Variable | Description |
|----------|-------------|
| `GITLAB_CI` | Environment detection |
| `CI_PROJECT_PATH` | owner/repo |
| `CI_MERGE_REQUEST_IID` | MR number |
| `CI_SERVER_URL` | GitLab URL |

---

## Exit Codes

| Code | Description |
|------|-------------|
| `0` | Success |
| `1` | Error (configuration, API, etc.) |

---

## Logging

### Levels

| Level | Description |
|-------|-------------|
| `DEBUG` | Detailed information for debugging |
| `INFO` | General information (default) |
| `WARNING` | Warnings |
| `ERROR` | Errors |
| `CRITICAL` | Critical errors |

### Configuration

```bash
export AI_REVIEWER_LOG_LEVEL=DEBUG
ai-review
```

### Output

CLI uses [Rich](https://rich.readthedocs.io/) for formatted output:

```
[12:34:56] INFO     Detected CI Provider: github
[12:34:56] INFO     Context extracted: owner/repo PR #123
[12:34:57] INFO     Fetching PR diff...
[12:34:58] INFO     Analyzing code with Gemini...
[12:35:02] INFO     Review completed successfully
```

---

## Errors

### Configuration Error

```
Configuration Error: AI_REVIEWER_GOOGLE_API_KEY is too short (minimum 10 characters)
```

**Cause:** Invalid configuration.

**Solution:** Check environment variables.

### Context Error

```
Context Error: Could not determine PR number from GitHub Actions context.
```

**Cause:** Workflow not running for PR.

**Solution:** Make sure workflow has `on: pull_request`.

### Provider Not Detected

```
Error: Could not detect CI environment.
Please specify --provider, --repo, and --pr manually.
```

**Cause:** Running outside CI.

**Solution:** Specify all parameters manually.

---

## Discover Command

Run project discovery standalone (without creating a review):

```bash
ai-review discover <REPO> [OPTIONS]
```

### Arguments

| Argument | Description |
|----------|-------------|
| `REPO` | Repository (owner/repo) |

### Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--provider` | `-p` | Git provider | `github` |
| `--json` | | Output as JSON | `false` |
| `--verbose` | `-v` | Show all details (conventions, CI tools, watch-files) | `false` |

### Examples

```bash
# GitHub repository
ai-review discover owner/repo

# JSON output
ai-review discover owner/repo --json

# Verbose mode
ai-review discover owner/repo -v

# GitLab project
ai-review discover group/project -p gitlab
```

### Example Output

```
🔍 Discovering project context...

Stack: Python (FastAPI) 3.13, uv
CI: ✅ .github/workflows/tests.yml — ruff, mypy, pytest

Attention Zones:
  ✅ Formatting — ruff format in CI
  ✅ Type checking — mypy --strict in CI
  ❌ Security scanning — No security scanner detected
  ⚠️ Test coverage — no coverage threshold
```

---

## Docker

Run via Docker:

```bash
docker run --rm \
  -e AI_REVIEWER_GOOGLE_API_KEY=your_key \
  -e AI_REVIEWER_GITHUB_TOKEN=your_token \
  ghcr.io/konstziv/ai-code-reviewer:1 \
  --provider github \
  --repo owner/repo \
  --pr 123
```

---

## Version

```bash
ai-review --version
```

```
AI Code Reviewer 0.1.0
```

---

## Help

```bash
ai-review --help
```

```
Usage: ai-review [OPTIONS]

  Run AI Code Reviewer.

  Automatically detects CI environment and reviews the current Pull Request.
  Can also be run manually by providing arguments.

Options:
  -p, --provider [github|gitlab]  CI provider (auto-detected if not provided)
  -r, --repo TEXT                 Repository name (e.g. owner/repo). Auto-detected in CI.
  --pr INTEGER                    Pull Request number. Auto-detected in CI.
  --help                          Show this message and exit.
```

---

## Next Step

- [Troubleshooting →](troubleshooting.md)
- [Examples →](examples/index.md)
