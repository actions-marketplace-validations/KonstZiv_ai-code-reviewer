# Project Structure Overview

This document provides a complete overview of the AI Code Reviewer project structure.

**Last Updated:** 2026-01-20

**Project Status:** 🚧 Early Development
- Structure established
- Dependencies configured
- Implementation in progress (see CURRENT_TASK/)

---

## Directory Tree

**Current structure** (showing only what exists):

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
├── theory/                            # Theoretical foundation
│   └── ai_code_review_unified_flow.md # Research & design
│
├── src/ai_reviewer/                   # Source code (structure only)
│   ├── __init__.py                    # Package initialization
│   ├── core/__init__.py               # Core module (empty - to be implemented)
│   ├── llm/__init__.py                # LLM routing (empty - to be implemented)
│   ├── agents/__init__.py             # Review agents (empty - to be implemented)
│   ├── integrations/__init__.py       # Git integrations (empty - to be implemented)
│   └── utils/__init__.py              # Utilities (empty - to be implemented)
│
├── tests/                             # Test structure
│   ├── __init__.py
│   ├── unit/__init__.py               # Unit tests (to be added)
│   ├── integration/__init__.py        # Integration tests (to be added)
│   └── e2e/__init__.py                # E2E tests (to be added)
│
├── docs/                              # MkDocs documentation
│   ├── index.md                       # Landing page
│   └── guides/
│       └── github-actions.md          # GitHub Actions guide
│
├── config/deployment/                 # Deployment configs (placeholders)
│   ├── quick-start/
│   │   └── config.yml                 # To be replaced with README.md
│   ├── small-team/
│   │   └── config.yml                 # To be replaced with README.md
│   └── enterprise/
│       └── config.yml                 # To be replaced with README.md
│
├── scripts/                           # Utility scripts (empty)
│
├── .github/workflows/                 # GitHub Actions
│   ├── tests.yml                      # CI tests
│   ├── docs.yml                       # Documentation deployment
│   └── release.yml                    # Release automation
│
├── pyproject.toml                     # Project metadata (PEP 735)
├── uv.lock                            # Locked dependencies
├── Makefile                           # Development shortcuts
├── mkdocs.yml                         # MkDocs configuration
├── .env.example                       # Environment template
├── .pre-commit-config.yaml            # Pre-commit hooks
├── .gitignore                         # Git ignore rules
├── README.md                          # Project README
├── LICENSE                            # Apache License 2.0
├── NOTICE                             # Copyright notice
└── PROJECT_STRUCTURE.md               # This file

```

**Note:** This project is in early development. Most modules exist as empty `__init__.py` files to establish structure. Implementation is in progress - see `CURRENT_TASK/` for active work.

---

## Key Files Explained

### License & Attribution

1. **LICENSE**
   - Apache License 2.0
   - Full license text

2. **NOTICE**
   - Copyright information: `Copyright 2026 Exsol`
   - Attribution: Developed by Kostyantin Zivenko
   - Required by Apache 2.0 license

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

### Theory & Design

**theory/** - Theoretical foundation and design decisions
- Architecture Decision Records (ADRs)
- Research notes
- Design explorations
- Proof-of-concept code

### Core Source Files

**Status:** Structure only - implementation in progress

All source modules currently exist as empty `__init__.py` files. The following structure is planned:

#### Core Module (`src/ai_reviewer/core/`)
- **Planned:** models.py, orchestrator.py, config.py
- **Status:** To be implemented (see CURRENT_TASK)

#### LLM Module (`src/ai_reviewer/llm/`)
- **Planned:** base.py, router.py, provider clients, cost_tracker.py
- **Status:** To be implemented (current focus)

#### Agents Module (`src/ai_reviewer/agents/`)
- **Planned:** base.py, security.py, architecture.py, qa.py
- **Status:** To be implemented (Phase 1)

#### Integrations Module (`src/ai_reviewer/integrations/`)
- **Planned:** base.py, gitlab.py, github.py
- **Status:** To be implemented (Phase 1)

#### Utils Module (`src/ai_reviewer/utils/`)
- **Planned:** git.py, errors.py, logging.py
- **Status:** To be implemented

See `CURRENT_TASK/TASK_DESCRIPTION.md` for active implementation work.

### Configuration Files

1. **pyproject.toml**
   - Python project metadata
   - Dependencies (using PEP 735 dependency groups)
   - LangChain, LangGraph, LLM SDKs
   - Build configuration
   - Tool configuration (ruff, mypy, pytest)

2. **uv.lock**
   - Locked dependency versions
   - Ensures reproducible builds

3. **.env.example**
   - Template for environment variables
   - API keys for all providers
   - Configuration options

4. **config/deployment/\*/README.md**
   - **Status:** Placeholders (coming soon)
   - Quick-start: Free tier setup guidance
   - Small-team: Team deployment guidance
   - Enterprise: Self-hosted setup guidance
   - Real configs will be added as features are implemented

### Development Tools

1. **Makefile**
   - Development shortcuts
   - `make help` - Show all commands
   - `make install` - Install dependencies (PEP 735)
   - `make test` - Run tests
   - `make quick` - Quick quality check

2. **.pre-commit-config.yaml**
   - Pre-commit hooks (ruff, mypy)
   - Runs automatically on `git commit`

### Documentation

1. **mkdocs.yml**
   - MkDocs configuration
   - Navigation structure (minimal for now)
   - Material theme settings

2. **docs/**
   - **index.md** - Landing page
   - **guides/github-actions.md** - GitHub Actions integration guide
   - Additional documentation will be added as features are implemented

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

# Quick quality check
make quick

# Run tests
make test
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
# Pre-commit hooks run automatically
git push origin feature/your-feature
```

### 5. Create PR

```bash
# Use GitHub PR template
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

## Configuration Placeholders

The `config/deployment/` directory currently contains **fictional config.yml files** that will be replaced with honest placeholders:

- **quick-start/config.yml** → Will become README.md explaining free tier setup
- **small-team/config.yml** → Will become README.md explaining team setup
- **enterprise/config.yml** → Will become README.md explaining enterprise setup

**Action needed:** Replace these fictional configs with README.md placeholders (see cleanup update).

Real configurations will be added as features are implemented.

---

## Next Steps

1. **Implement Multi-LLM Router** (Current Task)
2. **Create Security Agent**
3. **Integrate with GitHub**
4. **Write comprehensive tests**
5. **Document all features**

See [PROCESS_PROJECT.md](GENERAL_PROJECT_DESCRIPTION/PROCESS_PROJECT.md) for detailed roadmap.

---

## Questions?

- Read [CONTRIBUTING.md](GENERAL_PROJECT_DESCRIPTION/CONTRIBUTING.md)
- Check [CURRENT_TASK](CURRENT_TASK/)
- Review [Documentation](docs/)

---

**Note:** This project uses Apache License 2.0. See LICENSE and NOTICE files for details.
