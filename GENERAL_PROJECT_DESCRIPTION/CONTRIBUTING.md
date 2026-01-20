# Contributing to AI Code Reviewer

Thank you for your interest in contributing to AI Code Reviewer! This guide will help you get started.

---

## 🎯 Project Philosophy

This project is designed for **human-AI pair programming**:
- AI assistants (like Claude) are first-class contributors
- Documentation is optimized for both humans and AI
- Task tracking uses AI-friendly formats
- Development workflow supports AI collaboration

---

## 📋 Before You Start

1. **Read the project docs:**
   - `GENERAL_PROJECT_DESCRIPTION/PROJECT_CANVAS.md` - Vision and roadmap
   - `GENERAL_PROJECT_DESCRIPTION/PROCESS_PROJECT.md` - Current progress
   - `CURRENT_TASK/` - Active work items

2. **Check existing issues:**
   - [GitHub Issues](https://github.com/KonstZiv/ai-code-reviewer/issues)
   - Comment on issues you'd like to work on

3. **Join discussions:**
   - [GitHub Discussions](https://github.com/KonstZiv/ai-code-reviewer/discussions)

---

## 🚀 Development Setup

```bash
# Clone repository
git clone https://github.com/KonstZiv/ai-code-reviewer.git
cd ai-code-reviewer

# Create virtual environment
uv venv
source .venv/bin/activate  # Linux/Mac

# Install dependencies (PEP 735)
uv sync --all-groups

# Setup pre-commit hooks
uv run pre-commit install

# Verify setup
make quick
```

---

## 📝 Code Style

### Python Code

We use **ruff** for linting and formatting, **mypy** for type checking:

```bash
# Format code
uv run ruff format .

# Check linting
uv run ruff check .

# Type checking
uv run mypy src/

# Or all at once
make quick
```

### Code Standards

- **Type hints:** Required for all functions
- **Docstrings:** Google style for public APIs
- **Line length:** 100 characters
- **Import order:** Handled by ruff (isort)
- **Naming:**
  - Classes: `PascalCase`
  - Functions/variables: `snake_case`
  - Constants: `UPPER_CASE`
  - Private: Prefix with `_`

### Example

```python
from typing import List

def analyze_code(code: str, language: str = "python") -> List[Finding]:
    """Analyze code for issues.

    Args:
        code: Source code to analyze
        language: Programming language (default: python)

    Returns:
        List of findings

    Raises:
        ValueError: If code is empty
    """
    if not code:
        raise ValueError("Code cannot be empty")

    # Implementation
    return []
```

---

## 🧪 Testing

### Writing Tests

- **Unit tests:** `tests/unit/`
- **Integration tests:** `tests/integration/`
- **E2E tests:** `tests/e2e/`

```python
# tests/unit/test_analyzer.py
import pytest
from ai_reviewer.core.analyzer import CodeAnalyzer

def test_analyze_empty_code():
    """Test that empty code raises ValueError."""
    analyzer = CodeAnalyzer()

    with pytest.raises(ValueError, match="Code cannot be empty"):
        analyzer.analyze("")

@pytest.mark.asyncio
async def test_analyze_async():
    """Test async code analysis."""
    analyzer = CodeAnalyzer()
    result = await analyzer.analyze_async("print('hello')")

    assert result is not None
```

### Running Tests

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=ai_reviewer

# Specific file
uv run pytest tests/unit/test_analyzer.py -v

# Using Makefile
make test
```

### Coverage Requirements

- **Minimum coverage:** 80%
- **New code:** Should have >90% coverage
- Coverage report: `htmlcov/index.html`

---

## 🔄 Git Workflow

### Branch Naming

```
feature/<feature-name>   # New features
fix/<bug-description>    # Bug fixes
docs/<doc-update>        # Documentation
refactor/<what>          # Code refactoring
test/<test-name>         # Test improvements
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

<optional body>

<optional footer>
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `style` - Formatting (no code change)
- `refactor` - Code restructuring
- `test` - Adding tests
- `chore` - Maintenance

**Examples:**
```bash
feat(llm): add DeepSeek provider support
fix(security): resolve XSS vulnerability in output
docs(readme): update installation instructions
refactor(core): simplify analyzer interface
test(llm): add unit tests for router
```

### Workflow

1. **Create branch:**
   ```bash
   git checkout -b feature/multi-llm-router
   ```

2. **Make changes:**
   ```bash
   # Edit files
   vim src/ai_reviewer/llm/router.py

   # Check quality (pre-commit runs automatically on commit)
   make quick

   # Run tests
   make test
   ```

3. **Commit:**
   ```bash
   git add .
   git commit -m "feat(llm): implement multi-LLM router"
   ```

4. **Push:**
   ```bash
   git push -u origin feature/multi-llm-router
   ```

5. **Create PR:**
   ```bash
   gh pr create --title "feat(llm): Multi-LLM Router" \
     --body "Implements base router for multiple LLM providers"
   ```

---

## 🤖 AI-Friendly Development

### Task Documentation

When working on a task:

1. **Read task description:**
   ```bash
   cat CURRENT_TASK/TASK_DESCRIPTION.md
   ```

2. **Update progress:**
   ```bash
   # Edit CURRENT_TASK/PROCESS_TASK.md
   # Add completed steps, blockers, etc.
   ```

3. **Document decisions:**
   ```bash
   # Update GENERAL_PROJECT_DESCRIPTION/PROCESS_PROJECT.md
   # Add to decision log
   ```

### For AI Assistants

If you're an AI assistant helping with development:

1. **Always read project docs first:**
   - `GENERAL_PROJECT_DESCRIPTION/PROJECT_CANVAS.md`
   - `CURRENT_TASK/TASK_DESCRIPTION.md`

2. **Update task progress:**
   - Modify `CURRENT_TASK/PROCESS_TASK.md` as you work

3. **Follow code standards:**
   - Run `make quick` before suggesting changes
   - Include type hints
   - Write tests

4. **Provide context:**
   - Explain architectural decisions
   - Link to relevant documentation
   - Suggest improvements

---

## 📚 Documentation

### Code Documentation

- **Public APIs:** Google-style docstrings
- **Internal functions:** Brief docstring
- **Complex logic:** Inline comments

### Project Documentation

- **README.md** - Overview and quick start
- **docs/** - MkDocs documentation
- **GENERAL_PROJECT_DESCRIPTION/** - Project-level docs
- **CURRENT_TASK/** - Active work documentation

### Building Docs

```bash
# Serve locally
uv run mkdocs serve

# Or with Makefile
make docs

# Build for deployment
uv run mkdocs build
```

---

## 🔍 Code Review

### For Reviewers

- Check code style (ruff, mypy should pass)
- Verify tests exist and pass
- Review documentation updates
- Check CURRENT_TASK progress updates
- Ensure commit messages follow conventions

### PR Checklist

- [ ] Code follows style guide
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] `CURRENT_TASK/PROCESS_TASK.md` updated
- [ ] Commit messages follow conventions
- [ ] All CI checks pass
- [ ] No merge conflicts

---

## 🐛 Reporting Issues

### Bug Reports

Include:
- **Description:** What's broken?
- **Steps to reproduce:** How to trigger the bug?
- **Expected behavior:** What should happen?
- **Actual behavior:** What actually happens?
- **Environment:** OS, Python version, dependencies
- **Logs:** Error messages, stack traces

### Feature Requests

Include:
- **Problem:** What problem does this solve?
- **Solution:** What would you like to see?
- **Alternatives:** Other approaches considered?
- **Impact:** Who benefits from this?

---

## 🙏 Recognition

Contributors are recognized in:
- GitHub contributors graph
- Release notes (for significant contributions)
- Project documentation

---

## 📜 License

This project is licensed under the Apache License 2.0. By contributing, you agree that your contributions will be licensed under the same license.

See the [LICENSE](../LICENSE) file for details.

---

## 💬 Questions?

- **Issues:** [GitHub Issues](https://github.com/KonstZiv/ai-code-reviewer/issues)
- **Discussions:** [GitHub Discussions](https://github.com/KonstZiv/ai-code-reviewer/discussions)
- **Email:** kos.zivenko@gmail.com

---

**Thank you for contributing to AI Code Reviewer!** 🎉
