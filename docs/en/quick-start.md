# Quick Start

Get AI Code Reviewer running in 1 minute.

---

## GitHub Actions

### Step 1: Add a secret

`Settings → Secrets and variables → Actions → New repository secret`

| Name | Value |
|------|-------|
| `GOOGLE_API_KEY` | Your Gemini API key |

:point_right: [Get your key](https://aistudio.google.com/)

### Step 2: Create a workflow

In the root of your project, create file `.github/workflows/ai-review.yml`

`.github/workflows/ai-review.yml`:

```yaml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

concurrency:
  group: ai-review-${{ github.event.pull_request.number }}
  cancel-in-progress: true

jobs:
  review:
    runs-on: ubuntu-latest
    # Don't run for fork PRs (no access to secrets)
    if: github.event.pull_request.head.repo.full_name == github.repository
    permissions:
      contents: read
      pull-requests: write

    steps:
      - uses: KonstZiv/ai-code-reviewer@v1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          google_api_key: ${{ secrets.GOOGLE_API_KEY }}
```

### Step 3: Create a PR

Done! AI review will appear automatically.

---

## GitLab CI

### Step 1: Add a variable

`Settings → CI/CD → Variables`

| Name | Value | Options |
|------|-------|---------|
| `GOOGLE_API_KEY` | Your Gemini API key | Masked, Protected |

:point_right: [Get your key](https://aistudio.google.com/)

### Step 2: Add a job

In the root of your project, create file `.gitlab-ci.yml`

`.gitlab-ci.yml`:

```yaml
ai-review:
  image: ghcr.io/konstziv/ai-code-reviewer:1
  stage: test
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  allow_failure: true
  variables:
    GITLAB_TOKEN: $CI_JOB_TOKEN
    GOOGLE_API_KEY: $GOOGLE_API_KEY
```

!!! note "For inline comments"
    `CI_JOB_TOKEN` has limitations. For full functionality use [Personal Access Token](gitlab.md#personal-access-token).

### Step 3: Create an MR

Done! AI review will appear as comments on the MR.

---

## Local Run

For local testing you need:

- **GOOGLE_API_KEY** — [get it at Google AI Studio](https://aistudio.google.com/)
- **GITHUB_TOKEN** or **GITLAB_TOKEN** — depending on the platform:
    - GitHub: [how to get PAT](github.md#get-token)
    - GitLab: [how to get PAT](gitlab.md#get-token)

=== "GitHub"

    ```bash
    # Install
    pip install ai-reviewbot

    # Configure
    export GOOGLE_API_KEY=your_key
    export GITHUB_TOKEN=your_github_pat

    # Run for GitHub PR
    ai-review --repo owner/repo --pr-number 123
    ```

=== "GitLab"

    ```bash
    # Install
    pip install ai-reviewbot

    # Configure
    export GOOGLE_API_KEY=your_key
    export GITLAB_TOKEN=your_gitlab_pat

    # Run for GitLab MR
    ai-review --provider gitlab --project owner/repo --mr-iid 123
    ```

---

## What's Next?

| Task | Document |
|------|----------|
| Configure language | [Configuration](configuration.md) |
| Optimize for GitHub | [GitHub Guide](github.md) |
| Optimize for GitLab | [GitLab Guide](gitlab.md) |
| See examples | [Examples](examples/index.md) |

---

## Example Result

After running, you'll see inline comments:

![AI Review Example](https://via.placeholder.com/800x400?text=AI+Review+Inline+Comment)

Each comment contains:

- :red_circle: / :yellow_circle: / :blue_circle: Severity badge
- Problem description
- **"Apply suggestion"** button
- Collapsible "Why does this matter?" explanation

---

## Troubleshooting

### Review not appearing?

1. Check CI job logs
2. Verify that `GOOGLE_API_KEY` is correct
3. For GitHub: check `permissions: pull-requests: write`
4. For fork PRs: secrets are not available

### Rate limit?

Gemini free tier: 15 RPM. Wait a minute.

:point_right: [All issues →](troubleshooting.md)
