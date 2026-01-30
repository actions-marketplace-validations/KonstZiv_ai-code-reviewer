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
  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
    GITLAB_TOKEN: $GITLAB_TOKEN  # Project Access Token with 'api' scope
```

### Docker Run (Local Testing)

```bash
docker run --rm \
  -e GOOGLE_API_KEY="your-api-key" \
  -e GITHUB_TOKEN="your-token" \
  -e GITHUB_REPOSITORY="owner/repo" \
  -e GITHUB_EVENT_NUMBER="123" \
  koszivdocker/ai-reviewbot:1
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | Yes | Google Gemini API key |
| `GITHUB_TOKEN` | GitHub | GitHub token for API access |
| `GITLAB_TOKEN` | GitLab | Project Access Token with `api` scope |
| `LANGUAGE` | No | Response language (default: `en`) |
| `LANGUAGE_MODE` | No | `adaptive` or `fixed` (default: `adaptive`) |
| `GEMINI_MODEL` | No | Model to use (default: `gemini-2.5-flash`) |
| `LOG_LEVEL` | No | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

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
