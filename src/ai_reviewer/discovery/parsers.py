"""Deterministic parsers for project files.

Classify collected configs into categories, detect package managers and
project layout from the file tree.  These parsers do NOT interpret
file contents — interpretation is delegated to LLM (task 1.2).
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

# ── File classification sets ─────────────────────────────────────────

DEPENDENCY_FILES: frozenset[str] = frozenset(
    {
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "requirements.txt",
        "Pipfile",
        "poetry.lock",
        "package.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "go.mod",
        "go.sum",
        "Cargo.toml",
        "Cargo.lock",
        "Gemfile",
        "Gemfile.lock",
        "composer.json",
    }
)

CONFIG_FILES: frozenset[str] = frozenset(
    {
        "ruff.toml",
        ".ruff.toml",
        "pyproject.toml",
        ".flake8",
        ".pylintrc",
        ".mypy.ini",
        "mypy.ini",
        ".eslintrc",
        ".eslintrc.json",
        ".eslintrc.js",
        ".eslintrc.yml",
        "eslint.config.js",
        "eslint.config.mjs",
        "tsconfig.json",
        ".prettierrc",
        ".prettierrc.json",
        "biome.json",
        ".editorconfig",
        ".golangci.yml",
        ".golangci.yaml",
        "rustfmt.toml",
        "clippy.toml",
        ".clippy.toml",
    }
)

CI_FILE_NAMES: frozenset[str] = frozenset(
    {
        ".gitlab-ci.yml",
        "Makefile",
        "Jenkinsfile",
        "Taskfile.yml",
    }
)

CI_FILE_PREFIXES: tuple[str, ...] = (
    ".github/workflows/",
    ".circleci/",
)

PACKAGE_MANAGER_INDICATORS: dict[str, str] = {
    "uv.lock": "uv",
    "poetry.lock": "poetry",
    "Pipfile.lock": "pipenv",
    "yarn.lock": "yarn",
    "pnpm-lock.yaml": "pnpm",
    "package-lock.json": "npm",
    "go.mod": "go modules",
    "Cargo.lock": "cargo",
    "Gemfile.lock": "bundler",
}

_SOURCE_EXTENSIONS: tuple[str, ...] = (".py", ".js", ".ts", ".go", ".rs", ".java", ".kt")

FILE_TREE_LIMIT: int = 500
_MIN_DIRS_FOR_MONOREPO: int = 2
_MIN_PARTS_FOR_SUBDIR: int = 2
_REDACTED: str = "***"

# Patterns that look like secret values (API keys, tokens, passwords).
# Each pattern replaces the VALUE portion, preserving the key name.
_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    # KEY=value or KEY: value in env blocks (common in CI YAML)
    # Matches: API_KEY: sk-abc123, TOKEN=ghp_xxxx, PASSWORD: "secret"
    # Skips template refs: ${{ secrets.X }}, ${VAR}, $VAR
    re.compile(
        r"(?P<key>[A-Z][A-Z0-9_]*(?:_KEY|_TOKEN|_SECRET|_PASSWORD|_CREDENTIAL|_AUTH))"
        r"(?P<sep>\s*[:=]\s*)"
        r"(?P<val>['\"]?(?!\$\{)[^\s'\"#\n]+['\"]?)",
        re.IGNORECASE,
    ),
    # password/secret/token as YAML keys with literal values
    re.compile(
        r"(?P<key>(?:password|secret|token|api_key|apikey|auth_token|access_key))"
        r"(?P<sep>\s*:\s*)"
        r"(?P<val>['\"]?(?!\$\{)[^\s'\"#\n]+['\"]?)",
        re.IGNORECASE,
    ),
    # URLs with embedded credentials: https://user:pass@host
    re.compile(
        r"(?P<key>https?://)(?P<sep>[^@\s]+@)(?P<val>)",
    ),
)


# ── Public API ────────────────────────────────────────────────────────


def sanitize_secrets(content: str) -> str:
    """Remove potential secret values from file content.

    Preserves key names and structure so LLM can still understand
    what tools/services are configured, but replaces actual values
    with ``***``.

    Template references like ``${{ secrets.X }}`` and ``${VAR}``
    are preserved — they are not actual secrets.

    Args:
        content: Raw file content (YAML, TOML, JSON, etc.).

    Returns:
        Content with secret values replaced by ``***``.
    """
    result = content
    for pattern in _SECRET_PATTERNS:
        result = pattern.sub(_secret_replacer, result)
    return result


def _secret_replacer(match: re.Match[str]) -> str:
    """Replace secret value keeping the key and separator."""
    groups = match.groupdict()
    key = groups.get("key", "")
    sep = groups.get("sep", "")
    # For URL credentials: https://***@
    if key.startswith("http"):
        return f"{key}{_REDACTED}@"
    return f"{key}{sep}{_REDACTED}"


def classify_collected_files(
    collected_configs: dict[str, str],
) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    """Split collected configs into dependency, config, and CI files.

    A file may appear in multiple categories (e.g. ``pyproject.toml``
    goes to both dependency and config).

    Args:
        collected_configs: Path → content mapping from config collector.

    Returns:
        Three dicts: (dependency_files, config_files, ci_files).
    """
    dep_files: dict[str, str] = {}
    cfg_files: dict[str, str] = {}
    ci_files: dict[str, str] = {}

    for path, content in collected_configs.items():
        name = path.rsplit("/", 1)[-1]
        if name in DEPENDENCY_FILES:
            dep_files[path] = content
        if name in CONFIG_FILES:
            cfg_files[path] = content
        if _is_ci_file(path):
            ci_files[path] = content

    return dep_files, cfg_files, ci_files


def detect_package_managers(file_tree: Sequence[str]) -> tuple[str, ...]:
    """Detect package managers from lock files in the file tree.

    Args:
        file_tree: Repository file paths.

    Returns:
        Sorted tuple of detected package manager names.
    """
    managers: list[str] = []
    tree_names = {p.rsplit("/", 1)[-1] for p in file_tree}

    for indicator, manager in PACKAGE_MANAGER_INDICATORS.items():
        if indicator in tree_names:
            managers.append(manager)

    # Fallback: requirements.txt without lock → pip
    if not managers and "requirements.txt" in tree_names:
        managers.append("pip")

    return tuple(sorted(set(managers)))


def detect_layout(file_tree: Sequence[str]) -> str | None:
    """Detect project layout from file tree structure.

    Args:
        file_tree: Repository file paths.

    Returns:
        ``"src"``, ``"flat"``, ``"monorepo"``, or ``None``.
    """
    if not file_tree:
        return None

    has_src = any(p.startswith("src/") for p in file_tree)
    has_packages = any(p.startswith("packages/") for p in file_tree)
    has_apps = any(p.startswith("apps/") for p in file_tree)

    # Monorepo: multiple dirs containing their own dependency files
    dirs_with_packages: set[str] = set()
    for path in file_tree:
        parts = path.split("/")
        if len(parts) >= _MIN_PARTS_FOR_SUBDIR and parts[-1] in DEPENDENCY_FILES:
            # Use parent dir as the "package" identity
            dirs_with_packages.add("/".join(parts[:-1]))

    is_monorepo = (
        has_packages or (has_apps and has_src) or len(dirs_with_packages) >= _MIN_DIRS_FOR_MONOREPO
    )
    if is_monorepo:
        return "monorepo"
    if has_src:
        return "src"

    root_source = [p for p in file_tree if "/" not in p and p.endswith(_SOURCE_EXTENSIONS)]
    if root_source:
        return "flat"
    return None


def check_file_tree_truncation(file_tree: Sequence[str]) -> bool:
    """Check if file tree exceeds the limit.

    Args:
        file_tree: Repository file paths.

    Returns:
        ``True`` if the tree has >= ``FILE_TREE_LIMIT`` entries.
    """
    return len(file_tree) >= FILE_TREE_LIMIT


# ── Helpers ───────────────────────────────────────────────────────────


def _is_ci_file(path: str) -> bool:
    """Check if a path looks like a CI configuration file."""
    name = path.rsplit("/", 1)[-1]
    if name in CI_FILE_NAMES:
        return True
    return any(path.startswith(prefix) for prefix in CI_FILE_PREFIXES)


__all__ = [
    "CI_FILE_NAMES",
    "CI_FILE_PREFIXES",
    "CONFIG_FILES",
    "DEPENDENCY_FILES",
    "FILE_TREE_LIMIT",
    "PACKAGE_MANAGER_INDICATORS",
    "check_file_tree_truncation",
    "classify_collected_files",
    "detect_layout",
    "detect_package_managers",
    "sanitize_secrets",
]
