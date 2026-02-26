"""Config collection layer (Discovery Layer 2).

Collects project configuration files via ``RepositoryProvider.get_file_content()``.
Two modes:

- **Targeted**: CI insights available — fetch only configs for detected tools.
- **Broad**: no CI — fetch all known configs for detected languages.

Zero LLM tokens: purely deterministic API calls.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from ai_reviewer.discovery.models import CIInsights, PlatformData
    from ai_reviewer.integrations.repository import RepositoryProvider

# ── Constants ────────────────────────────────────────────────────────

MAX_CHARS_PER_FILE: int = 10_000
MAX_CHARS_TOTAL: int = 50_000

TOOL_CONFIG_MAP: dict[str, tuple[str, ...]] = {
    # Python
    "ruff": ("pyproject.toml", "ruff.toml", ".ruff.toml"),
    "mypy": ("pyproject.toml", "mypy.ini", ".mypy.ini", "setup.cfg"),
    "pytest": ("pyproject.toml", "pytest.ini", "setup.cfg", "conftest.py"),
    "black": ("pyproject.toml", "black.toml", ".black.toml"),
    "isort": ("pyproject.toml", ".isort.cfg", "setup.cfg"),
    "flake8": (".flake8", "setup.cfg", "tox.ini"),
    "bandit": ("pyproject.toml", ".bandit", "bandit.yaml"),
    "pre-commit": (".pre-commit-config.yaml",),
    "pylint": ("pyproject.toml", ".pylintrc", "pylintrc", "setup.cfg"),
    # JS/TS
    "eslint": (
        "eslint.config.js",
        "eslint.config.mjs",
        ".eslintrc.json",
        ".eslintrc.js",
        ".eslintrc.yml",
    ),
    "prettier": (".prettierrc", ".prettierrc.json", ".prettierrc.js", "prettier.config.js"),
    "jest": ("jest.config.js", "jest.config.ts", "package.json"),
    "vitest": ("vitest.config.ts", "vitest.config.js", "package.json"),
    "tsc": ("tsconfig.json",),
    "biome": ("biome.json", "biome.jsonc"),
    # Go
    "golangci-lint": (".golangci.yml", ".golangci.yaml", ".golangci.toml"),
    # Rust
    "cargo clippy": ("clippy.toml", ".clippy.toml"),
}

LANGUAGE_CONFIG_MAP: dict[str, tuple[str, ...]] = {
    "Python": (
        "pyproject.toml",
        "setup.cfg",
        "setup.py",
        "tox.ini",
        ".pre-commit-config.yaml",
        "Pipfile",
    ),
    "JavaScript": ("package.json", "tsconfig.json", ".babelrc", "webpack.config.js"),
    "TypeScript": ("package.json", "tsconfig.json"),
    "Go": ("go.mod",),
    "Rust": ("Cargo.toml",),
    "Java": ("pom.xml", "build.gradle", "build.gradle.kts"),
}


# ── Model ────────────────────────────────────────────────────────────


class ConfigContent(BaseModel):
    """Content of a single configuration file."""

    model_config = ConfigDict(frozen=True)

    path: str
    content: str
    size_chars: int = Field(ge=0)
    truncated: bool = False


# ── Selector ─────────────────────────────────────────────────────────


class SmartConfigSelector:
    """Select config file paths based on CI insights or language heuristics.

    Stateless: all data flows through method arguments.
    """

    @staticmethod
    def _filter_configs(
        file_tree: Sequence[str],
        keys: Iterable[str],
        mapping: dict[str, tuple[str, ...]],
    ) -> tuple[str, ...]:
        """Filter and deduplicate config paths against the file tree.

        Args:
            file_tree: Repository file paths to match against.
            keys: Lookup keys (tool names or language names).
            mapping: Key → candidate config paths mapping.

        Returns:
            Sorted, deduplicated tuple of config paths present in file tree.
        """
        file_set = set(file_tree)
        seen: set[str] = set()
        result: list[str] = []

        for key in keys:
            for path in mapping.get(key, ()):
                if path not in seen and path in file_set:
                    seen.add(path)
                    result.append(path)

        result.sort()
        return tuple(result)

    def select_targeted(
        self,
        platform_data: PlatformData,
        ci_insights: CIInsights,
    ) -> tuple[str, ...]:
        """Select configs for tools detected in CI.

        Args:
            platform_data: Platform metadata (used for ``file_tree``).
            ci_insights: CI analysis results with detected tools.

        Returns:
            Sorted, deduplicated tuple of config paths present in file tree.
        """
        return self._filter_configs(
            platform_data.file_tree,
            (t.name for t in ci_insights.detected_tools),
            TOOL_CONFIG_MAP,
        )

    def select_broad(
        self,
        platform_data: PlatformData,
    ) -> tuple[str, ...]:
        """Select configs based on detected languages (no CI available).

        Args:
            platform_data: Platform metadata with languages and file tree.

        Returns:
            Sorted, deduplicated tuple of config paths present in file tree.
        """
        return self._filter_configs(
            platform_data.file_tree,
            platform_data.languages,
            LANGUAGE_CONFIG_MAP,
        )


# ── Collector ────────────────────────────────────────────────────────


class ConfigCollector:
    """Fetch configuration file contents via the repository provider.

    Respects per-file and total character limits to keep the discovery
    payload manageable.
    """

    def __init__(self, repo_provider: RepositoryProvider) -> None:
        self._repo = repo_provider

    def collect(
        self,
        repo_name: str,
        paths: Sequence[str],
    ) -> tuple[ConfigContent, ...]:
        """Collect config file contents for given paths.

        Args:
            repo_name: Repository identifier (e.g. ``owner/repo``).
            paths: Config file paths to fetch.

        Returns:
            Tuple of ``ConfigContent`` objects, respecting size limits.
        """
        configs: list[ConfigContent] = []
        total_chars = 0

        for path in paths:
            remaining = MAX_CHARS_TOTAL - total_chars
            if remaining <= 0:
                break

            raw = self._repo.get_file_content(repo_name, path)
            if raw is None:
                continue

            limit = min(MAX_CHARS_PER_FILE, remaining)
            truncated = len(raw) > limit
            content = raw[:limit] if truncated else raw

            configs.append(
                ConfigContent(
                    path=path,
                    content=content,
                    size_chars=len(content),
                    truncated=truncated,
                ),
            )
            total_chars += len(content)

        return tuple(configs)


__all__ = [
    "LANGUAGE_CONFIG_MAP",
    "MAX_CHARS_PER_FILE",
    "MAX_CHARS_TOTAL",
    "TOOL_CONFIG_MAP",
    "ConfigCollector",
    "ConfigContent",
    "SmartConfigSelector",
]
