# Installation

The installation option depends on your use case and goals.

---

## 1. CI/CD — Automated Review {#ci-cd}

The most common scenario: AI Code Reviewer runs automatically when a PR/MR is created or updated.

Set up in 5 minutes:

- :octicons-mark-github-16: **[Set up review for GitHub →](quick-start.md)**

    :point_right: [Workflow examples →](examples/github-minimal.md) · [Detailed GitHub Guide →](github.md)

- :simple-gitlab: **[Set up review for GitLab →](quick-start.md)**

    :point_right: [Workflow examples →](examples/gitlab-minimal.md) · [Detailed GitLab Guide →](gitlab.md)

For fine-tuning see [Configuration →](configuration.md)

---

## 2. Standalone Deployment: CLI/Docker {#standalone}

CLI and Docker image allow running AI Code Reviewer outside the standard CI pipeline.

### Use Cases

| Scenario | How to implement |
|----------|------------------|
| **Manual run** | Local terminal — debugging, demo, evaluation |
| **Scheduled review** | GitLab Scheduled Pipeline / GitHub Actions `schedule` / cron |
| **Batch review** | Script iterating over open PR/MR |
| **Own server** | Docker on server with Git API access |
| **On-demand review** | Webhook → container launch |

### Required Environment Variables

| Variable | Description | When needed | How to get |
|----------|-------------|-------------|------------|
| `GOOGLE_API_KEY` | Gemini API key | **Always** | [Google AI Studio](https://aistudio.google.com/) |
| `GITHUB_TOKEN` | GitHub Personal Access Token | For GitHub | [Instructions](github.md#get-token) |
| `GITLAB_TOKEN` | GitLab Personal Access Token | For GitLab | [Instructions](gitlab.md#get-token) |

---

### Manual Run

For debugging, demo, evaluation before deployment, retrospective PR/MR analysis.

#### Docker (recommended)

No Python installation required — everything is in the container.

**Step 1: Pull the image**

```bash
docker pull ghcr.io/konstziv/ai-code-reviewer:1
```

**Step 2: Run the review**

=== "GitHub PR"

    ```bash
    docker run --rm \
      -e GOOGLE_API_KEY=your_api_key \
      -e GITHUB_TOKEN=your_token \
      ghcr.io/konstziv/ai-code-reviewer:1 \
      --repo owner/repo --pr-number 123
    ```

=== "GitLab MR"

    ```bash
    docker run --rm \
      -e GOOGLE_API_KEY=your_api_key \
      -e GITLAB_TOKEN=your_token \
      ghcr.io/konstziv/ai-code-reviewer:1 \
      --provider gitlab --project owner/repo --mr-iid 123
    ```

!!! tip "Docker images"
    Available from two registries:

    - `ghcr.io/konstziv/ai-code-reviewer:1` — GitHub Container Registry
    - `koszivdocker/ai-reviewbot:1` — DockerHub

#### pip / uv

Installation as a Python package.

**Step 1: Install**

=== "pip"

    ```bash
    pip install ai-reviewbot
    ```

=== "uv"

    ```bash
    uv tool install ai-code-reviewer
    ```

=== "pipx"

    ```bash
    pipx install ai-code-reviewer
    ```

!!! note "Python version"
    Requires Python **3.13+**

**Step 2: Set up variables**

```bash
export GOOGLE_API_KEY=your_api_key
export GITHUB_TOKEN=your_token  # or GITLAB_TOKEN for GitLab
```

**Step 3: Run**

=== "GitHub PR"

    ```bash
    ai-review --repo owner/repo --pr-number 123
    ```

=== "GitLab MR"

    ```bash
    ai-review --provider gitlab --project owner/repo --mr-iid 123
    ```

---

### Optional Variables

Additional variables are available for fine-tuning:

| Variable | Default | Effect |
|----------|---------|--------|
| `LANGUAGE` | `en` | Response language (ISO 639) |
| `LANGUAGE_MODE` | `adaptive` | Language detection mode |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model |
| `LOG_LEVEL` | `INFO` | Logging level |

:point_right: [Full list of variables →](configuration.md#optional)

---

### Scheduled Reviews

Running reviews on a schedule — for resource savings or when instant feedback is not needed.

=== "GitLab Scheduled Pipeline"

    ```yaml
    # .gitlab-ci.yml
    ai-review-scheduled:
      image: ghcr.io/konstziv/ai-code-reviewer:1
      script:
        - |
          # Get list of open MRs
          MR_LIST=$(curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
            "$CI_SERVER_URL/api/v4/projects/$CI_PROJECT_ID/merge_requests?state=opened" \
            | jq -r '.[].iid')

          # Run review for each MR
          for MR_IID in $MR_LIST; do
            echo "Reviewing MR !$MR_IID"
            ai-review --provider gitlab --project $CI_PROJECT_PATH --pr $MR_IID || true
          done
      rules:
        - if: $CI_PIPELINE_SOURCE == "schedule"
      variables:
        GOOGLE_API_KEY: $GOOGLE_API_KEY
        GITLAB_TOKEN: $GITLAB_TOKEN
    ```

    **Schedule setup:** Project → Build → Pipeline schedules → New schedule

=== "GitHub Actions Schedule"

    ```yaml
    # .github/workflows/scheduled-review.yml
    name: Scheduled AI Review

    on:
      schedule:
        - cron: '0 9 * * *'  # Daily at 9:00 UTC

    jobs:
      review-open-prs:
        runs-on: ubuntu-latest
        steps:
          - name: Get open PRs and review
            env:
              GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
              GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
            run: |
              # Get list of open PRs
              PRS=$(gh pr list --repo ${{ github.repository }} --state open --json number -q '.[].number')

              for PR in $PRS; do
                echo "Reviewing PR #$PR"
                docker run --rm \
                  -e GOOGLE_API_KEY -e GITHUB_TOKEN \
                  ghcr.io/konstziv/ai-code-reviewer:1 \
                  --repo ${{ github.repository }} --pr $PR || true
              done
    ```

---

### Own Server / Private Environment

For deployment on your own infrastructure with Git API access.

**Options:**

- **Docker on server** — run via cron, systemd timer, or as a service
- **Kubernetes** — CronJob for scheduled reviews
- **Self-hosted GitLab** — add `GITLAB_URL` variable (see example below)

**Cron job example:**

```bash
# /etc/cron.d/ai-review
# Daily at 10:00 run review for all open MRs
0 10 * * * reviewer /usr/local/bin/review-all-mrs.sh
```

```bash
#!/bin/bash
# /usr/local/bin/review-all-mrs.sh
export GOOGLE_API_KEY="your_key"
export GITLAB_TOKEN="your_token"

MR_LIST=$(curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://gitlab.company.com/api/v4/projects/123/merge_requests?state=opened" \
  | jq -r '.[].iid')

for MR_IID in $MR_LIST; do
  docker run --rm \
    -e GOOGLE_API_KEY -e GITLAB_TOKEN \
    ghcr.io/konstziv/ai-code-reviewer:1 \
    --provider gitlab --project group/repo --pr $MR_IID
done
```

!!! tip "Self-hosted GitLab"
    For self-hosted GitLab add the `GITLAB_URL` variable:

    ```bash
    -e GITLAB_URL=https://gitlab.company.com
    ```

---

## 3. Contributors / Development {#development}

If you have the time and inspiration to help develop the package, or want to use it as a foundation for your own development — we sincerely welcome and encourage such actions!

### Development Installation

```bash
# Clone the repository
git clone https://github.com/KonstZiv/ai-code-reviewer.git
cd ai-code-reviewer

# Install dependencies (we use uv)
uv sync

# Verify
uv run ai-review --help

# Run tests
uv run pytest

# Run quality checks
uv run ruff check .
uv run mypy .
```

!!! info "uv"
    We use [uv](https://github.com/astral-sh/uv) for dependency management.

    Install: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Project Structure

```
ai-code-reviewer/
├── src/ai_reviewer/      # Source code
│   ├── core/             # Models, config, formatting
│   ├── integrations/     # GitHub, GitLab, Gemini
│   └── utils/            # Utilities
├── tests/                # Tests
├── docs/                 # Documentation
└── examples/             # CI configuration examples
```

:point_right: [How to contribute →](https://github.com/KonstZiv/ai-code-reviewer/blob/main/CONTRIBUTING.md)

---

## Requirements {#requirements}

### System Requirements

| Component | Requirement |
|-----------|-------------|
| Python | 3.13+ (for pip install) |
| Docker | 20.10+ (for Docker) |
| OS | Linux, macOS, Windows |
| RAM | 256MB+ |
| Network | Access to `generativelanguage.googleapis.com` |

### API Keys

| Key | Required | How to get |
|-----|----------|------------|
| Google Gemini API | **Yes** | [Google AI Studio](https://aistudio.google.com/) |
| GitHub PAT | For GitHub | [Instructions](github.md#get-token) |
| GitLab PAT | For GitLab | [Instructions](gitlab.md#get-token) |

### Gemini API Limits

!!! info "Free tier"
    Google Gemini has a free tier:

    | Limit | Value |
    |-------|-------|
    | Requests per minute | 15 RPM |
    | Tokens per day | 1M |
    | Requests per day | 1500 |

    This is sufficient for most projects.

---

## Next Step

:point_right: [Quick Start →](quick-start.md)
