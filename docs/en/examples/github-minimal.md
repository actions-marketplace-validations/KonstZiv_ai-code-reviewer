# GitHub: Minimal Example

The simplest configuration for GitHub Actions.

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
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write

    steps:
      - uses: KonstZiv/ai-code-reviewer@v1
        with:
          google_api_key: ${{ secrets.GOOGLE_API_KEY }}
```

---

## Step 3: Create a PR

Done! AI review will appear automatically.

---

## What's Included

| Feature | Status |
|---------|--------|
| Inline comments | :white_check_mark: |
| Apply Suggestion button | :white_check_mark: |
| Language adaptivity | :white_check_mark: (adaptive) |
| Metrics | :white_check_mark: |

---

## Limitations

| Limitation | Solution |
|------------|----------|
| Fork PRs don't work | Expected behavior |
| No concurrency | See [advanced example](github-advanced.md) |
| English by default | Add `language: uk` |

---

## Next Step

:point_right: [Advanced example →](github-advanced.md)
