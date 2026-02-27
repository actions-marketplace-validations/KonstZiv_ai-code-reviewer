"""Watch-files caching for Discovery LLM results.

Avoids re-running LLM analysis when project configuration hasn't changed.
The LLM returns a ``watch_files`` list on first run; subsequent runs hash
those files and compare against the cached snapshot.

Typical flow::

    Run 1: raw_data -> LLM -> result + watch_files   (~500 tokens)
    Run 2: check watch_files -> unchanged -> cache    (0 tokens)
    Run N: watch_file changed -> LLM -> new result    (~500 tokens)
"""

from __future__ import annotations

import hashlib
import logging
from abc import ABC, abstractmethod
from datetime import datetime  # noqa: TC003
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from ai_reviewer.discovery.models import LLMDiscoveryResult  # noqa: TC001

if TYPE_CHECKING:
    from ai_reviewer.integrations.repository import RepositoryProvider

logger = logging.getLogger(__name__)

# Sentinel hash for files that don't exist at snapshot time.
_NOT_FOUND_HASH = "NOT_FOUND"


# ── Models ───────────────────────────────────────────────────────────


class DiscoveryCache(BaseModel):
    """Cached LLM discovery result with watch-files snapshot.

    Attributes:
        repo_key: Repository identifier (e.g. ``owner/repo``).
        result: The cached LLM discovery response.
        watch_files_snapshot: Mapping of watched file paths to SHA-256 hashes.
        created_at: When the cache entry was created.
        llm_model: Model identifier used for the cached result.
    """

    model_config = ConfigDict(frozen=True)

    repo_key: str = Field(..., min_length=1, description="Repository identifier")
    result: LLMDiscoveryResult = Field(..., description="Cached LLM response")
    watch_files_snapshot: dict[str, str] = Field(
        ..., description="Watched file path to SHA-256 hash"
    )
    created_at: datetime = Field(..., description="Cache creation timestamp")
    llm_model: str = Field(default="", description="LLM model used for cached result")


# ── Storage interface ────────────────────────────────────────────────


class DiscoveryCacheStorage(ABC):
    """Abstract interface for discovery cache storage."""

    @abstractmethod
    def get(self, repo_key: str) -> DiscoveryCache | None:
        """Get cached result if it exists.

        Args:
            repo_key: Repository identifier.

        Returns:
            Cached entry or ``None`` if not found.
        """

    @abstractmethod
    def put(self, cache: DiscoveryCache) -> None:
        """Store a discovery cache entry.

        Args:
            cache: The cache entry to store.
        """

    @abstractmethod
    def invalidate(self, repo_key: str) -> None:
        """Remove a cached result.

        Args:
            repo_key: Repository identifier.
        """


class InMemoryDiscoveryCache(DiscoveryCacheStorage):
    """Simple in-memory cache.

    Lives as long as the process runs. Sufficient for GitHub Action
    (one run = one MR). Persistent storage (Redis/file) planned for Beta-1.
    """

    def __init__(self) -> None:
        self._store: dict[str, DiscoveryCache] = {}

    def get(self, repo_key: str) -> DiscoveryCache | None:
        return self._store.get(repo_key)

    def put(self, cache: DiscoveryCache) -> None:
        self._store[cache.repo_key] = cache

    def invalidate(self, repo_key: str) -> None:
        self._store.pop(repo_key, None)


# ── Watch-files logic ────────────────────────────────────────────────


def create_watch_files_snapshot(
    repo: RepositoryProvider,
    repo_key: str,
    watch_files: tuple[str, ...],
) -> dict[str, str]:
    """Hash watch-files for future comparison.

    Args:
        repo: Repository provider for fetching file content.
        repo_key: Repository identifier.
        watch_files: File paths to snapshot.

    Returns:
        Mapping of file path to SHA-256 hex digest (or ``NOT_FOUND``).
    """
    snapshot: dict[str, str] = {}
    for path in watch_files:
        content = repo.get_file_content(repo_key, path)
        if content is None:
            snapshot[path] = _NOT_FOUND_HASH
        else:
            snapshot[path] = hashlib.sha256(content.encode()).hexdigest()
    return snapshot


def should_rerun_discovery(
    repo: RepositoryProvider,
    repo_key: str,
    cache_storage: DiscoveryCacheStorage,
    *,
    llm_model: str = "",
) -> tuple[bool, DiscoveryCache | None]:
    """Check if cached discovery result is still valid.

    Args:
        repo: Repository provider for fetching file content.
        repo_key: Repository identifier.
        cache_storage: Cache storage backend.
        llm_model: Current LLM model name. If different from cached,
            forces re-run.

    Returns:
        Tuple of (should_rerun, cached_entry).
        ``(True, None)`` on cache miss,
        ``(True, cached)`` when files changed or model changed,
        ``(False, cached)`` when cache is valid.
    """
    cached = cache_storage.get(repo_key)

    if cached is None:
        return True, None

    # Model change → invalidate
    if llm_model and cached.llm_model and llm_model != cached.llm_model:
        logger.info(
            "LLM model changed (%s -> %s), invalidating cache",
            cached.llm_model,
            llm_model,
        )
        return True, cached

    # No watch-files → always re-run (LLM didn't provide any)
    if not cached.watch_files_snapshot:
        return True, cached

    # Check each watch-file
    for path, old_hash in cached.watch_files_snapshot.items():
        content = repo.get_file_content(repo_key, path)
        if content is None:
            new_hash = _NOT_FOUND_HASH
        else:
            new_hash = hashlib.sha256(content.encode()).hexdigest()

        if new_hash != old_hash:
            logger.info("Watch-file changed: %s", path)
            return True, cached

    logger.info("All watch-files unchanged, using cache for %s", repo_key)
    return False, cached


__all__ = [
    "DiscoveryCache",
    "DiscoveryCacheStorage",
    "InMemoryDiscoveryCache",
    "create_watch_files_snapshot",
    "should_rerun_discovery",
]
