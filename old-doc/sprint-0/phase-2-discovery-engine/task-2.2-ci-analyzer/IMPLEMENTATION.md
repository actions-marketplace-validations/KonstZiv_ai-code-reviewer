# Task 2.2: CIPipelineAnalyzer — Implementation Guide

## Архітектура

```python
class CIPipelineAnalyzer:
    """Детерміністичний парсер CI файлів."""

    def analyze(self, yaml_content: str, ci_file_path: str = "") -> CIInsights:
        """Парсить YAML → CIInsights."""
        data = yaml.safe_load(yaml_content)
        commands = self._extract_commands(data)

        return CIInsights(
            ci_file_path=ci_file_path,
            raw_yaml=yaml_content,
            detected_tools=tuple(self._detect_tools(commands)),
            python_version=self._detect_version(commands, data, "python"),
            node_version=self._detect_version(commands, data, "node"),
            go_version=self._detect_version(commands, data, "go"),
            package_manager=self._detect_package_manager(commands),
            services=tuple(self._detect_services(data)),
            deployment_targets=tuple(self._detect_deployments(commands, data)),
            min_coverage=self._detect_coverage_threshold(commands),
        )

    def analyze_makefile(self, content: str) -> CIInsights:
        """Makefile як proxy CI."""
```

## TOOL_PATTERNS

```python
TOOL_PATTERNS: dict[str, tuple[str, ToolCategory]] = {
    # Python
    r"\bruff\b(?:\s+check)?": ("ruff", ToolCategory.LINTING),
    r"\bruff\b\s+format": ("ruff format", ToolCategory.FORMATTING),
    r"\bflake8\b": ("flake8", ToolCategory.LINTING),
    r"\bpylint\b": ("pylint", ToolCategory.LINTING),
    r"\bblack\b": ("black", ToolCategory.FORMATTING),
    r"\bisort\b": ("isort", ToolCategory.FORMATTING),
    r"\bmypy\b": ("mypy", ToolCategory.TYPE_CHECKING),
    r"\bpyright\b": ("pyright", ToolCategory.TYPE_CHECKING),
    r"\bpytest\b": ("pytest", ToolCategory.TESTING),
    r"\bbandit\b": ("bandit", ToolCategory.SECURITY),
    r"\bsafety\b(?:\s+check)?": ("safety", ToolCategory.SECURITY),
    r"\bpre-commit\b": ("pre-commit", ToolCategory.META),

    # JavaScript / TypeScript
    r"\beslint\b": ("eslint", ToolCategory.LINTING),
    r"\bbiome\b": ("biome", ToolCategory.LINTING),
    r"\bprettier\b": ("prettier", ToolCategory.FORMATTING),
    r"\btsc\b": ("tsc", ToolCategory.TYPE_CHECKING),
    r"\bjest\b": ("jest", ToolCategory.TESTING),
    r"\bvitest\b": ("vitest", ToolCategory.TESTING),
    r"\bmocha\b": ("mocha", ToolCategory.TESTING),
    r"\bnpm\s+audit\b": ("npm audit", ToolCategory.SECURITY),

    # Go
    r"\bgo\s+vet\b": ("go vet", ToolCategory.LINTING),
    r"\bgolangci-lint\b": ("golangci-lint", ToolCategory.LINTING),
    r"\bgo\s+test\b": ("go test", ToolCategory.TESTING),
    r"\bgofmt\b": ("gofmt", ToolCategory.FORMATTING),

    # Rust
    r"\bcargo\s+clippy\b": ("cargo clippy", ToolCategory.LINTING),
    r"\bcargo\s+fmt\b": ("cargo fmt", ToolCategory.FORMATTING),
    r"\bcargo\s+test\b": ("cargo test", ToolCategory.TESTING),
}
```

## _extract_commands()

Рекурсивний walker по YAML. Шукає значення в ключах:
`run`, `script`, `before_script`, `after_script`, `command`, `commands`,
`steps[].run`, `jobs.*.steps[].run`.

Повертає `list[str]` — всі команди як рядки.

## VERSION_PATTERNS

```python
# В commands
r"python-version:\s*['"]?(\d+\.\d+)": "python",
r"node-version:\s*['"]?(\d+)": "node",
r"go-version:\s*['"]?(\d+\.\d+)": "go",

# В YAML structure
# GitHub Actions: jobs.*.strategy.matrix.python-version
# GitLab CI: image: python:3.13
```

## PKG_MANAGER_PATTERNS

```python
r"\buv\b(?:\s+(?:sync|run|pip))": "uv",
r"\bpoetry\b(?:\s+(?:install|run))": "poetry",
r"\bpip\b\s+install": "pip",
r"\bnpm\b\s+(?:ci|install)": "npm",
r"\byarn\b(?:\s+install)?": "yarn",
r"\bpnpm\b": "pnpm",
r"\bcargo\b(?:\s+build)": "cargo",
```

## Тест fixtures

Створити у `tests/fixtures/ci/`:

1. `github_actions_python_modern.yml` — ruff, mypy, pytest, uv, Python 3.13
2. `github_actions_python_legacy.yml` — flake8, tox, pip, Python 3.9
3. `github_actions_js.yml` — eslint, jest, npm, Node 20
4. `gitlab_ci_go.yml` — golangci-lint, go test, Go 1.22
5. `makefile_only.txt` — lint, test, format targets

---

## Чеклист

- [ ] `ci_analyzer.py` — CIPipelineAnalyzer з analyze() + analyze_makefile()
- [ ] TOOL_PATTERNS: ≥20 tools across 4 languages
- [ ] VERSION_PATTERNS: Python, Node, Go
- [ ] PKG_MANAGER_PATTERNS: ≥6 managers
- [ ] COVERAGE_PATTERNS: --cov-fail-under, threshold
- [ ] 5+ test fixtures
- [ ] `make check` проходить
