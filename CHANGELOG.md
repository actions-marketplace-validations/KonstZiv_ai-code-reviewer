# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure
- Multi-LLM router architecture (Anthropic, OpenAI, Google, DeepSeek, Ollama)
- 3 deployment scenarios (quick-start, small-team, enterprise)
- AI-friendly documentation system (GENERAL_PROJECT_DESCRIPTION, CURRENT_TASK)
- MkDocs documentation framework
- GitHub Actions workflows (tests, docs, release)
- Pre-commit hooks (ruff, mypy)
- PyPI publishing automation

### Infrastructure
- Python 3.13+ requirement
- uv package manager
- Ruff for linting and formatting
- MyPy for type checking
- Pytest with coverage tracking
- GitHub Pages for documentation

## [0.1.0] - TBD

### Added
- Multi-LLM Router implementation
- Security Agent (first agent)
- GitHub integration
- GitLab integration
- Basic CLI interface
- Configuration management

---

## Release Process

### Version Numbers

We use [Semantic Versioning](https://semver.org/):
- **MAJOR** version: Incompatible API changes
- **MINOR** version: New functionality (backwards-compatible)
- **PATCH** version: Bug fixes (backwards-compatible)

### Creating a Release

1. **Update version in pyproject.toml:**
   ```toml
   version = "0.2.0"
   ```

2. **Update CHANGELOG.md:**
   ```markdown
   ## [0.2.0] - 2026-01-XX

   ### Added
   - New feature

   ### Changed
   - Modified behavior

   ### Fixed
   - Bug fix
   ```

3. **Commit changes:**
   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "chore: bump version to 0.2.0"
   git push origin main
   ```

4. **Create and push tag:**
   ```bash
   git tag -a v0.2.0 -m "Release v0.2.0"
   git push origin v0.2.0
   ```

5. **GitHub Actions will automatically:**
   - Run all tests
   - Build package
   - Publish to PyPI
   - Create GitHub Release
   - Deploy documentation

---

## Version History Template

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- New features

### Changed
- Changes in existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Now removed features

### Fixed
- Bug fixes

### Security
- Security improvements
```
