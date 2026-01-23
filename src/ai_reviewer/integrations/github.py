"""GitHub integration for AI Code Reviewer.

This module provides a client for interacting with the GitHub API using PyGithub.
It handles fetching merge requests (pull requests), retrieving linked tasks (issues),
and posting review comments.
"""

from __future__ import annotations

import functools
import logging
import re
from typing import TYPE_CHECKING, ParamSpec, TypeVar

from github import Github, GithubException, RateLimitExceededException
from github.Auth import Token

from ai_reviewer.core.models import (
    Comment,
    CommentAuthorType,
    CommentType,
    FileChange,
    FileChangeType,
    LinkedTask,
    MergeRequest,
)

if TYPE_CHECKING:
    from collections.abc import Callable


logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")

HTTP_FORBIDDEN = 403


def handle_rate_limit(func: Callable[P, R]) -> Callable[P, R | None]:  # noqa: UP047
    """Decorator to handle GitHub API rate limits.

    Args:
        func: The function to decorate.

    Returns:
        The decorated function which returns None on rate limit error.
    """

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R | None:
        try:
            return func(*args, **kwargs)
        except RateLimitExceededException:
            logger.exception("GitHub API rate limit exceeded.")
            # We cannot post a comment if the rate limit is exceeded.
            # Ideally, we would notify the user, but we are blocked.
            return None
        except GithubException as e:
            # Re-raise other GitHub exceptions
            if e.status == HTTP_FORBIDDEN and "rate limit" in str(e).lower():
                logger.exception("GitHub API rate limit exceeded (403).")
                return None
            raise

    return wrapper


class GitHubClient:
    """Client for interacting with GitHub API.

    Attributes:
        github: The PyGithub instance.
    """

    def __init__(self, token: str) -> None:
        """Initialize GitHub client.

        Args:
            token: GitHub personal access token.
        """
        auth = Token(token)
        self.github = Github(auth=auth)
        logger.debug("GitHub client initialized")

    @handle_rate_limit
    def get_pull_request(self, repo_name: str, pr_number: int) -> MergeRequest:
        """Fetch a pull request from GitHub and convert to MergeRequest model.

        Args:
            repo_name: Repository name in 'owner/repo' format.
            pr_number: Pull request number.

        Returns:
            MergeRequest model populated with PR data.

        Raises:
            ValueError: If repo_name is invalid or PR not found.
            GithubException: If API call fails.
        """
        try:
            repo = self.github.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
        except GithubException:
            logger.exception("Failed to fetch PR %s from %s", pr_number, repo_name)
            raise

        # Fetch comments (both issue comments and review comments)
        comments: list[Comment] = []

        # 1. Issue comments (general discussion)
        for issue_comment in pr.get_issue_comments():
            comments.append(
                Comment(
                    author=issue_comment.user.login,
                    author_type=(
                        CommentAuthorType.BOT
                        if issue_comment.user.type == "Bot"
                        else CommentAuthorType.USER
                    ),
                    body=issue_comment.body,
                    type=CommentType.ISSUE,
                    created_at=issue_comment.created_at,
                )
            )

        # 2. Review comments (code specific)
        for review_comment in pr.get_review_comments():
            comments.append(
                Comment(
                    author=review_comment.user.login,
                    author_type=(
                        CommentAuthorType.BOT
                        if review_comment.user.type == "Bot"
                        else CommentAuthorType.USER
                    ),
                    body=review_comment.body,
                    type=CommentType.REVIEW,
                    created_at=review_comment.created_at,
                )
            )

        # Fetch file changes
        changes: list[FileChange] = []
        for file in pr.get_files():
            # Determine change type
            if file.status == "added":
                change_type = FileChangeType.ADDED
            elif file.status == "modified":
                change_type = FileChangeType.MODIFIED
            elif file.status == "removed":
                change_type = FileChangeType.DELETED
            elif file.status == "renamed":
                change_type = FileChangeType.RENAMED
            else:
                # Fallback for unknown status
                change_type = FileChangeType.MODIFIED

            # Handle binary or large files where patch might be None
            patch_content = file.patch
            if patch_content is None:
                logger.debug(
                    "File %s has no patch (binary or too large), skipping content",
                    file.filename,
                )

            changes.append(
                FileChange(
                    filename=file.filename,
                    change_type=change_type,
                    additions=file.additions,
                    deletions=file.deletions,
                    patch=patch_content,
                    previous_filename=file.previous_filename,
                )
            )

        return MergeRequest(
            number=pr.number,
            title=pr.title,
            description=pr.body or "",
            author=pr.user.login,
            source_branch=pr.head.ref,
            target_branch=pr.base.ref,
            comments=tuple(comments),
            changes=tuple(changes),
            url=pr.html_url,
            created_at=pr.created_at,
            updated_at=pr.updated_at,
        )

    @handle_rate_limit
    def get_linked_task(self, repo_name: str, pr: MergeRequest) -> LinkedTask | None:
        """Attempt to find a linked task/issue for the PR.

        Looks for patterns like "Fixes #123" or "Closes #123" in the PR description.
        If found, fetches the issue details from GitHub.

        Args:
            repo_name: Repository name in 'owner/repo' format.
            pr: The MergeRequest object to check.

        Returns:
            LinkedTask if found, None otherwise.
        """
        if not pr.description:
            return None

        # Common GitHub keywords for closing issues
        # https://docs.github.com/en/issues/tracking-your-work-with-issues/linking-a-pull-request-to-an-issue
        pattern = r"(?:close|closes|closed|fix|fixes|fixed|resolve|resolves|resolved)\s+#(\d+)"
        match = re.search(pattern, pr.description, re.IGNORECASE)

        if not match:
            return None

        issue_number = int(match.group(1))

        try:
            repo = self.github.get_repo(repo_name)
            issue = repo.get_issue(issue_number)

            return LinkedTask(
                identifier=str(issue.number),
                title=issue.title,
                description=issue.body or "",
                url=issue.html_url,
            )
        except GithubException as e:
            logger.warning("Found issue link #%s but failed to fetch it: %s", issue_number, e)
            return None

    @handle_rate_limit
    def post_review_comment(self, repo_name: str, pr_number: int, comment: str) -> None:
        """Post a comment to the pull request.

        Args:
            repo_name: Repository name in 'owner/repo' format.
            pr_number: Pull request number.
            comment: The comment text to post.

        Raises:
            GithubException: If API call fails.
        """
        try:
            repo = self.github.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            pr.create_issue_comment(comment)
            logger.info("Posted review comment to PR #%s in %s", pr_number, repo_name)
        except GithubException:
            logger.exception("Failed to post comment to PR #%s in %s", pr_number, repo_name)
            raise
