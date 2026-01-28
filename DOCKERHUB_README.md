# AI ReviewBot

[![Docker Pulls](https://img.shields.io/docker/pulls/konstziv/ai-reviewbot)](https://hub.docker.com/r/konstziv/ai-reviewbot)
[![Docker Image Size](https://img.shields.io/docker/image-size/konstziv/ai-reviewbot/latest)](https://hub.docker.com/r/konstziv/ai-reviewbot)
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
  image: konstziv/ai-reviewbot:latest
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
    GITLAB_TOKEN: $CI_JOB_TOKEN
```

### Docker Run (Local Testing)

```bash
docker run --rm \
  -e GOOGLE_API_KEY="your-api-key" \
  -e GITHUB_TOKEN="your-token" \
  -e GITHUB_REPOSITORY="owner/repo" \
  -e GITHUB_EVENT_NUMBER="123" \
  konstziv/ai-reviewbot:latest
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_API_KEY` | Yes | Google Gemini API key |
| `GITHUB_TOKEN` | GitHub | GitHub token for API access |
| `GITLAB_TOKEN` | GitLab | GitLab token (or `CI_JOB_TOKEN`) |
| `LANGUAGE` | No | Response language (default: `en`) |
| `LANGUAGE_MODE` | No | `adaptive` or `fixed` (default: `adaptive`) |
| `GEMINI_MODEL` | No | Model to use (default: `gemini-2.5-flash`) |
| `LOG_LEVEL` | No | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

## Tags

- `latest` — Latest stable release
- `1.0.0`, `1.0`, `1` — Specific versions
- `1.0.0a1` — Alpha/pre-release versions

## Links

- 📚 [Full Documentation](https://konstziv.github.io/ai-code-reviewer/)
- 🐙 [GitHub Repository](https://github.com/KonstZiv/ai-code-reviewer)
- 🚀 [GitHub Action](https://github.com/marketplace/actions/ai-code-reviewer)
- 📦 [PyPI Package](https://pypi.org/project/ai-reviewbot/)

## License

Apache 2.0 — See [LICENSE](https://github.com/KonstZiv/ai-code-reviewer/blob/main/LICENSE) for details.
