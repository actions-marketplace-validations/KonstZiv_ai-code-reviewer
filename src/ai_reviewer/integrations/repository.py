"""Abstract base class for repository metadata and file access.

This module defines the ``RepositoryProvider`` interface for accessing
repository-level data (languages, metadata, file tree, file content)
through platform APIs without cloning the repository.

Used by the Discovery engine to gather project context (CI config,
conventions, languages) before generating a review.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RepositoryMetadata(BaseModel):
    """Repository metadata from the platform API.

    Attributes:
        name: Full repository name (e.g. ``owner/repo``).
        description: Repository description text.
        default_branch: Name of the default branch.
        topics: Repository topics / tags.
        license: SPDX license identifier (e.g. ``MIT``, ``Apache-2.0``).
        visibility: ``public``, ``private``, or ``internal``.
        ci_config_path: Custom CI configuration path (GitLab-specific).
    """

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., min_length=1, description="Full repository name")
    description: str | None = Field(default=None, description="Repository description")
    default_branch: str = Field(default="main", description="Default branch name")
    topics: tuple[str, ...] = Field(default=(), description="Repository topics")
    license: str | None = Field(default=None, description="SPDX license identifier")
    visibility: Literal["public", "private", "internal"] = Field(
        default="private", description="Repository visibility"
    )
    ci_config_path: str | None = Field(default=None, description="Custom CI config path (GitLab)")


class RepositoryProvider(ABC):
    """Abstract interface for repository data access.

    Provides read-only access to repository metadata and files via the
    platform API. Implementations exist for GitHub (PyGithub) and
    GitLab (python-gitlab).
    """

    @abstractmethod
    def get_languages(self, repo_name: str) -> dict[str, float]:
        """Get programming languages used in the repository.

        Args:
            repo_name: Repository identifier (e.g. ``owner/repo``).

        Returns:
            Mapping of language name to percentage (0-100).
            GitHub returns bytes — implementations must convert to percentages.
            GitLab returns percentages natively.
        """

    @abstractmethod
    def get_metadata(self, repo_name: str) -> RepositoryMetadata:
        """Get basic repository metadata.

        Args:
            repo_name: Repository identifier.

        Returns:
            RepositoryMetadata populated from the platform API.
        """

    @abstractmethod
    def get_file_tree(
        self,
        repo_name: str,
        *,
        ref: str | None = None,
    ) -> tuple[str, ...]:
        """Get the list of file paths in the repository.

        Returns blob paths only (no directories). Uses the platform's
        tree API to avoid cloning. Limited to ~10 000 entries on GitHub.

        Args:
            repo_name: Repository identifier.
            ref: Git ref (branch, tag, SHA). Defaults to the default branch.

        Returns:
            Tuple of file paths relative to the repository root.
        """

    @abstractmethod
    def get_file_content(
        self,
        repo_name: str,
        path: str,
        *,
        ref: str | None = None,
    ) -> str | None:
        """Get the content of a single file.

        Args:
            repo_name: Repository identifier.
            path: File path relative to the repository root.
            ref: Git ref (branch, tag, SHA). Defaults to the default branch.

        Returns:
            File content as a string, or ``None`` if the file is binary,
            does not exist, or is a directory.
        """


__all__ = [
    "RepositoryMetadata",
    "RepositoryProvider",
]
