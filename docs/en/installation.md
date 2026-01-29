# Installation

The installation option depends on your use case and goals.

---

## 1. CI/CD — Automated Review {#ci-cd}

The most common scenario: AI Code Reviewer runs automatically when a PR/MR is created or updated.

### GitHub Actions

The simplest way for GitHub — use the ready-made GitHub Action:

```yaml
# .github/workflows/ai-review.yml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

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

**Required setup:**

| What's needed | Where to configure |
|---------------|-------------------|
| `GOOGLE_API_KEY` | Repository → Settings → Secrets → Actions |

:point_right: [Full example with concurrency and filtering →](quick-start.md#github-actions)

:point_right: [Detailed GitHub Guide →](github.md)

---

### GitLab CI

For GitLab, use the Docker image in `.gitlab-ci.yml`:

```yaml
# .gitlab-ci.yml
ai-review:
  image: ghcr.io/konstziv/ai-code-reviewer:1
  stage: test
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  allow_failure: true
  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
```

**Required setup:**

| What's needed | Where to configure |
|---------------|-------------------|
| `GOOGLE_API_KEY` | Project → Settings → CI/CD → Variables (Masked) |
| `GITLAB_TOKEN` | Optional, for inline comments ([details](gitlab.md#tokens)) |

:point_right: [Full example →](quick-start.md#gitlab-ci)

:point_right: [Detailed GitLab Guide →](gitlab.md)

---

## 2. Local Testing / Evaluation {#local}

### Why is this needed?

1. **Evaluation before deployment** — try on a real PR before adding to CI
2. **Debugging** — if something doesn't work in CI, run locally with `--log-level DEBUG`
3. **Retrospective review** — analyze an old PR/MR
4. **Demo** — show the team/management how it works

### How it works

```
Local terminal
       │
       ▼
   ai-review CLI
       │
       ├──► GitHub/GitLab API (reads PR/MR, diff, linked issues)
       │
       ├──► Gemini API (gets review)
       │
       └──► GitHub/GitLab API (publishes comments)
```

### Required Environment Variables

| Variable | Description | When needed | How to get |
|----------|-------------|-------------|------------|
| `GOOGLE_API_KEY` | Gemini API key | **Always** | [Google AI Studio](https://aistudio.google.com/) |
| `GITHUB_TOKEN` | GitHub Personal Access Token | For GitHub | [Instructions](github.md#get-token) |
| `GITLAB_TOKEN` | GitLab Personal Access Token | For GitLab | [Instructions](gitlab.md#get-token) |

---

### Option A: Docker (recommended)

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

---

### Option B: pip / uv

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

## 3. Corporate Environment (air-gapped) {#airgapped}

For environments with limited internet access.

### Limitations

!!! warning "Gemini API access required"
    AI Code Reviewer uses Google Gemini API for code analysis.

    **Required access to:** `generativelanguage.googleapis.com`

    Support for locally deployed LLM models is **not implemented** yet.

### Docker Image Deployment

**Step 1: On a machine with internet access**

```bash
# Pull the image
docker pull ghcr.io/konstziv/ai-code-reviewer:1

# Save to file
docker save ghcr.io/konstziv/ai-code-reviewer:1 > ai-code-reviewer.tar
```

**Step 2: Transfer the file to the closed environment**

**Step 3: Load into internal registry**

```bash
# Load from file
docker load < ai-code-reviewer.tar

# Re-tag for internal registry
docker tag ghcr.io/konstziv/ai-code-reviewer:1 \
    registry.internal.company.com/devops/ai-code-reviewer:1

# Push
docker push registry.internal.company.com/devops/ai-code-reviewer:1
```

**Step 4: Use in GitLab CI**

```yaml
ai-review:
  image: registry.internal.company.com/devops/ai-code-reviewer:1
  script:
    - ai-review
  variables:
    GITLAB_URL: https://gitlab.internal.company.com
    GOOGLE_API_KEY: $GOOGLE_API_KEY
```

---

## 4. Contributors / Development {#development}

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
