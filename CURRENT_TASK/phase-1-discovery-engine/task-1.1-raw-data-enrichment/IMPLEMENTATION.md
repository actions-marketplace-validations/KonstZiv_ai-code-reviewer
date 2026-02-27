# Implementation: Raw Data Enrichment

## Файли для зміни

```
ai-code-reviewer/
├── discovery/
│   ├── models.py          # + RawProjectData model
│   ├── orchestrator.py    # fix _build_profile_deterministic → _collect_raw_data
│   └── parsers.py         # NEW: dependency/config file parsers
└── tests/
    └── discovery/
        ├── test_parsers.py        # NEW
        └── test_orchestrator.py   # update
```

## Крок 1: RawProjectData model (`models.py`)

```python
class RawProjectData(BaseModel):
    """All data collected deterministically (0 LLM tokens).

    This is the input for LLM analysis (task 1.2).
    Contains raw strings — LLM interprets them.
    """

    languages: dict[str, float] = Field(
        default_factory=dict,
        description="Language → percentage from Platform API",
    )
    file_tree: list[str] = Field(
        default_factory=list,
        description="Flattened file paths",
    )
    file_tree_truncated: bool = Field(
        default=False,
        description="True if tree was cut at FILE_TREE_LIMIT",
    )
    ci_files: dict[str, str] = Field(
        default_factory=dict,
        description="Path → content of CI config files",
    )
    dependency_files: dict[str, str] = Field(
        default_factory=dict,
        description="Path → content (pyproject.toml, package.json, go.mod, etc.)",
    )
    config_files: dict[str, str] = Field(
        default_factory=dict,
        description="Path → content (ruff.toml, .eslintrc, tsconfig.json, etc.)",
    )
    detected_package_managers: list[str] = Field(
        default_factory=list,
        description="Deterministically detected: uv, pip, npm, yarn, pnpm, go modules",
    )
    layout: str | None = Field(
        default=None,
        description="src | flat | monorepo — from file tree heuristic",
    )
    reviewbot_config: str | None = Field(
        default=None,
        description="Content of .reviewbot.md if exists",
    )
```

## Крок 2: Parsers (`parsers.py`)

```python
"""Deterministic parsers for project files.

Не інтерпретують — тільки структурують.
Інтерпретація — задача LLM (task 1.2).
"""

import logging
from pathlib import PurePath

logger = logging.getLogger(__name__)

# Files that indicate dependency management
DEPENDENCY_FILES = {
    "pyproject.toml", "setup.py", "setup.cfg", "requirements.txt",
    "Pipfile", "poetry.lock",
    "package.json", "yarn.lock", "pnpm-lock.yaml",
    "go.mod", "go.sum",
    "Cargo.toml", "Cargo.lock",
    "Gemfile", "Gemfile.lock",
    "composer.json",
}

# Files that indicate code quality / linting config
CONFIG_FILES = {
    "ruff.toml", ".ruff.toml", "pyproject.toml",  # ruff section
    ".flake8", ".pylintrc", ".mypy.ini", "mypy.ini",
    ".eslintrc", ".eslintrc.json", ".eslintrc.js", ".eslintrc.yml",
    "tsconfig.json", ".prettierrc", ".prettierrc.json",
    "biome.json", ".editorconfig",
    "golangci-lint.yml", ".golangci.yml",
    "rustfmt.toml", "clippy.toml",
}

# Package manager detection from file presence
PACKAGE_MANAGER_INDICATORS = {
    "uv.lock": "uv",
    "poetry.lock": "poetry",
    "Pipfile.lock": "pipenv",
    "yarn.lock": "yarn",
    "pnpm-lock.yaml": "pnpm",
    "package-lock.json": "npm",
    "go.sum": "go modules",
    "Cargo.lock": "cargo",
}

FILE_TREE_LIMIT = 500


def classify_collected_files(
    collected_configs: dict[str, str],
    file_tree: list[str],
) -> tuple[dict[str, str], dict[str, str]]:
    """Split collected configs into dependency files and config files."""
    dep_files: dict[str, str] = {}
    cfg_files: dict[str, str] = {}

    for path, content in collected_configs.items():
        name = PurePath(path).name
        if name in DEPENDENCY_FILES:
            dep_files[path] = content
        if name in CONFIG_FILES:
            cfg_files[path] = content
        # Note: pyproject.toml goes to BOTH — it has deps AND config

    return dep_files, cfg_files


def detect_package_managers(file_tree: list[str]) -> list[str]:
    """Detect package managers from lock files in tree."""
    managers = []
    tree_names = {PurePath(p).name for p in file_tree}

    for indicator, manager in PACKAGE_MANAGER_INDICATORS.items():
        if indicator in tree_names:
            managers.append(manager)

    # Fallback: requirements.txt without lock → pip
    if not managers and "requirements.txt" in tree_names:
        managers.append("pip")

    return sorted(set(managers))


def detect_layout(file_tree: list[str]) -> str | None:
    """Detect project layout from file tree structure."""
    if not file_tree:
        return None

    has_src = any(p.startswith("src/") for p in file_tree)

    # Monorepo heuristic: multiple dirs with their own package files
    top_dirs_with_packages = set()
    for path in file_tree:
        parts = PurePath(path).parts
        if len(parts) >= 2 and parts[1] in DEPENDENCY_FILES:
            top_dirs_with_packages.add(parts[0])

    if len(top_dirs_with_packages) >= 2:
        return "monorepo"
    elif has_src:
        return "src"
    else:
        return "flat"


def check_file_tree_truncation(file_tree: list[str]) -> bool:
    """Check if file tree exceeds limit."""
    return len(file_tree) >= FILE_TREE_LIMIT
```

## Крок 3: Інтеграція в orchestrator

```python
# В DiscoveryOrchestrator._collect_raw_data() (renamed from _build_profile_deterministic)

from .parsers import (
    classify_collected_files,
    detect_package_managers,
    detect_layout,
    check_file_tree_truncation,
)

def _collect_raw_data(
    self,
    platform_data: PlatformData,
    ci_insights: CIInsights | None,
    collected_configs: dict[str, str],
) -> RawProjectData:
    """Collect all deterministic data (0 LLM tokens)."""

    dep_files, cfg_files = classify_collected_files(
        collected_configs, platform_data.file_tree
    )

    ci_files = {}
    if ci_insights and ci_insights.raw_files:
        ci_files = ci_insights.raw_files

    return RawProjectData(
        languages=platform_data.languages,
        file_tree=platform_data.file_tree,
        file_tree_truncated=check_file_tree_truncation(platform_data.file_tree),
        ci_files=ci_files,
        dependency_files=dep_files,
        config_files=cfg_files,
        detected_package_managers=detect_package_managers(platform_data.file_tree),
        layout=detect_layout(platform_data.file_tree),
        reviewbot_config=collected_configs.get(".reviewbot.md"),
    )
```

## Тести

```python
# tests/discovery/test_parsers.py

def test_classify_pyproject_goes_to_both():
    configs = {"pyproject.toml": "[project]\nname='test'"}
    deps, cfgs = classify_collected_files(configs, [])
    assert "pyproject.toml" in deps
    assert "pyproject.toml" in cfgs


def test_detect_uv_from_lock():
    tree = ["src/main.py", "pyproject.toml", "uv.lock"]
    assert detect_package_managers(tree) == ["uv"]


def test_detect_go_modules():
    tree = ["main.go", "go.mod", "go.sum", "internal/"]
    assert detect_package_managers(tree) == ["go modules"]


def test_layout_src():
    tree = ["src/app/__init__.py", "src/app/main.py", "tests/"]
    assert detect_layout(tree) == "src"


def test_layout_monorepo():
    tree = ["frontend/package.json", "backend/pyproject.toml", "shared/"]
    assert detect_layout(tree) == "monorepo"


def test_file_tree_truncation():
    tree = [f"file_{i}.py" for i in range(600)]
    assert check_file_tree_truncation(tree) is True
```

## Ризики

- **Malformed configs** → try/except, log warning, skip. НЕ ламає pipeline.
- **Великий pyproject.toml** → передаємо as-is, LLM розбереться (task 1.2).
