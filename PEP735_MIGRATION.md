# 🆕 PEP 735 Migration

**Modern dependency groups for Python**

---

## 📋 What Changed

### Old Way (Deprecated)
```toml
[project.optional-dependencies]
dev = [
    "pytest>=9.0.2",
    "ruff>=0.14.12",
]
```

### New Way (PEP 735)
```toml
[dependency-groups]
dev = [
    "pytest>=9.0.2",
    "ruff>=0.14.12",
]

test = [
    "pytest>=9.0.2",
]

docs = [
    "mkdocs>=1.6.1",
]
```

---

## 🎯 Why PEP 735?

### 1. Modern Standard
- **PEP 735** accepted in 2024
- Replaces `[project.optional-dependencies]`
- Better separation of concerns

### 2. Clearer Semantics
```toml
# OLD: "Optional" is misleading - dev deps aren't optional!
[project.optional-dependencies]
dev = [...]

# NEW: Clear purpose - dependency groups
[dependency-groups]
dev = [...]    # Development dependencies
test = [...]   # Testing only
docs = [...]   # Documentation only
```

### 3. Better Tooling Support
- `uv` natively supports PEP 735
- More granular dependency management
- Faster installation (only install what you need)

### 4. Lockfile Integration
```bash
# uv creates uv.lock with exact versions
uv sync --group dev  # Install from lockfile
```

---

## 🔧 Command Changes

### Installation

**Old:**
```bash
uv pip install -e ".[dev]"
```

**New (PEP 735):**
```bash
uv sync --all-groups  # All groups (dev, test, docs)
uv sync --group dev   # Only dev group
uv sync               # Only production dependencies
```

### Updating Dependencies

**Old:**
```bash
uv pip compile pyproject.toml --upgrade
uv pip install -e ".[dev]"
```

**New:**
```bash
uv lock --upgrade     # Update uv.lock
uv sync --all-groups  # Install updated deps
```

---

## 📊 Dependency Groups Structure

Our project has 3 groups:

```toml
[dependency-groups]
# Complete development environment
dev = [
    "pytest>=9.0.2",        # Testing
    "ruff>=0.14.12",        # Linting
    "mypy>=1.19.1",         # Type checking
    "pre-commit>=4.0.0",    # Git hooks
    "mkdocs>=1.6.1",        # Documentation
    # ... (includes all below)
]

# Testing only
test = [
    "pytest>=9.0.2",
    "pytest-asyncio>=1.3.0",
    "pytest-cov>=7.0.0",
    "pytest-mock>=3.15.1",
]

# Documentation only
docs = [
    "mkdocs>=1.6.1",
    "mkdocs-material>=9.7.1",
    "mkdocstrings[python]>=1.0.1",
]
```

### Use Cases

```bash
# Local development - everything
uv sync --all-groups

# CI testing - only test deps
uv sync --group test

# Build docs - only docs deps
uv sync --group docs

# Production - no dev deps
uv sync
```

---

## 🚀 Makefile Support

Our Makefile handles this automatically:

```bash
make install       # uv sync --all-groups
make install-prod  # uv sync (production only)
make install-dev   # uv sync --group dev
make install-docs  # uv sync --group docs
```

---

## 🔄 Migration Guide

### If You Already Have Project

**Step 1: Update pyproject.toml**
```bash
# Replace updated pyproject.toml
cp updated-files/pyproject.toml .
```

**Step 2: Create lockfile**
```bash
# uv will create uv.lock
uv sync --all-groups
```

**Step 3: Update commands**
```bash
# Old
uv pip install -e ".[dev]"

# New
uv sync --all-groups
```

**Step 4: Commit changes**
```bash
git add pyproject.toml uv.lock
git commit -m "build: migrate to PEP 735 dependency groups"
```

---

## 📚 Benefits

### For Developers

**Faster installation:**
```bash
# Only install what you need
uv sync --group test  # Just testing tools
```

**Clear purpose:**
```bash
# No confusion about "optional" dependencies
[dependency-groups]  # Clear: these are groups
```

**Better reproducibility:**
```bash
# uv.lock ensures exact versions
uv sync  # Always same versions
```

### For CI/CD

**Optimized pipelines:**
```yaml
# GitHub Actions - only install test deps
- run: uv sync --group test
- run: uv run pytest
```

**Faster builds:**
```yaml
# Docs pipeline - only docs deps
- run: uv sync --group docs
- run: uv run mkdocs build
```

---

## 🐛 Troubleshooting

### "uv.lock not found"
```bash
# Create lockfile
uv lock
```

### "Unknown group: dev"
```bash
# Check pyproject.toml has [dependency-groups]
grep "dependency-groups" pyproject.toml
```

### "Old command doesn't work"
```bash
# OLD (still works but deprecated)
uv pip install -e ".[dev]"

# NEW (recommended)
uv sync --all-groups
```

### CI still uses old commands
```bash
# Update GitHub Actions workflows
# Replace: uv pip install -e ".[dev]"
# With: uv sync --all-groups
```

---

## 📖 Learn More

- **PEP 735:** https://peps.python.org/pep-0735/
- **uv docs:** https://docs.astral.sh/uv/
- **Migration guide:** https://docs.astral.sh/uv/concepts/dependencies/

---

## ✅ Quick Reference

| Task | Old Command | New Command (PEP 735) |
|------|-------------|----------------------|
| Install all deps | `uv pip install -e ".[dev]"` | `uv sync --all-groups` |
| Install prod only | `uv pip install -e .` | `uv sync` |
| Install dev group | N/A | `uv sync --group dev` |
| Update deps | `uv pip compile --upgrade` | `uv lock --upgrade && uv sync` |
| Add dependency | `uv pip install package` | `uv add package` |
| Add dev dependency | `uv pip install package` | `uv add --group dev package` |

---

## 🎉 Summary

**What:** PEP 735 introduces `[dependency-groups]`

**Why:** Modern, clearer, better tooling support

**How:**
1. Update `pyproject.toml`
2. Use `uv sync` instead of `uv pip install -e`
3. Enjoy faster, clearer dependency management

**Migration:** Just replace `pyproject.toml` and run `uv sync`

---

**Our project is now using PEP 735!** 🚀
