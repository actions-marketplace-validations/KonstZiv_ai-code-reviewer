# AI ReviewBot

[![Docker Pulls](https://img.shields.io/docker/pulls/koszivdocker/ai-reviewbot)](https://hub.docker.com/r/koszivdocker/ai-reviewbot)
[![Docker Image Size](https://img.shields.io/docker/image-size/koszivdocker/ai-reviewbot/1)](https://hub.docker.com/r/koszivdocker/ai-reviewbot)
[![GitHub](https://img.shields.io/github/license/KonstZiv/ai-code-reviewer)](https://github.com/KonstZiv/ai-code-reviewer)

AI-powered code review tool for GitHub and GitLab with **inline suggestions** and "Apply" button support.

## Features

- 🤖 **AI-Powered Reviews** — Uses Google Gemini for intelligent code analysis
- 💡 **Inline Suggestions** — Comments directly on code lines with "Apply suggestion" button
- 🌍 **Multi-Language** — Responds in the language of your PR/MR (adaptive mode)
- 🔒 **Security Focus** — Identifies vulnerabilities with severity levels
- 📊 **Metrics** — Shows tokens used, latency, and estimated cost
- 🦊 **GitHub & GitLab** — Works with both platforms

## Quick Start

### GitLab CI

```yaml
ai-review:
  image: koszivdocker/ai-reviewbot:1
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

> **Note:** Set `AI_REVIEWER_GOOGLE_API_KEY` and `AI_REVIEWER_GITLAB_TOKEN` as CI/CD variables in Settings -- they are inherited by jobs automatically.

### Docker Run (Local Testing)

```bash
docker run --rm \
  -e AI_REVIEWER_GOOGLE_API_KEY="your-api-key" \
  -e AI_REVIEWER_GITHUB_TOKEN="your-token" \
  -e GITHUB_REPOSITORY="owner/repo" \
  -e GITHUB_EVENT_NUMBER="123" \
  koszivdocker/ai-reviewbot:1
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AI_REVIEWER_GOOGLE_API_KEY` | Yes | Google Gemini API key |
| `AI_REVIEWER_GITHUB_TOKEN` | GitHub | GitHub token for API access |
| `AI_REVIEWER_GITLAB_TOKEN` | GitLab | Personal Access Token with `api` scope |
| `AI_REVIEWER_LANGUAGE` | No | Response language (default: `en`) |
| `AI_REVIEWER_LANGUAGE_MODE` | No | `adaptive` or `fixed` (default: `adaptive`) |
| `AI_REVIEWER_GEMINI_MODEL` | No | Model to use (default: `gemini-2.5-flash`) |
| `AI_REVIEWER_LOG_LEVEL` | No | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

## Tags

- `1.0.0`, `1.0`, `1` — Specific versions (recommended)
- `1.0.0a1` — Alpha/pre-release versions
- `latest` — Latest stable release (available after v1.0.0)

## Links

- 📚 [Full Documentation](https://konstziv.github.io/ai-code-reviewer/)
- 🐙 [GitHub Repository](https://github.com/KonstZiv/ai-code-reviewer)
- 🚀 [GitHub Action](https://github.com/marketplace/actions/ai-code-reviewer)
- 📦 [PyPI Package](https://pypi.org/project/ai-reviewbot/)

## License

Apache 2.0 — See [LICENSE](https://github.com/KonstZiv/ai-code-reviewer/blob/main/LICENSE) for details.
