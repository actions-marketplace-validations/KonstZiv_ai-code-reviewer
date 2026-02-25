"""Deterministic CI pipeline analyzer.

Parses CI configuration files (GitHub Actions YAML, GitLab CI YAML,
Makefiles) to extract tool usage, language versions, package managers,
services, deployment targets, and coverage thresholds.

Zero LLM tokens — all detection is regex-based.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import yaml

from ai_reviewer.discovery.models import CIInsights, DetectedTool, ToolCategory

if TYPE_CHECKING:
    from typing import Any

_MAX_RECURSION_DEPTH = 20

# ── Tool detection patterns ──────────────────────────────────────────
# Mapping: regex pattern → (tool_name, category)
# Order matters: more specific patterns must come first (e.g. "ruff format" before "ruff").

_TOOL_PATTERNS: tuple[tuple[str, str, ToolCategory], ...] = (
    # Python — specific before generic
    (r"\bruff\b\s+format", "ruff format", ToolCategory.FORMATTING),
    (r"\bruff\b(?:\s+check)?(?!\s+format)", "ruff", ToolCategory.LINTING),
    (r"\bflake8\b", "flake8", ToolCategory.LINTING),
    (r"\bpylint\b", "pylint", ToolCategory.LINTING),
    (r"\bblack\b", "black", ToolCategory.FORMATTING),
    (r"\bisort\b", "isort", ToolCategory.FORMATTING),
    (r"\bmypy\b", "mypy", ToolCategory.TYPE_CHECKING),
    (r"\bpyright\b", "pyright", ToolCategory.TYPE_CHECKING),
    (r"\bpytest\b", "pytest", ToolCategory.TESTING),
    (r"\bbandit\b", "bandit", ToolCategory.SECURITY),
    (r"\bsafety\b(?:\s+check)?", "safety", ToolCategory.SECURITY),
    (r"\bpre-commit\b", "pre-commit", ToolCategory.META),
    # JavaScript / TypeScript
    (r"\beslint\b", "eslint", ToolCategory.LINTING),
    (r"\bbiome\b", "biome", ToolCategory.LINTING),
    (r"\bprettier\b", "prettier", ToolCategory.FORMATTING),
    (r"\btsc\b", "tsc", ToolCategory.TYPE_CHECKING),
    (r"\bjest\b", "jest", ToolCategory.TESTING),
    (r"\bvitest\b", "vitest", ToolCategory.TESTING),
    (r"\bmocha\b", "mocha", ToolCategory.TESTING),
    (r"\bnpm\s+audit\b", "npm audit", ToolCategory.SECURITY),
    # Go
    (r"\bgo\s+vet\b", "go vet", ToolCategory.LINTING),
    (r"\bgolangci-lint\b", "golangci-lint", ToolCategory.LINTING),
    (r"\bgo\s+test\b", "go test", ToolCategory.TESTING),
    (r"\bgofmt\b", "gofmt", ToolCategory.FORMATTING),
    # Rust
    (r"\bcargo\s+clippy\b", "cargo clippy", ToolCategory.LINTING),
    (r"\bcargo\s+fmt\b", "cargo fmt", ToolCategory.FORMATTING),
    (r"\bcargo\s+test\b", "cargo test", ToolCategory.TESTING),
)

# Pre-compiled tool regexes for performance.
_COMPILED_TOOL_PATTERNS: tuple[tuple[re.Pattern[str], str, ToolCategory], ...] = tuple(
    (re.compile(pattern), name, category) for pattern, name, category in _TOOL_PATTERNS
)

# ── Version detection patterns ───────────────────────────────────────

_VERSION_PATTERNS: dict[str, tuple[re.Pattern[str], ...]] = {
    "python": (
        re.compile(r"python-version:\s*['\"]?(\d+\.\d+)"),
        re.compile(r"python-version:\s*\[.*?['\"](\d+\.\d+)['\"]"),
        re.compile(r"python:(\d+\.\d+)"),
    ),
    "node": (
        re.compile(r"node-version:\s*['\"]?(\d+)"),
        re.compile(r"node-version:\s*\[.*?['\"](\d+)['\"]"),
        re.compile(r"node:(\d+)"),
    ),
    "go": (
        re.compile(r"go-version:\s*['\"]?(\d+\.\d+)"),
        re.compile(r"go-version:\s*\[.*?['\"](\d+\.\d+)['\"]"),
        re.compile(r"golang:(\d+\.\d+)"),
    ),
}

# ── Package manager patterns ─────────────────────────────────────────
# Order: more specific first.

_PKG_MANAGER_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\buv\b\s+(?:sync|run|pip|add)"), "uv"),
    (re.compile(r"\bpoetry\b\s+(?:install|run|add)"), "poetry"),
    (re.compile(r"\bpip\b\s+install"), "pip"),
    (re.compile(r"\bnpm\b\s+(?:ci|install)"), "npm"),
    (re.compile(r"\byarn\b(?:\s+install)?"), "yarn"),
    (re.compile(r"\bpnpm\b"), "pnpm"),
    (re.compile(r"\bcargo\b\s+(?:build|test|run)"), "cargo"),
)

# ── Coverage threshold patterns ──────────────────────────────────────

_COVERAGE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"--cov-fail-under[=\s]+(\d+)"),
    re.compile(r"coverage_minimum[=:\s]+(\d+)"),
    re.compile(r"--coverageThreshold.*?branches.*?(\d+)"),
    re.compile(r"fail_under\s*=\s*(\d+)"),
    re.compile(r"min_coverage[=:\s]+(\d+)"),
)

# ── Service detection ────────────────────────────────────────────────

_KNOWN_SERVICES = frozenset(
    {
        "postgres",
        "postgresql",
        "mysql",
        "mariadb",
        "redis",
        "mongo",
        "mongodb",
        "rabbitmq",
        "elasticsearch",
        "memcached",
    }
)

# ── Deployment detection ─────────────────────────────────────────────

_DEPLOYMENT_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\btwine\s+upload\b"), "pypi"),
    (re.compile(r"\bdocker\s+push\b"), "docker_registry"),
    (re.compile(r"\bhelm\s+(?:upgrade|install)\b"), "kubernetes"),
    (re.compile(r"\bnpm\s+publish\b"), "npm_registry"),
    (re.compile(r"\bcargo\s+publish\b"), "crates_io"),
    (re.compile(r"\bgh\s+release\b"), "github_releases"),
)

# ── YAML command extraction keys ─────────────────────────────────────

_COMMAND_KEYS = frozenset(
    {
        "run",
        "script",
        "before_script",
        "after_script",
        "command",
        "commands",
    }
)


class CIPipelineAnalyzer:
    """Deterministic CI pipeline configuration analyzer.

    Extracts development tools, language versions, package managers,
    services, deployment targets, and coverage thresholds from CI
    configuration files using regex pattern matching.
    """

    def analyze(self, yaml_content: str, ci_file_path: str = "ci.yml") -> CIInsights:
        """Parse YAML CI configuration into CIInsights.

        Args:
            yaml_content: Raw YAML content of the CI file.
            ci_file_path: Path to the CI file for context.

        Returns:
            CIInsights with all detected information.
        """
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError:
            return CIInsights(ci_file_path=ci_file_path, raw_yaml=yaml_content)
        if not isinstance(data, dict):
            return CIInsights(ci_file_path=ci_file_path, raw_yaml=yaml_content)

        commands = _extract_commands(data)
        full_text = yaml_content + "\n" + "\n".join(commands)

        return CIInsights(
            ci_file_path=ci_file_path,
            raw_yaml=yaml_content,
            detected_tools=_detect_tools(commands),
            python_version=_detect_version(full_text, "python"),
            node_version=_detect_version(full_text, "node"),
            go_version=_detect_version(full_text, "go"),
            package_manager=_detect_package_manager(commands),
            services=_detect_services(data),
            deployment_targets=_detect_deployments(commands),
            min_coverage=_detect_coverage_threshold(commands),
        )

    def analyze_makefile(self, content: str, ci_file_path: str = "Makefile") -> CIInsights:
        """Parse a Makefile as a CI proxy.

        Extracts tool usage from Makefile targets. Treats each
        indented line as a command.

        Args:
            content: Raw Makefile content.
            ci_file_path: Path to the Makefile.

        Returns:
            CIInsights with detected tools and settings.
        """
        commands: list[str] = []
        for line in content.split("\n"):
            stripped = line.strip()
            if line.startswith(("\t", "    ")):
                commands.append(stripped)

        return CIInsights(
            ci_file_path=ci_file_path,
            raw_yaml=content,
            detected_tools=_detect_tools(commands),
            python_version=_detect_version("\n".join(commands), "python"),
            node_version=_detect_version("\n".join(commands), "node"),
            go_version=_detect_version("\n".join(commands), "go"),
            package_manager=_detect_package_manager(commands),
            services=(),
            deployment_targets=_detect_deployments(commands),
            min_coverage=_detect_coverage_threshold(commands),
        )


# ── Private helpers ──────────────────────────────────────────────────


def _extract_commands(data: Any, *, _depth: int = 0) -> list[str]:  # noqa: ANN401
    """Recursively extract command strings from YAML structure.

    Walks the parsed YAML tree looking for known command keys
    (``run``, ``script``, ``before_script``, etc.) and collects
    their string values.

    Args:
        data: Parsed YAML data (dict, list, or scalar).
        _depth: Current recursion depth (safety limit).

    Returns:
        List of command strings found in the YAML.
    """
    if _depth > _MAX_RECURSION_DEPTH:
        return []

    commands: list[str] = []

    if isinstance(data, dict):
        for key, value in data.items():
            if key in _COMMAND_KEYS:
                if isinstance(value, str):
                    commands.append(value)
                elif isinstance(value, list):
                    commands.extend(str(item) for item in value if item is not None)
            else:
                commands.extend(_extract_commands(value, _depth=_depth + 1))
    elif isinstance(data, list):
        for item in data:
            commands.extend(_extract_commands(item, _depth=_depth + 1))

    return commands


def _detect_tools(commands: list[str]) -> tuple[DetectedTool, ...]:
    """Detect development tools from command strings.

    Scans each command against known tool patterns. Deduplicates
    by tool name (first match wins for the command string).

    Args:
        commands: List of CI command strings.

    Returns:
        Tuple of unique DetectedTool instances.
    """
    seen: dict[str, DetectedTool] = {}
    joined = "\n".join(commands)

    for regex, name, category in _COMPILED_TOOL_PATTERNS:
        if name in seen:
            continue
        match = regex.search(joined)
        if match:
            # Find the full command line containing this match
            command_line = ""
            for cmd in commands:
                if regex.search(cmd):
                    command_line = cmd.strip()
                    break
            seen[name] = DetectedTool(
                name=name,
                category=category,
                command=command_line,
            )

    return tuple(seen.values())


def _detect_version(text: str, language: str) -> str | None:
    """Detect language version from text using known patterns.

    Args:
        text: Combined YAML + commands text to search.
        language: Language key (``python``, ``node``, ``go``).

    Returns:
        Version string or None if not found.
    """
    patterns = _VERSION_PATTERNS.get(language, ())
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            return match.group(1)
    return None


def _detect_package_manager(commands: list[str]) -> str | None:
    """Detect the package manager from commands.

    Args:
        commands: List of CI command strings.

    Returns:
        Package manager name or None.
    """
    joined = "\n".join(commands)
    for pattern, name in _PKG_MANAGER_PATTERNS:
        if pattern.search(joined):
            return name
    return None


def _detect_services(data: Any) -> tuple[str, ...]:  # noqa: ANN401
    """Detect CI service containers from YAML structure.

    Looks for ``services`` keys in the YAML and matches container
    image names against known service databases.

    Args:
        data: Parsed YAML data.

    Returns:
        Tuple of normalized service names.
    """
    found: list[str] = []
    _collect_services(data, found, depth=0)
    # Deduplicate while preserving order
    seen: set[str] = set()
    result: list[str] = []
    for svc in found:
        if svc not in seen:
            seen.add(svc)
            result.append(svc)
    return tuple(result)


def _collect_services(data: Any, found: list[str], *, depth: int) -> None:  # noqa: ANN401
    """Recursively collect service names from YAML.

    Args:
        data: Current YAML node.
        found: Accumulator list for found services.
        depth: Recursion depth limit.
    """
    if depth > _MAX_RECURSION_DEPTH or not isinstance(data, dict):
        return

    for key, value in data.items():
        if key == "services":
            if isinstance(value, dict):
                for svc_key in value:
                    normalized = _normalize_service_name(str(svc_key))
                    if normalized:
                        found.append(normalized)
            elif isinstance(value, list):
                for item in value:
                    name = str(item) if not isinstance(item, dict) else str(item.get("image", ""))
                    normalized = _normalize_service_name(name)
                    if normalized:
                        found.append(normalized)
        elif isinstance(value, dict):
            _collect_services(value, found, depth=depth + 1)


def _normalize_service_name(raw: str) -> str | None:
    """Normalize a service image name to a known service.

    Args:
        raw: Raw image name (e.g. ``postgres:16``, ``redis:7-alpine``).

    Returns:
        Normalized service name, or None if not recognized.
    """
    base = raw.split(":")[0].split("/")[-1].lower()
    for known in _KNOWN_SERVICES:
        if base.startswith(known):
            return known
    return None


def _detect_deployments(commands: list[str]) -> tuple[str, ...]:
    """Detect deployment targets from commands.

    Args:
        commands: List of CI command strings.

    Returns:
        Tuple of deployment target identifiers.
    """
    joined = "\n".join(commands)
    targets: list[str] = []
    for pattern, name in _DEPLOYMENT_PATTERNS:
        if pattern.search(joined):
            targets.append(name)
    return tuple(targets)


def _detect_coverage_threshold(commands: list[str]) -> int | None:
    """Detect minimum coverage threshold from commands.

    Args:
        commands: List of CI command strings.

    Returns:
        Coverage threshold as integer (0-100), or None.
    """
    joined = "\n".join(commands)
    for pattern in _COVERAGE_PATTERNS:
        match = pattern.search(joined)
        if match:
            value = int(match.group(1))
            if 0 <= value <= 100:  # noqa: PLR2004
                return value
    return None


__all__ = ["CIPipelineAnalyzer"]
