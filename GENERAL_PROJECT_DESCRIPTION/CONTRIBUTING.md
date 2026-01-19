# Contributing Guidelines

Welcome to AI Code Reviewer! This document explains how humans and AI agents should collaborate on this project.

---

## 🤖 AI-First Development

This project is designed for **human-AI pair programming**. All processes are optimized for both human and AI understanding.

### For AI Agents

When starting a new session:
1. Read `GENERAL_PROJECT_DESCRIPTION/PROJECT_CANVAS.md` — understand the vision
2. Read `GENERAL_PROJECT_DESCRIPTION/PROCESS_PROJECT.md` — understand current state
3. Read `CURRENT_TASK/TASK_DESCRIPTION.md` — understand active work
4. Read `CURRENT_TASK/PROCESS_TASK.md` — understand task progress

### State Files

These files persist knowledge between sessions:

| File | Purpose | Update Frequency |
|------|---------|------------------|
| `PROJECT_CANVAS.md` | Vision, roadmap | When strategy changes |
| `PROCESS_PROJECT.md` | Implementation plan | Daily during active development |
| `TASK_DESCRIPTION.md` | Current task spec | At task start |
| `PROCESS_TASK.md` | Task progress | After each significant step |

---

## 📝 Task Management

### Task Structure

Every task MUST have:
1. **TASK_DESCRIPTION.md** in `CURRENT_TASK/`
2. **PROCESS_TASK.md** tracking progress
3. Clear acceptance criteria
4. Definition of "done"

### Task Description Format

```markdown
# Task: [Short Title]

**Created:** YYYY-MM-DD  
**Assignee:** [Name or "AI Agent"]  
**Estimated:** [Hours/Days]  
**Status:** [Not Started | In Progress | Blocked | Done]

## 🎯 Goal
[1-2 sentences: what we want to achieve]

## 📋 Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## 🔧 Technical Approach
[How we plan to implement this]

## 🧪 Testing Strategy
[How we will verify it works]

## 📦 Dependencies
- Depends on: [Other tasks]
- Blocks: [Other tasks]

## 📝 Notes
[Any additional context]
```

### Task Process Format

```markdown
# Task Process: [Task Name]

## ⏱️ Timeline
- Started: YYYY-MM-DD HH:MM
- Last Updated: YYYY-MM-DD HH:MM
- Estimated Completion: YYYY-MM-DD

## 📊 Progress: XX%

## ✅ Completed Steps
1. [Step description] — [Date]
2. [Step description] — [Date]

## 🔄 Current Step
[What we're working on right now]

## ⏭️ Next Steps
1. [Next action]
2. [Then this]

## 🚧 Blockers
- [Issue 1] — [How to resolve]

## 💡 Decisions Made
- [Date]: [Decision] — [Rationale]

## 📝 Session Notes
### [Date] — [Author]
[What was done, what was learned, next steps]
```

---

## 🔀 Git Workflow

### Branch Naming

```
type/short-description

Types:
- feature/  — New functionality
- fix/      — Bug fixes
- docs/     — Documentation only
- refactor/ — Code refactoring
- test/     — Adding tests
- chore/    — Dependencies, config, etc.

Examples:
- feature/multi-llm-router
- fix/gitlab-webhook-parsing
- docs/quick-start-tutorial
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): short description

[optional body]

[optional footer]

Types:
- feat:     New feature
- fix:      Bug fix
- docs:     Documentation
- style:    Formatting (no code change)
- refactor: Code restructuring
- test:     Adding tests
- chore:    Maintenance

Examples:
feat(llm): add DeepSeek provider support
fix(gitlab): handle empty MR descriptions
docs(deployment): add quick-start tutorial
test(agents): add security agent unit tests
```

### Pull Request / Merge Request Format

```markdown
## 🎯 What
[Brief description of changes]

## 🤔 Why
[Why these changes are needed]

## 🔧 How
[Technical approach]

## ✅ Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing done
- [ ] Documentation updated

## 📸 Screenshots (if UI changes)
[Images]

## 🔗 Related
- Issue: #123
- Task: CURRENT_TASK/task-name
- Docs: [Link]

## ♻️ Checklist
- [ ] Code follows style guide
- [ ] Tests added/updated
- [ ] Docs updated
- [ ] PROCESS_PROJECT.md updated (if needed)
- [ ] No secrets in code
```

---

## 💻 Code Style

### Python

**Formatter:** `ruff format`  
**Linter:** `ruff check`  
**Type checker:** `mypy`

```python
# Good: Type hints everywhere
async def analyze_code(
    context: ReviewContext,
    config: AnalysisConfig
) -> AgentReport:
    """Analyze code for issues.
    
    Args:
        context: Review context with code and metadata
        config: Analysis configuration
        
    Returns:
        Report with findings
        
    Raises:
        AnalysisError: If analysis fails
    """
    pass

# Good: Pydantic models for data
class Finding(BaseModel):
    """Code review finding."""
    
    severity: Severity
    title: str
    description: str
    line: int
    
    model_config = ConfigDict(frozen=True)

# Bad: No types
def analyze(ctx, cfg):
    pass

# Bad: Mutable default arguments
def foo(items=[]):  # ❌
    pass

def foo(items: list[str] | None = None):  # ✅
    items = items or []
```

### File Organization

```python
# Standard order:
# 1. Docstring
# 2. Imports (stdlib, third-party, local)
# 3. Constants
# 4. Type aliases
# 5. Classes
# 6. Functions

"""Module for LLM routing."""

import os
from typing import Protocol

from langchain.chat_models import BaseChatModel
from pydantic import BaseModel

from ai_reviewer.core.models import Task

# Constants
DEFAULT_TEMPERATURE = 0.0

# Type aliases
LLMProvider = str

# Classes
class LLMRouter:
    """Routes tasks to appropriate LLM."""
    pass
```

### Error Handling

```python
# Good: Specific exceptions
class ReviewError(Exception):
    """Base exception for review errors."""

class ContextBuildError(ReviewError):
    """Failed to build context."""

class AgentError(ReviewError):
    """Agent execution failed."""

# Good: Try-catch with recovery
async def build_context(event: ParsedEvent) -> ContextPackage:
    """Build context with fallback."""
    try:
        return await _build_full_context(event)
    except APIError as e:
        logger.warning("API failed, using minimal context", error=e)
        return _build_minimal_context(event)
    except Exception as e:
        logger.error("Unexpected error", error=e)
        raise ContextBuildError("Failed to build context") from e

# Bad: Bare except
try:
    do_something()
except:  # ❌
    pass
```

---

## 📚 Documentation

### Docstrings

Use Google style:

```python
def calculate_risk_score(findings: list[Finding]) -> float:
    """Calculate overall risk score from findings.
    
    The risk score is weighted by severity:
    - CRITICAL: 0.4 per finding
    - ERROR: 0.2 per finding
    - WARNING: 0.1 per finding
    
    Args:
        findings: List of review findings
        
    Returns:
        Risk score between 0.0 and 1.0
        
    Examples:
        >>> findings = [Finding(severity=Severity.CRITICAL, ...)]
        >>> calculate_risk_score(findings)
        0.4
    """
    pass
```

### MkDocs Structure

```
docs/
├── index.md                 # Landing page
├── getting-started/
│   ├── quick-start.md      # 1-minute setup
│   ├── installation.md     # Detailed install
│   └── first-review.md     # First review tutorial
├── deployment/
│   ├── solo-dev.md         # Solo developer (free)
│   ├── small-team.md       # Small team ($10-30/mo)
│   └── enterprise.md       # Enterprise (self-hosted)
├── guides/
│   ├── gitlab-ci.md        # GitLab integration
│   ├── github-actions.md   # GitHub integration
│   ├── configuration.md    # Config reference
│   └── agents.md           # Understanding agents
├── development/
│   ├── architecture.md     # System design
│   ├── adding-agents.md    # Create new agents
│   ├── adding-providers.md # Add LLM providers
│   └── testing.md          # Testing guide
└── api/
    └── reference.md        # API documentation
```

---

## 🧪 Testing

### Test Organization

```
tests/
├── unit/                   # Fast, isolated tests
│   ├── test_models.py
│   ├── test_agents.py
│   └── test_llm_router.py
├── integration/            # Tests with external services
│   ├── test_gitlab_api.py
│   └── test_llm_providers.py
└── e2e/                    # Full workflow tests
    └── test_review_flow.py
```

### Test Requirements

- Unit tests for all business logic
- Integration tests for external APIs (mocked in CI)
- E2E test for main happy path
- Minimum 80% coverage

### Test Naming

```python
# Pattern: test_<what>_<condition>_<expected>

def test_router_simple_task_uses_local_llm():
    """Router should use local LLM for simple tasks."""
    pass

def test_security_agent_finds_hardcoded_secret():
    """Security agent detects hardcoded API keys."""
    pass

def test_context_build_api_error_falls_back():
    """Context builder falls back to minimal on API error."""
    pass
```

---

## 🚀 Development Workflow

### Setting Up

```bash
# Clone
git clone https://github.com/your-org/ai-code-reviewer.git
cd ai-code-reviewer

# Install
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Configure
cp .env.example .env
# Edit .env with your API keys

# Verify
pytest
ruff check .
mypy .
```

### Making Changes

1. **Create task description**
   ```bash
   # Update CURRENT_TASK/TASK_DESCRIPTION.md
   ```

2. **Create branch**
   ```bash
   git checkout -b feature/your-feature
   ```

3. **Develop with AI**
   - AI reads task description
   - Implement in small steps
   - Update PROCESS_TASK.md after each step

4. **Test**
   ```bash
   pytest
   ruff check .
   mypy .
   ```

5. **Document**
   - Update relevant docs
   - Add docstrings
   - Update PROCESS_PROJECT.md if needed

6. **Commit**
   ```bash
   git add .
   git commit -m "feat(scope): description"
   ```

7. **Push and create PR**
   ```bash
   git push origin feature/your-feature
   # Create PR with proper template
   ```

---

## 🎨 Design Principles for Contributors

### 1. Fail Gracefully
Always have a fallback:
```python
# ✅ Good
try:
    return expensive_operation()
except:
    logger.warning("Falling back to cheaper alternative")
    return cheap_alternative()

# ❌ Bad
return expensive_operation()  # Crashes if fails
```

### 2. Log Everything Important
```python
# ✅ Good
logger.info("Starting review", mr_id=mr_id, depth=config.depth)
try:
    result = review()
    logger.info("Review completed", findings=len(result.findings))
except Exception as e:
    logger.error("Review failed", error=e, mr_id=mr_id)

# ❌ Bad
result = review()  # Silent failures
```

### 3. Make It Configurable
```python
# ✅ Good - configurable
class SecurityAgent:
    def __init__(self, config: SecurityConfig):
        self.patterns = config.secret_patterns
        self.enabled_checks = config.enabled_checks

# ❌ Bad - hardcoded
class SecurityAgent:
    PATTERNS = [...]  # Can't customize
```

### 4. Document for AI
```python
# ✅ Good - clear for AI
class ReviewContext:
    """Main context object for review cycle.
    
    This object is passed through the entire review pipeline.
    Each stage adds data to it. If a stage fails, the context
    contains error records for debugging.
    
    Lifecycle:
        1. Created in parse_event()
        2. Context added in build_context()
        3. Findings added by agents
        4. Decision added in synthesize()
    """
    pass

# ❌ Bad - unclear
class ReviewContext:
    """Context."""  # What? When? How?
    pass
```

---

## ❓ Questions?

- Read existing code and docs
- Check `PROCESS_PROJECT.md` for decisions
- Ask in discussions
- For AI: analyze similar patterns in codebase

---

## 📜 License

This project is MIT licensed. By contributing, you agree to license your contributions under MIT.

---

**Remember:** We're building for both humans and AI. Clear structure and documentation helps everyone! 🤝
