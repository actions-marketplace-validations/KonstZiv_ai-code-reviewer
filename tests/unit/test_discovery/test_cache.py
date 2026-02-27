"""Tests for discovery.cache — watch-files caching."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from ai_reviewer.discovery.cache import (
    DiscoveryCache,
    InMemoryDiscoveryCache,
    create_watch_files_snapshot,
    should_rerun_discovery,
)
from ai_reviewer.discovery.models import LLMDiscoveryResult
from ai_reviewer.integrations.repository import RepositoryProvider


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@pytest.fixture
def mock_repo() -> MagicMock:
    return MagicMock(spec=RepositoryProvider)


@pytest.fixture
def sample_result() -> LLMDiscoveryResult:
    return LLMDiscoveryResult(
        watch_files=("pyproject.toml", ".github/workflows/ci.yml"),
        watch_files_reason="CI and dependency config",
    )


@pytest.fixture
def sample_cache(sample_result: LLMDiscoveryResult) -> DiscoveryCache:
    return DiscoveryCache(
        repo_key="owner/repo",
        result=sample_result,
        watch_files_snapshot={
            "pyproject.toml": _sha256("old-content"),
            ".github/workflows/ci.yml": _sha256("ci-content"),
        },
        created_at=datetime.now(tz=UTC),
        llm_model="gemini-3-flash-preview",
    )


# ── InMemoryDiscoveryCache ───────────────────────────────────────────


class TestInMemoryDiscoveryCache:
    """Tests for InMemoryDiscoveryCache CRUD operations."""

    def test_get_returns_none_on_miss(self) -> None:
        cache = InMemoryDiscoveryCache()
        assert cache.get("owner/repo") is None

    def test_put_and_get(self, sample_cache: DiscoveryCache) -> None:
        cache = InMemoryDiscoveryCache()
        cache.put(sample_cache)
        assert cache.get("owner/repo") == sample_cache

    def test_invalidate_removes_entry(self, sample_cache: DiscoveryCache) -> None:
        cache = InMemoryDiscoveryCache()
        cache.put(sample_cache)
        cache.invalidate("owner/repo")
        assert cache.get("owner/repo") is None

    def test_invalidate_nonexistent_is_noop(self) -> None:
        cache = InMemoryDiscoveryCache()
        cache.invalidate("owner/repo")  # Should not raise

    def test_put_overwrites_existing(self, sample_cache: DiscoveryCache) -> None:
        cache = InMemoryDiscoveryCache()
        cache.put(sample_cache)

        new_result = LLMDiscoveryResult(framework="Django")
        new_entry = DiscoveryCache(
            repo_key="owner/repo",
            result=new_result,
            watch_files_snapshot={},
            created_at=datetime.now(tz=UTC),
            llm_model="gemini-3-flash-preview",
        )
        cache.put(new_entry)
        assert cache.get("owner/repo") == new_entry


# ── create_watch_files_snapshot ──────────────────────────────────────


class TestCreateWatchFilesSnapshot:
    """Tests for snapshot creation."""

    def test_creates_hashes_for_existing_files(self, mock_repo: MagicMock) -> None:
        mock_repo.get_file_content.side_effect = ["content-a", "content-b"]

        snapshot = create_watch_files_snapshot(
            mock_repo, "owner/repo", ("file_a.toml", "file_b.yml")
        )

        assert snapshot == {
            "file_a.toml": _sha256("content-a"),
            "file_b.yml": _sha256("content-b"),
        }

    def test_not_found_files_get_sentinel(self, mock_repo: MagicMock) -> None:
        mock_repo.get_file_content.return_value = None

        snapshot = create_watch_files_snapshot(mock_repo, "owner/repo", ("missing.toml",))

        assert snapshot == {"missing.toml": "NOT_FOUND"}

    def test_empty_watch_files(self, mock_repo: MagicMock) -> None:
        snapshot = create_watch_files_snapshot(mock_repo, "owner/repo", ())
        assert snapshot == {}
        mock_repo.get_file_content.assert_not_called()


# ── should_rerun_discovery ───────────────────────────────────────────


class TestShouldRerunDiscovery:
    """Tests for watch-files check logic."""

    def test_cache_miss_returns_true_none(self, mock_repo: MagicMock) -> None:
        """No cached entry → must run."""
        storage = InMemoryDiscoveryCache()

        rerun, cached = should_rerun_discovery(mock_repo, "owner/repo", storage)

        assert rerun is True
        assert cached is None

    def test_cache_hit_files_unchanged(
        self, mock_repo: MagicMock, sample_cache: DiscoveryCache
    ) -> None:
        """All watch-files unchanged → use cache."""
        storage = InMemoryDiscoveryCache()
        storage.put(sample_cache)

        # Return same content as when snapshot was taken
        mock_repo.get_file_content.side_effect = ["old-content", "ci-content"]

        rerun, cached = should_rerun_discovery(
            mock_repo, "owner/repo", storage, llm_model="gemini-3-flash-preview"
        )

        assert rerun is False
        assert cached == sample_cache

    def test_cache_hit_file_changed(
        self, mock_repo: MagicMock, sample_cache: DiscoveryCache
    ) -> None:
        """One file changed → re-run."""
        storage = InMemoryDiscoveryCache()
        storage.put(sample_cache)

        mock_repo.get_file_content.side_effect = ["NEW-content", "ci-content"]

        rerun, cached = should_rerun_discovery(
            mock_repo, "owner/repo", storage, llm_model="gemini-3-flash-preview"
        )

        assert rerun is True
        assert cached == sample_cache

    def test_cache_hit_file_deleted(
        self, mock_repo: MagicMock, sample_cache: DiscoveryCache
    ) -> None:
        """Watch-file deleted → re-run."""
        storage = InMemoryDiscoveryCache()
        storage.put(sample_cache)

        # First file now returns None (deleted)
        mock_repo.get_file_content.side_effect = [None, "ci-content"]

        rerun, cached = should_rerun_discovery(
            mock_repo, "owner/repo", storage, llm_model="gemini-3-flash-preview"
        )

        assert rerun is True
        assert cached == sample_cache

    def test_model_change_invalidates_cache(
        self, mock_repo: MagicMock, sample_cache: DiscoveryCache
    ) -> None:
        """Different LLM model → re-run even if files unchanged."""
        storage = InMemoryDiscoveryCache()
        storage.put(sample_cache)

        rerun, cached = should_rerun_discovery(
            mock_repo, "owner/repo", storage, llm_model="gemini-2.5-flash"
        )

        assert rerun is True
        assert cached == sample_cache
        # Should not check files at all
        mock_repo.get_file_content.assert_not_called()

    def test_empty_snapshot_forces_rerun(
        self, mock_repo: MagicMock, sample_result: LLMDiscoveryResult
    ) -> None:
        """Cache with empty snapshot → always re-run."""
        storage = InMemoryDiscoveryCache()
        entry = DiscoveryCache(
            repo_key="owner/repo",
            result=sample_result,
            watch_files_snapshot={},
            created_at=datetime.now(tz=UTC),
            llm_model="gemini-3-flash-preview",
        )
        storage.put(entry)

        rerun, cached = should_rerun_discovery(
            mock_repo, "owner/repo", storage, llm_model="gemini-3-flash-preview"
        )

        assert rerun is True
        assert cached == entry

    def test_no_model_specified_skips_model_check(
        self, mock_repo: MagicMock, sample_cache: DiscoveryCache
    ) -> None:
        """None llm_model → skip model comparison, check files."""
        storage = InMemoryDiscoveryCache()
        storage.put(sample_cache)

        mock_repo.get_file_content.side_effect = ["old-content", "ci-content"]

        rerun, cached = should_rerun_discovery(mock_repo, "owner/repo", storage)

        assert rerun is False
        assert cached == sample_cache


# ── DiscoveryCache model ─────────────────────────────────────────────


class TestDiscoveryCacheModel:
    """Tests for DiscoveryCache Pydantic model."""

    def test_frozen(self, sample_cache: DiscoveryCache) -> None:
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            sample_cache.repo_key = "other"  # type: ignore[misc]

    def test_serialization_roundtrip(self, sample_cache: DiscoveryCache) -> None:
        data = sample_cache.model_dump()
        restored = DiscoveryCache.model_validate(data)
        assert restored == sample_cache
