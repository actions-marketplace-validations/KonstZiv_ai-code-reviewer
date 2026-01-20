# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Code Reviewer — autonomous AI agent for intelligent code review in CI/CD pipelines. Multi-LLM support (Claude, GPT, Gemini, DeepSeek, Ollama) with cost optimization via hybrid local + cloud routing.

**Status:** Early development — structure established, implementation in progress.

## Commands

```bash
# Setup (first time)
uv venv && source .venv/bin/activate
uv sync --all-groups
uv run pre-commit install

# Development workflow
make quick              # Format + lint + mypy (run before commit)
make test               # Run tests with coverage
make test-fast          # Run tests without coverage (-x flag)
uv run pytest tests/unit/test_file.py -v  # Single test file
uv run pytest -k "test_name"              # Run specific test

# Code quality
uv run ruff format .    # Format code
uv run ruff check .     # Lint
uv run ruff check --fix .  # Lint with autofix
uv run mypy src/        # Type checking

# Documentation
make docs               # Serve docs locally (http://127.0.0.1:8000)

# Pre-commit
uv run pre-commit run --all-files  # Run all hooks manually
```

## Architecture

```
src/ai_reviewer/
├── core/           # Models, orchestrator, config (Pydantic models)
├── llm/            # Multi-LLM router — provider abstraction layer
├── agents/         # Review agents (Security, Architecture, QA)
├── integrations/   # Git platforms (GitHub, GitLab via PyGithub, python-gitlab)
└── utils/          # Shared utilities

tests/
├── unit/           # Unit tests
├── integration/    # Integration tests (may call external APIs, mark: @pytest.mark.integration)
└── e2e/            # End-to-end tests (mark: @pytest.mark.e2e)
```

**Key dependencies:** LangChain + LangGraph for LLM orchestration, Pydantic for data models, Click/Typer for CLI.

## Code Standards

- **Python 3.13+** with strict type hints (mypy --strict)
- **Ruff** for linting/formatting (line length: 100)
- **Google-style docstrings** for public APIs
- **Pytest** with fixtures (not unittest-style classes)
- Entry point: `ai_reviewer.cli:main` (command: `ai-review`)

## Project Documentation

- `CURRENT_TASK/` — Active task tracking (read before starting work)
- `GENERAL_PROJECT_DESCRIPTION/PROJECT_CANVAS.md` — Vision, roadmap
- `GENERAL_PROJECT_DESCRIPTION/PROCESS_PROJECT.md` — Implementation progress
- `theory/` — Design decisions, architecture research

## Git Workflow

Branch naming: `feature/<name>`, `fix/<name>`, `docs/<name>`, `refactor/<name>`

Commit style: Conventional Commits — `feat(scope): description`, `fix(scope): description`
