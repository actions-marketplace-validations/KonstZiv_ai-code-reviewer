# Project Structure Overview

This document provides a complete overview of the AI Code Reviewer project structure.

Last Updated: 2026-01-19

---

## Directory Tree

```
ai-code-reviewer/
│
├── GENERAL_PROJECT_DESCRIPTION/       # Project-level documentation
│   ├── PROJECT_CANVAS.md              # Vision, roadmap, metrics
│   ├── PROCESS_PROJECT.md             # Implementation plan & progress
│   └── CONTRIBUTING.md                # Contribution guidelines
│
├── CURRENT_TASK/                      # Active task tracking
│   ├── TASK_DESCRIPTION.md            # Current task specification
│   └── PROCESS_TASK.md                # Task progress tracking
│
├── src/ai_reviewer/                   # Source code
│   ├── __init__.py                    # Package initialization
│   │
│   ├── core/                          # Core models & orchestration
│   │   ├── __init__.py
│   │   ├── models.py                  # Pydantic models (ReviewContext, etc)
│   │   ├── orchestrator.py            # Main workflow orchestrator (LangGraph)
│   │   └── config.py                  # Configuration management
│   │
│   ├── llm/                           # Multi-LLM routing
│   │   ├── __init__.py
│   │   ├── base.py                    # Base abstractions
│   │   ├── router.py                  # LLM router logic
│   │   ├── anthropic_client.py        # Claude integration
│   │   ├── openai_client.py           # GPT integration
│   │   ├── google_client.py           # Gemini integration
│   │   ├── deepseek_client.py         # DeepSeek integration
│   │   └── cost_tracker.py            # Cost tracking
│   │
│   ├── agents/                        # Review agents
│   │   ├── __init__.py
│   │   ├── base.py                    # ReviewAgent abstract class
│   │   ├── security.py                # Security agent
│   │   ├── architecture.py            # Architecture agent
│   │   ├── qa.py                      # QA agent
│   │   └── performance.py             # Performance agent (future)
│   │
│   ├── integrations/                  # Git platform integrations
│   │   ├── __init__.py
│   │   ├── base.py                    # Abstract integration
│   │   ├── gitlab.py                  # GitLab API client
│   │   └── github.py                  # GitHub API client
│   │
│   ├── utils/                         # Utilities
│   │   ├── __init__.py
│   │   ├── git.py                     # Git operations
│   │   ├── errors.py                  # Error handling
│   │   └── logging.py                 # Logging setup
│   │
│   └── cli.py                         # Command-line interface
│
├── tests/                             # Test suite
│   ├── __init__.py
│   │
│   ├── unit/                          # Unit tests
│   │   ├── __init__.py
│   │   ├── test_models.py
│   │   ├── test_llm_router.py
│   │   ├── test_security_agent.py
│   │   └── ...
│   │
│   ├── integration/                   # Integration tests
│   │   ├── __init__.py
│   │   ├── test_llm_providers.py
│   │   ├── test_gitlab_api.py
│   │   └── ...
│   │
│   └── e2e/                           # End-to-end tests
│       ├── __init__.py
│       └── test_review_flow.py
│
├── docs/                              # MkDocs documentation
│   ├── index.md                       # Landing page
│   │
│   ├── getting-started/               # Getting started guides
│   │   ├── quick-start.md
│   │   ├── installation.md
│   │   ├── first-review.md
│   │   └── configuration.md
│   │
│   ├── deployment/                    # Deployment scenarios
│   │   ├── index.md
│   │   ├── solo-dev.md                # FREE tier setup
│   │   ├── small-team.md              # $10-30/month setup
│   │   └── enterprise.md              # Self-hosted setup
│   │
│   ├── guides/                        # Integration guides
│   │   ├── gitlab-ci.md
│   │   ├── github-actions.md
│   │   ├── webhook-mode.md
│   │   ├── architecture.md
│   │   ├── how-it-works.md
│   │   ├── agents.md
│   │   ├── llm-routing.md
│   │   ├── cost-optimization.md
│   │   └── local-dev.md
│   │
│   ├── configuration/                 # Configuration reference
│   │   ├── index.md
│   │   ├── llm-providers.md
│   │   ├── review-settings.md
│   │   ├── repository-context.md
│   │   └── environment.md
│   │
│   ├── development/                   # Developer documentation
│   │   ├── contributing.md
│   │   ├── architecture.md
│   │   ├── adding-agents.md
│   │   ├── adding-providers.md
│   │   ├── testing.md
│   │   └── project-structure.md
│   │
│   ├── api/                           # API reference
│   │   ├── core-models.md
│   │   ├── llm-router.md
│   │   ├── agents.md
│   │   └── integrations.md
│   │
│   ├── troubleshooting/               # Troubleshooting
│   │   ├── common-issues.md
│   │   ├── faq.md
│   │   └── debugging.md
│   │
│   └── about/                         # About pages
│       ├── changelog.md
│       ├── roadmap.md
│       └── license.md
│
├── config/                            # Configuration templates
│   ├── deployment/                    # Deployment-specific configs
│   │   ├── quick-start/
│   │   │   └── config.yml             # Free tier config
│   │   ├── small-team/
│   │   │   └── config.yml             # $10-30/month config
│   │   └── enterprise/
│   │       └── config.yml             # Self-hosted config
│   │
│   └── .ai-reviewer.example.yml      # Full config example
│
├── scripts/                           # Utility scripts
│   ├── setup-dev.sh                   # Development setup
│   ├── run-tests.sh                   # Run test suite
│   └── deploy.sh                      # Deployment helper
│
├── .github/                           # GitHub specific
│   └── workflows/
│       ├── tests.yml                  # CI tests
│       ├── docs.yml                   # Deploy docs
│       └── release.yml                # Release automation
│
├── .gitlab/                           # GitLab specific
│   └── ci/
│       └── .gitlab-ci.yml             # GitLab CI config
│
├── pyproject.toml                     # Project metadata & dependencies
├── mkdocs.yml                         # MkDocs configuration
├── .env.example                       # Environment variables template
├── .gitignore                         # Git ignore rules
├── README.md                          # Project README
├── LICENSE                            # MIT License
└── CHANGELOG.md                       # Version history

```

---

## Key Files Explained

### Project Documentation (AI-Friendly)

These files help AI agents quickly understand the project context:

1. **GENERAL_PROJECT_DESCRIPTION/PROJECT_CANVAS.md**
   - Vision and mission
   - Success metrics
   - Roadmap
   - Recent changes

2. **GENERAL_PROJECT_DESCRIPTION/PROCESS_PROJECT.md**
   - Implementation plan
   - Progress tracking
   - Decision log
   - Next steps

3. **GENERAL_PROJECT_DESCRIPTION/CONTRIBUTING.md**
   - How to contribute
   - Code style guidelines
   - Testing requirements
   - Git workflow

4. **CURRENT_TASK/TASK_DESCRIPTION.md**
   - Active task specification
   - Acceptance criteria
   - Technical approach
   - Dependencies

5. **CURRENT_TASK/PROCESS_TASK.md**
   - Task progress tracking
   - Completed steps
   - Current step
   - Blockers

### Core Source Files

#### Core Module (`src/ai_reviewer/core/`)
- **models.py**: Pydantic models for all data structures
  - `ParsedEvent`, `ReviewContext`, `Finding`, etc.
- **orchestrator.py**: Main LangGraph workflow
  - State machine for review process
- **config.py**: Configuration management
  - Load from .env, .yml, etc.

#### LLM Module (`src/ai_reviewer/llm/`)
- **base.py**: Abstract interfaces
  - `BaseLLMClient`, `LLMRequest`, `LLMResponse`
- **router.py**: Intelligent routing logic
  - Task complexity assessment
  - Provider selection
  - Fallback handling
- **{provider}_client.py**: Provider implementations
  - Anthropic, OpenAI, Google, DeepSeek
- **cost_tracker.py**: Track API costs

#### Agents Module (`src/ai_reviewer/agents/`)
- **base.py**: `ReviewAgent` abstract class
- **security.py**: Security vulnerability detection
- **architecture.py**: Code architecture analysis
- **qa.py**: Testing and quality checks

#### Integrations Module (`src/ai_reviewer/integrations/`)
- **base.py**: Abstract Git platform interface
- **gitlab.py**: GitLab API client
- **github.py**: GitHub API client

### Configuration Files

1. **pyproject.toml**
   - Python project metadata
   - Dependencies (LangChain, LangGraph, LLM SDKs)
   - Build configuration
   - Tool configuration (ruff, mypy, pytest)

2. **.env.example**
   - Template for environment variables
   - API keys for all providers
   - Configuration options

3. **config/deployment/*/config.yml**
   - Deployment-specific configurations
   - Quick-start: Free tier (Gemini)
   - Small-team: Hybrid ($10-30/month)
   - Enterprise: Self-hosted + local LLM

### Documentation

1. **mkdocs.yml**
   - MkDocs configuration
   - Navigation structure
   - Theme settings

2. **docs/**
   - Complete user and developer documentation
   - Tutorials, guides, API reference
   - Organized by user journey

---

## Development Workflow

### 1. Start New Feature
```bash
# Check current task
cat CURRENT_TASK/TASK_DESCRIPTION.md

# Create feature branch
git checkout -b feature/your-feature

# Update task progress
vim CURRENT_TASK/PROCESS_TASK.md
```

### 2. Implement
```bash
# Code in src/ai_reviewer/
# Add tests in tests/
# Update docs in docs/

# Run tests
pytest

# Check code quality
ruff check .
mypy .
```

### 3. Document
```bash
# Update relevant docs
# Add docstrings (Google style)
# Update PROCESS_TASK.md with progress
```

### 4. Commit & Push
```bash
git add .
git commit -m "feat(scope): description"
git push origin feature/your-feature
```

### 5. Create PR/MR
```bash
# Follow template in CONTRIBUTING.md
# Link to CURRENT_TASK
# Wait for CI and review
```

---

## File Naming Conventions

### Python Files
- **Modules**: `lowercase_with_underscores.py`
- **Classes**: `PascalCase` (e.g., `ReviewAgent`)
- **Functions**: `lowercase_with_underscores` (e.g., `build_context`)
- **Constants**: `UPPER_CASE` (e.g., `MAX_TOKENS`)

### Documentation
- **Markdown**: `kebab-case.md` (e.g., `quick-start.md`)
- **Config**: `kebab-case.yml` or `.yml`

### Tests
- **Test files**: `test_*.py` (e.g., `test_llm_router.py`)
- **Test functions**: `test_<what>_<condition>_<expected>()`

---

## Import Structure

```python
# Standard library
import os
from typing import Optional

# Third-party
from langchain.chat_models import BaseChatModel
from pydantic import BaseModel

# Local
from ai_reviewer.core.models import ReviewContext
from ai_reviewer.llm.router import LLMRouter
```

---

## Next Steps

1. **Implement Multi-LLM Router** (Current Task)
2. **Create Security Agent**
3. **Integrate with GitLab**
4. **Write comprehensive tests**
5. **Document all features**

See [PROCESS_PROJECT.md](GENERAL_PROJECT_DESCRIPTION/PROCESS_PROJECT.md) for detailed roadmap.

---

## Questions?

- Read [CONTRIBUTING.md](GENERAL_PROJECT_DESCRIPTION/CONTRIBUTING.md)
- Check [CURRENT_TASK](CURRENT_TASK/)
- Review [Documentation](docs/)
