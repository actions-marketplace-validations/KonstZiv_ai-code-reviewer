"""Tests for discovery.diff_analysis — MR-aware diff analysis."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime

import pytest

from ai_reviewer.core.models import FileChange, FileChangeType
from ai_reviewer.discovery.cache import DiscoveryCache
from ai_reviewer.discovery.diff_analysis import (
    DiffDepsChange,
    DiffLanguageProfile,
    analyze_diff_languages,
    check_watch_files_in_diff,
    detect_deps_changes,
    detect_language_from_path,
    format_deps_change_context,
    format_diff_language_context,
)
from ai_reviewer.discovery.models import LLMDiscoveryResult


def _make_change(
    filename: str,
    *,
    additions: int = 10,
    deletions: int = 0,
    patch: str | None = None,
) -> FileChange:
    return FileChange(
        filename=filename,
        change_type=FileChangeType.MODIFIED,
        additions=additions,
        deletions=deletions,
        patch=patch,
    )


# ── detect_language_from_path ────────────────────────────────────────


class TestDetectLanguageFromPath:
    """Tests for file-path-to-language detection."""

    @pytest.mark.parametrize(
        ("path", "expected"),
        [
            ("src/main.py", "Python"),
            ("app.js", "JavaScript"),
            ("lib/types.ts", "TypeScript"),
            ("cmd/main.go", "Go"),
            ("src/lib.rs", "Rust"),
            ("migrations/001.sql", "SQL"),
            ("config.yml", "YAML"),
            (".github/workflows/ci.yaml", "YAML"),
            ("Dockerfile", "Dockerfile"),
            ("Makefile", "Makefile"),
            ("styles.css", "CSS"),
        ],
    )
    def test_known_extensions(self, path: str, expected: str) -> None:
        assert detect_language_from_path(path) == expected

    def test_unknown_extension(self) -> None:
        assert detect_language_from_path("data.bin") is None

    def test_no_extension(self) -> None:
        assert detect_language_from_path("LICENSE") is None

    def test_dockerfile_basename(self) -> None:
        assert detect_language_from_path("docker/Dockerfile") == "Dockerfile"


# ── analyze_diff_languages ───────────────────────────────────────────


class TestAnalyzeDiffLanguages:
    """Tests for diff language analysis."""

    def test_python_repo_sql_diff(self) -> None:
        """Python repo + SQL diff → matches_repo=False."""
        changes = (
            _make_change("migrations/001.sql", additions=50),
            _make_change(".github/workflows/ci.yml", additions=20),
            _make_change("Dockerfile", additions=10),
        )
        repo_langs = {"Python": 85.0, "Shell": 15.0}

        result = analyze_diff_languages(changes, repo_langs)

        assert result is not None
        assert result.primary_language == "SQL"
        assert result.matches_repo is False
        assert "SQL" in result.adaptation_note
        assert "Python" in result.adaptation_note

    def test_python_repo_python_diff(self) -> None:
        """Python repo + Python diff → matches_repo=True."""
        changes = (
            _make_change("src/main.py", additions=30),
            _make_change("tests/test_main.py", additions=20),
        )
        repo_langs = {"Python": 95.0, "Shell": 5.0}

        result = analyze_diff_languages(changes, repo_langs)

        assert result is not None
        assert result.primary_language == "Python"
        assert result.matches_repo is True
        assert result.adaptation_note == ""

    def test_no_recognizable_files(self) -> None:
        """Unknown file extensions → None."""
        changes = (_make_change("data.bin", additions=100),)

        result = analyze_diff_languages(changes, {"Python": 100.0})

        assert result is None

    def test_empty_changes(self) -> None:
        assert analyze_diff_languages((), {"Python": 100.0}) is None

    def test_zero_line_files_still_counted(self) -> None:
        """Files with 0 additions+deletions still get counted as 1 line."""
        changes = (_make_change("main.py", additions=0, deletions=0),)
        result = analyze_diff_languages(changes, {"Python": 100.0})
        assert result is not None
        assert result.primary_language == "Python"

    def test_percentages_sum_to_100(self) -> None:
        changes = (
            _make_change("a.py", additions=50),
            _make_change("b.js", additions=50),
        )
        result = analyze_diff_languages(changes, {"Python": 100.0})
        assert result is not None
        total = sum(result.languages.values())
        assert total == pytest.approx(100.0, abs=0.2)


# ── check_watch_files_in_diff ────────────────────────────────────────


class TestCheckWatchFilesInDiff:
    """Tests for watch-files overlap detection."""

    def _make_cache(self, watch_paths: tuple[str, ...]) -> DiscoveryCache:
        snapshot = {p: hashlib.sha256(b"x").hexdigest() for p in watch_paths}
        return DiscoveryCache(
            repo_key="owner/repo",
            result=LLMDiscoveryResult(),
            watch_files_snapshot=snapshot,
            created_at=datetime.now(tz=UTC),
        )

    def test_overlap_detected(self) -> None:
        """MR changes a watch-file → returned in overlap set."""
        changes = (
            _make_change("src/main.py"),
            _make_change("pyproject.toml"),
        )
        cached = self._make_cache(("pyproject.toml", ".github/workflows/ci.yml"))

        overlap = check_watch_files_in_diff(changes, cached)

        assert overlap == frozenset({"pyproject.toml"})

    def test_no_overlap(self) -> None:
        """MR doesn't change any watch-files → empty set."""
        changes = (_make_change("src/main.py"),)
        cached = self._make_cache(("pyproject.toml",))

        overlap = check_watch_files_in_diff(changes, cached)

        assert overlap == frozenset()

    def test_no_cache(self) -> None:
        """No cache → empty set."""
        changes = (_make_change("pyproject.toml"),)

        overlap = check_watch_files_in_diff(changes, None)

        assert overlap == frozenset()

    def test_empty_snapshot(self) -> None:
        cached = DiscoveryCache(
            repo_key="owner/repo",
            result=LLMDiscoveryResult(),
            watch_files_snapshot={},
            created_at=datetime.now(tz=UTC),
        )
        overlap = check_watch_files_in_diff((_make_change("pyproject.toml"),), cached)
        assert overlap == frozenset()


# ── detect_deps_changes ──────────────────────────────────────────────


class TestDetectDepsChanges:
    """Tests for dependency change detection from diffs."""

    def test_pyproject_toml_added_deps(self) -> None:
        """New deps detected from pyproject.toml diff."""
        patch = '@@ -10,3 +10,5 @@\n "flask>=3.0",\n+"sqlalchemy>=2.0",\n+"alembic>=1.0",\n'
        changes = (_make_change("pyproject.toml", additions=2, patch=patch),)

        result = detect_deps_changes(changes)

        assert result is not None
        assert "sqlalchemy" in result.added
        assert "alembic" in result.added
        assert result.removed == ()

    def test_package_json_added_deps(self) -> None:
        """New deps detected from package.json diff."""
        patch = (
            "@@ -5,3 +5,5 @@\n"
            '   "react": "^18.0",\n'
            '+  "axios": "^1.6",\n'
            '+  "@tanstack/react-query": "^5.0"\n'
        )
        changes = (_make_change("package.json", additions=2, patch=patch),)

        result = detect_deps_changes(changes)

        assert result is not None
        assert "axios" in result.added
        assert "@tanstack/react-query" in result.added

    def test_go_mod_deps(self) -> None:
        """New deps detected from go.mod diff."""
        patch = (
            "@@ -3,2 +3,3 @@\n+github.com/gorilla/mux v1.8.0\n-github.com/gin-gonic/gin v1.9.0\n"
        )
        changes = (_make_change("go.mod", additions=1, deletions=1, patch=patch),)

        result = detect_deps_changes(changes)

        assert result is not None
        assert "github.com/gorilla/mux" in result.added
        assert "github.com/gin-gonic/gin" in result.removed

    def test_no_dep_file_in_diff(self) -> None:
        """No dependency files in diff → None."""
        changes = (_make_change("src/main.py", patch="+ pass"),)

        result = detect_deps_changes(changes)

        assert result is None

    def test_dep_file_no_patch(self) -> None:
        """Dep file exists but no patch → None."""
        changes = (_make_change("pyproject.toml", patch=None),)

        result = detect_deps_changes(changes)

        assert result is None

    def test_version_bump_not_reported(self) -> None:
        """Same dep added and removed (version bump) → filtered out."""
        patch = '@@ -10,1 +10,1 @@\n-"flask>=2.0",\n+"flask>=3.0",\n'
        changes = (_make_change("pyproject.toml", additions=1, deletions=1, patch=patch),)

        result = detect_deps_changes(changes)

        # flask appears in both added and removed → version bump → filtered
        assert result is None

    def test_metadata_lines_skipped(self) -> None:
        """Lines like name=, version=, description= are skipped."""
        patch = (
            "@@ -1,3 +1,3 @@\n"
            '+name = "my-project"\n'
            '+version = "1.0.0"\n'
            '+description = "A project"\n'
        )
        changes = (_make_change("pyproject.toml", additions=3, patch=patch),)

        result = detect_deps_changes(changes)

        assert result is None

    def test_nested_dep_file(self) -> None:
        """Dep file in subdirectory is also detected."""
        patch = '@@ -1,1 +1,2 @@\n "flask>=2.0"\n+"celery>=5.0"\n'
        changes = (_make_change("backend/pyproject.toml", additions=1, patch=patch),)

        result = detect_deps_changes(changes)

        assert result is not None
        assert "celery" in result.added


# ── Prompt formatting ────────────────────────────────────────────────


class TestFormatDiffLanguageContext:
    """Tests for diff language prompt formatting."""

    def test_mismatch_produces_section(self) -> None:
        profile = DiffLanguageProfile(
            languages={"SQL": 60.0, "YAML": 30.0, "Dockerfile": 10.0},
            primary_language="SQL",
            matches_repo=False,
            adaptation_note="This MR is primarily SQL (60%) + YAML (30%), not Python.",
        )
        result = format_diff_language_context(profile)
        assert "## MR Language Mismatch" in result
        assert "SQL" in result

    def test_match_returns_empty(self) -> None:
        profile = DiffLanguageProfile(
            languages={"Python": 100.0},
            primary_language="Python",
            matches_repo=True,
        )
        result = format_diff_language_context(profile)
        assert result == ""


class TestFormatDepsChangeContext:
    """Tests for dependency change prompt formatting."""

    def test_added_deps(self) -> None:
        deps = DiffDepsChange(added=("sqlalchemy", "alembic"))
        result = format_deps_change_context(deps)
        assert "## Dependency Changes" in result
        assert "sqlalchemy" in result
        assert "attack surface" in result

    def test_removed_deps(self) -> None:
        deps = DiffDepsChange(removed=("flask",))
        result = format_deps_change_context(deps)
        assert "Removed: flask" in result
        assert "attack surface" not in result  # No warning for removals only
