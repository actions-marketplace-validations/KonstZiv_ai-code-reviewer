# AI ReviewBot

[![PyPI version](https://img.shields.io/pypi/v/ai-reviewbot)](https://pypi.org/project/ai-reviewbot/)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Tests](https://github.com/KonstZiv/ai-code-reviewer/actions/workflows/tests.yml/badge.svg)](https://github.com/KonstZiv/ai-code-reviewer/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/KonstZiv/ai-code-reviewer/branch/main/graph/badge.svg)](https://codecov.io/gh/KonstZiv/ai-code-reviewer)

AI-powered code review tool for **GitHub** and **GitLab** that provides intelligent feedback with **inline suggestions** and one-click "Apply" button.

<p align="center">
  <a href="https://konstziv.github.io/ai-code-reviewer/">📚 Documentation</a> •
  <a href="https://konstziv.github.io/ai-code-reviewer/quick-start/">🚀 Quick Start</a> •
  <a href="https://github.com/marketplace/actions/ai-code-reviewer">🛒 GitHub Marketplace</a>
</p>

---

## ✨ Features

- 🤖 **AI-Powered Analysis** — Uses Google Gemini for deep code understanding
- 💡 **Inline Suggestions** — Comments directly on code lines with GitHub's "Apply suggestion" button
- 🔒 **Security Focus** — Identifies vulnerabilities with severity levels (Critical, Warning, Info)
- 🌍 **Multi-Language** — Responds in your PR/MR language (adaptive mode)
- ✨ **Good Practices** — Highlights what you're doing right, not just issues
- 📊 **Transparent Metrics** — Shows tokens, latency, and estimated cost
- 🦊 **GitHub & GitLab** — Native support for both platforms

## 🚀 Quick Start

### GitHub Actions (Recommended)

```yaml
# .github/workflows/ai-review.yml
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
          github_token: ${{ secrets.GITHUB_TOKEN }}
          google_api_key: ${{ secrets.GOOGLE_API_KEY }}
```

### GitLab CI

```yaml
# .gitlab-ci.yml
ai-review:
  image: ghcr.io/konstziv/ai-code-reviewer:1
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
    GITLAB_TOKEN: $GITLAB_TOKEN  # Project Access Token with 'api' scope
```

### PyPI

```bash
pip install ai-reviewbot

# Set environment variables
export GOOGLE_API_KEY="your-key"
export GITHUB_TOKEN="your-token"

# Run review
ai-review --repo owner/repo --pr 123
```

### Docker

```bash
# DockerHub
docker pull koszivdocker/ai-reviewbot:1

# GitHub Container Registry
docker pull ghcr.io/konstziv/ai-code-reviewer:1
```

## 📖 Documentation

Full documentation available in **6 languages**:

| Language | Link |
|----------|------|
| 🇬🇧 English | [Documentation](https://konstziv.github.io/ai-code-reviewer/) |
| 🇺🇦 Українська | [Документація](https://konstziv.github.io/ai-code-reviewer/uk/) |
| 🇩🇪 Deutsch | [Dokumentation](https://konstziv.github.io/ai-code-reviewer/de/) |
| 🇪🇸 Español | [Documentación](https://konstziv.github.io/ai-code-reviewer/es/) |
| 🇲🇪 Crnogorski | [Dokumentacija](https://konstziv.github.io/ai-code-reviewer/sr/) |
| 🇮🇹 Italiano | [Documentazione](https://konstziv.github.io/ai-code-reviewer/it/) |

## ⚙️ Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_API_KEY` | — | **Required.** Google Gemini API key |
| `GITHUB_TOKEN` | — | GitHub token (for GitHub) |
| `GITLAB_TOKEN` | — | GitLab token (for GitLab) |
| `LANGUAGE` | `en` | Response language (ISO 639 code) |
| `LANGUAGE_MODE` | `adaptive` | `adaptive` (detect from PR) or `fixed` |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model to use |
| `LOG_LEVEL` | `INFO` | Logging level |

See [Configuration Guide](https://konstziv.github.io/ai-code-reviewer/configuration/) for all options.

## 🎯 Example Output

The reviewer provides structured feedback with inline suggestions:

### Summary Comment

> **🤖 AI Code Review**
>
> **📊 Summary** — Found 2 issues and 1 good practice.
>
> | Category | Critical | Warning | Info |
> |----------|----------|---------|------|
> | Security | 1 | 0 | 0 |
> | Code Quality | 0 | 1 | 0 |
>
> **✨ Good Practices** — Excellent error handling in `api/handlers.py`
>
> ---
> ⏱️ 1.2s | 🪙 1,540 tokens | 💰 ~$0.002

### Inline Comment with "Apply" Button

> ⚠️ **SQL Injection Risk**
>
> User input is concatenated directly into SQL query.
>
> ```suggestion
> cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
> ```
>
> 💡 **Why this matters:** SQL injection allows attackers to execute arbitrary SQL commands. Always use parameterized queries.
>
> 📚 [Learn more](https://owasp.org/www-community/attacks/SQL_Injection)

## 🛠️ Development

```bash
# Clone repository
git clone https://github.com/KonstZiv/ai-code-reviewer.git
cd ai-code-reviewer

# Install dependencies with uv
uv sync --all-groups

# Run tests
uv run pytest

# Run linters
uv run ruff check .
uv run mypy src/

# Build documentation
uv run mkdocs serve
```

## 📦 Installation Options

| Method | Command | Best For |
|--------|---------|----------|
| **GitHub Action** | `uses: KonstZiv/ai-code-reviewer@v1` | GitHub projects |
| **Docker** | `docker pull koszivdocker/ai-reviewbot` | GitLab CI |
| **PyPI** | `pip install ai-reviewbot` | Local testing |

## 💰 Cost Estimate

Using Gemini 2.5 Flash:
- **Input:** $0.075 / 1M tokens
- **Output:** $0.30 / 1M tokens
- **Average review:** ~$0.002 (1,500 tokens)

100 reviews/month ≈ **$0.20**

## 📄 License

Apache 2.0 — See [LICENSE](LICENSE) for details.

## 🤝 Contributing

Contributions are welcome! See [Contributing Guide](CONTRIBUTING.md).

## 📬 Support

- 🐛 [Report a Bug](https://github.com/KonstZiv/ai-code-reviewer/issues/new?template=bug_report.md)
- 💡 [Request a Feature](https://github.com/KonstZiv/ai-code-reviewer/issues/new?template=feature_request.md)
- 📚 [Documentation](https://konstziv.github.io/ai-code-reviewer/)

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/KonstZiv">Kostyantin Zivenko</a>
</p>
