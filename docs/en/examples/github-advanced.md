# GitHub: Advanced Example

Production-ready configuration with all best practices.

---

## Step 1: Add a Secret

`Settings → Secrets and variables → Actions → New repository secret`

| Name | Value |
|------|-------|
| `GOOGLE_API_KEY` | Your Gemini API key |

---

## Step 2: Create the File

`.github/workflows/ai-review.yml`:

```yaml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]
    # Optional: file filter
    # paths:
    #   - '**.py'
    #   - '**.js'
    #   - '**.ts'

# Cancel previous run on new commit
concurrency:
  group: ai-review-${{ github.event.pull_request.number }}
  cancel-in-progress: true

jobs:
  review:
    name: AI Review
    runs-on: ubuntu-latest

    # Don't run for fork PRs (secrets not available)
    if: github.event.pull_request.head.repo.full_name == github.repository

    # Don't block PR if review fails
    continue-on-error: true

    # Timeout protection
    timeout-minutes: 10

    permissions:
      contents: read
      pull-requests: write

    steps:
      - name: Run AI Code Review
        uses: KonstZiv/ai-code-reviewer@v1
        with:
          google_api_key: ${{ secrets.GOOGLE_API_KEY }}
          language: uk
          language_mode: adaptive
          log_level: INFO
```

---

## What's Included

| Feature | Status | Description |
|---------|--------|-------------|
| Inline comments | :white_check_mark: | With Apply Suggestion |
| Concurrency | :white_check_mark: | Cancels old runs |
| Fork filter | :white_check_mark: | Skips fork PRs |
| Timeout | :white_check_mark: | 10 minutes max |
| Non-blocking | :white_check_mark: | PR not blocked |
| Custom language | :white_check_mark: | `language: uk` |

---

## Variations

### With File Filter

```yaml
on:
  pull_request:
    paths:
      - 'src/**'
      - '**.py'
    paths-ignore:
      - '**.md'
      - 'docs/**'
```

### With Branch Filter

```yaml
on:
  pull_request:
    branches:
      - main
      - develop
```

### With Custom Model

```yaml
- uses: KonstZiv/ai-code-reviewer@v1
  with:
    google_api_key: ${{ secrets.GOOGLE_API_KEY }}
    gemini_model: gemini-1.5-pro  # More powerful model
```

### With DEBUG Logs

```yaml
- uses: KonstZiv/ai-code-reviewer@v1
  with:
    google_api_key: ${{ secrets.GOOGLE_API_KEY }}
    log_level: DEBUG
```

---

## Action Options

| Input | Description | Default |
|-------|-------------|---------|
| `google_api_key` | Gemini API key | **required** |
| `github_token` | GitHub token | `${{ github.token }}` |
| `language` | Response language | `en` |
| `language_mode` | `adaptive` / `fixed` | `adaptive` |
| `gemini_model` | Gemini model | `gemini-2.0-flash` |
| `log_level` | Log level | `INFO` |

---

## Troubleshooting

### Review Not Appearing

1. Check workflow logs
2. Check that it's not a fork PR
3. Check `permissions: pull-requests: write`

### Rate Limit

Concurrency automatically cancels old runs, reducing load.

---

## Next Step

:point_right: [GitLab examples →](gitlab-minimal.md)
