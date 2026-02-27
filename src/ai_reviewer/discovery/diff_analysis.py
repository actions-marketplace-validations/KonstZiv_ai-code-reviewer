"""MR-aware diff analysis for Discovery.

Analyses the actual MR diff to detect:
- **Language mismatch**: diff language differs from repo primary language.
- **Watch-files overlap**: diff touches cached watch-files (force re-discovery).
- **Dependency changes**: new/removed packages in dependency manifests.

All functions are pure — no I/O, no LLM calls.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from ai_reviewer.core.models import FileChange
    from ai_reviewer.discovery.cache import DiscoveryCache

# ── Extension → language mapping ─────────────────────────────────────

_EXT_TO_LANG: dict[str, str] = {
    ".py": "Python",
    ".pyi": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".java": "Java",
    ".kt": "Kotlin",
    ".cs": "C#",
    ".cpp": "C++",
    ".cc": "C++",
    ".c": "C",
    ".h": "C",
    ".hpp": "C++",
    ".swift": "Swift",
    ".php": "PHP",
    ".sql": "SQL",
    ".sh": "Shell",
    ".bash": "Shell",
    ".zsh": "Shell",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".json": "JSON",
    ".toml": "TOML",
    ".xml": "XML",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".md": "Markdown",
    ".rst": "reStructuredText",
    ".dockerfile": "Dockerfile",
    ".tf": "Terraform",
    ".hcl": "HCL",
    ".proto": "Protobuf",
    ".graphql": "GraphQL",
    ".r": "R",
    ".lua": "Lua",
    ".ex": "Elixir",
    ".exs": "Elixir",
    ".hs": "Haskell",
    ".scala": "Scala",
    ".clj": "Clojure",
}

# File names that map to a specific language (no extension needed).
_NAME_TO_LANG: dict[str, str] = {
    "Dockerfile": "Dockerfile",
    "Makefile": "Makefile",
    "Jenkinsfile": "Groovy",
    "Vagrantfile": "Ruby",
    "Gemfile": "Ruby",
    "Rakefile": "Ruby",
}

# Dependency manifest file names (basename only).
_DEPENDENCY_FILES: frozenset[str] = frozenset(
    {
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "requirements.txt",
        "Pipfile",
        "package.json",
        "go.mod",
        "Cargo.toml",
        "Gemfile",
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
    }
)

# Regex patterns for extracting dependency names from added/removed lines.
_DEP_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    # Pattern for pyproject.toml dependency lines (quoted package names).
    ("pyproject.toml", re.compile(r'^[+\-]\s*"?([a-zA-Z0-9_][a-zA-Z0-9_\-]*)')),
    # Pattern for requirements.txt lines (bare package names).
    ("requirements.txt", re.compile(r"^[+\-]\s*([a-zA-Z0-9_][a-zA-Z0-9_\-]*)")),
    # Pattern for package.json dependency entries.
    ("package.json", re.compile(r'^[+\-]\s*"([a-zA-Z0-9@_][a-zA-Z0-9@/_\-]*)":\s*"')),
    # Pattern for go.mod require directives.
    ("go.mod", re.compile(r"^[+\-]\s*(?:require\s+)?([a-zA-Z0-9./\-]+)\s+v")),
    # Pattern for Cargo.toml dependency entries.
    ("Cargo.toml", re.compile(r"^[+\-]\s*([a-zA-Z0-9_][a-zA-Z0-9_\-]*)\s*=")),
)

# Lines to skip when parsing dependency diffs (headers, comments, metadata).
_SKIP_LINE_RE = re.compile(
    r"^[+\-]\s*(?:#|//|<!--|\[|name\s*=|version\s*=|description\s*=|"
    r"authors?\s*=|license\s*=|readme\s*=|edition\s*=|requires-python|"
    r"python_requires|\"name\"|\"version\"|\"description\"|\"license\"|"
    r"\"private\"|\"scripts\"|\"engines\")"
)


# ── Models ───────────────────────────────────────────────────────────


class DiffLanguageProfile(BaseModel):
    """Languages present in the actual MR diff.

    Attributes:
        languages: Language name to percentage mapping.
        primary_language: Dominant language in the diff.
        matches_repo: Whether diff primary matches repo primary.
        adaptation_note: Human-readable note for the review prompt.
    """

    model_config = ConfigDict(frozen=True)

    languages: dict[str, float] = Field(..., description="Language to percentage")
    primary_language: str = Field(..., min_length=1, description="Dominant diff language")
    matches_repo: bool = Field(..., description="Diff primary matches repo primary")
    adaptation_note: str = Field(default="", description="Adaptation note for prompt")


class DiffDepsChange(BaseModel):
    """Dependencies added or removed in this MR.

    Attributes:
        added: Newly added dependency names.
        removed: Removed dependency names.
    """

    model_config = ConfigDict(frozen=True)

    added: tuple[str, ...] = Field(default=(), description="Newly added deps")
    removed: tuple[str, ...] = Field(default=(), description="Removed deps")


# ── Language analysis ────────────────────────────────────────────────


def detect_language_from_path(path: str) -> str | None:
    """Detect programming language from a file path.

    Checks basename first (Dockerfile, Makefile), then extension.

    Returns:
        Language name or ``None`` if unknown.
    """
    # Check basename
    basename = path.rsplit("/", 1)[-1] if "/" in path else path
    lang = _NAME_TO_LANG.get(basename)
    if lang:
        return lang

    # Check extension
    dot_idx = basename.rfind(".")
    if dot_idx == -1:
        return None
    ext = basename[dot_idx:].lower()
    return _EXT_TO_LANG.get(ext)


def analyze_diff_languages(
    changes: tuple[FileChange, ...],
    repo_languages: dict[str, float],
) -> DiffLanguageProfile | None:
    """Analyze which languages are present in the MR diff.

    Args:
        changes: File changes from the MR.
        repo_languages: Repository-level language percentages.

    Returns:
        Language profile of the diff, or ``None`` if no recognizable files.
    """
    lang_lines: dict[str, int] = {}

    for change in changes:
        lang = detect_language_from_path(change.filename)
        if lang is None:
            continue
        lines = change.additions + change.deletions
        if lines == 0:
            lines = 1  # count file presence even with 0 lines
        lang_lines[lang] = lang_lines.get(lang, 0) + lines

    if not lang_lines:
        return None

    total = sum(lang_lines.values())
    languages = {lang: round((lines / total) * 100, 1) for lang, lines in lang_lines.items()}
    primary = max(languages, key=lambda k: languages[k])

    repo_primary = max(repo_languages, key=lambda k: repo_languages[k]) if repo_languages else ""
    matches = primary == repo_primary

    note = ""
    if not matches and repo_primary:
        top_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)[:3]
        lang_summary = " + ".join(f"{lang} ({pct:.0f}%)" for lang, pct in top_langs)
        note = f"This MR is primarily {lang_summary}, not the repo's primary {repo_primary}."

    return DiffLanguageProfile(
        languages=languages,
        primary_language=primary,
        matches_repo=matches,
        adaptation_note=note,
    )


# ── Watch-files in diff ──────────────────────────────────────────────


def check_watch_files_in_diff(
    changes: tuple[FileChange, ...],
    cached: DiscoveryCache | None,
) -> frozenset[str]:
    """Check if this MR modifies any cached watch-files.

    Args:
        changes: File changes from the MR.
        cached: Existing discovery cache entry (may be ``None``).

    Returns:
        Set of watch-file paths found in the diff (empty if none).
    """
    if cached is None or not cached.watch_files_snapshot:
        return frozenset()

    diff_paths = {c.filename for c in changes}
    watch_paths = set(cached.watch_files_snapshot)

    return frozenset(diff_paths & watch_paths)


# ── Dependency changes ───────────────────────────────────────────────


def _basename(path: str) -> str:
    """Extract basename from a file path."""
    return path.rsplit("/", 1)[-1] if "/" in path else path


def _extract_dep_from_line(line: str, filename: str) -> str | None:
    """Extract a dependency name from a diff line.

    Args:
        line: A single diff line starting with + or -.
        filename: The basename of the dependency file.

    Returns:
        Dependency name or ``None``.
    """
    if _SKIP_LINE_RE.match(line):
        return None

    for pattern_file, pattern in _DEP_PATTERNS:
        if pattern_file == filename:
            m = pattern.match(line)
            if m:
                return m.group(1)

    return None


def detect_deps_changes(
    changes: tuple[FileChange, ...],
) -> DiffDepsChange | None:
    """Detect dependency additions and removals from the MR diff.

    Parses patch content of dependency manifest files (pyproject.toml,
    package.json, go.mod, etc.) to extract added/removed packages.

    Args:
        changes: File changes from the MR.

    Returns:
        Dependency changes, or ``None`` if no dependency files changed.
    """
    dep_changes = [c for c in changes if _basename(c.filename) in _DEPENDENCY_FILES]
    if not dep_changes:
        return None

    added: list[str] = []
    removed: list[str] = []

    for change in dep_changes:
        if not change.patch:
            continue

        basename = _basename(change.filename)
        for line in change.patch.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                dep = _extract_dep_from_line(line, basename)
                if dep:
                    added.append(dep)
            elif line.startswith("-") and not line.startswith("---"):
                dep = _extract_dep_from_line(line, basename)
                if dep:
                    removed.append(dep)

    # Remove deps that appear in both (version bumps, not real adds/removes)
    added_set = set(added) - set(removed)
    removed_set = set(removed) - set(added)

    if not added_set and not removed_set:
        return None

    return DiffDepsChange(
        added=tuple(sorted(added_set)),
        removed=tuple(sorted(removed_set)),
    )


# ── Prompt formatting ────────────────────────────────────────────────


def format_diff_language_context(profile: DiffLanguageProfile) -> str:
    """Format diff language mismatch as a prompt section.

    Returns an empty string if the diff language matches the repo.
    """
    if profile.matches_repo or not profile.adaptation_note:
        return ""
    return f"\n## MR Language Mismatch\n{profile.adaptation_note}"


def format_deps_change_context(deps: DiffDepsChange) -> str:
    """Format dependency changes as a prompt section."""
    parts: list[str] = ["\n## Dependency Changes in This MR"]
    if deps.added:
        parts.append("Added: " + ", ".join(deps.added))
    if deps.removed:
        parts.append("Removed: " + ", ".join(deps.removed))
    if deps.added:
        parts.append(
            "New dependencies increase attack surface. "
            "Verify they are necessary and from trusted sources."
        )
    return "\n".join(parts)


__all__ = [
    "DiffDepsChange",
    "DiffLanguageProfile",
    "analyze_diff_languages",
    "check_watch_files_in_diff",
    "detect_deps_changes",
    "detect_language_from_path",
    "format_deps_change_context",
    "format_diff_language_context",
]
