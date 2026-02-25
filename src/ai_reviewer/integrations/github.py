"""GitHub integration for AI Code Reviewer.

This module provides a client for interacting with the GitHub API using PyGithub.
It handles fetching merge requests (pull requests), retrieving linked tasks (issues),
and posting review comments.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

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
from ai_reviewer.integrations.base import ISSUE_CLOSING_RE, GitProvider, _parse_branch_issue_number
from ai_reviewer.integrations.conversation import (
    BOT_QUESTION_MARKER,
    BotThread,
    ConversationProvider,
    ThreadStatus,
    format_questions_markdown,
    parse_questions_from_markdown,
)
from ai_reviewer.integrations.repository import RepositoryMetadata, RepositoryProvider
from ai_reviewer.utils.retry import (
    AuthenticationError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    ServerError,
    with_retry,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from ai_reviewer.integrations.base import ReviewSubmission
    from ai_reviewer.integrations.conversation import BotQuestion


logger = logging.getLogger(__name__)

# HTTP status codes
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_INTERNAL_SERVER_ERROR = 500


def _convert_github_exception(e: GithubException) -> Exception:
    """Convert PyGithub exception to our exception hierarchy.

    Args:
        e: PyGithub exception.

    Returns:
        Converted exception (RetryableError or APIClientError).
    """
    status = e.status
    message = str(e.data) if e.data else str(e)

    if status == HTTP_UNAUTHORIZED:
        return AuthenticationError(f"GitHub: {message}")

    if status == HTTP_FORBIDDEN:
        # Check if this is rate limit (GitHub returns 403 for secondary rate limit)
        if "rate limit" in message.lower():
            return RateLimitError(f"GitHub: {message}")
        return ForbiddenError(f"GitHub: {message}")

    if status == HTTP_NOT_FOUND:
        return NotFoundError(f"GitHub: {message}")

    if status >= HTTP_INTERNAL_SERVER_ERROR:
        return ServerError(f"GitHub: {message}", status_code=status)

    # For other errors, return as-is (will not be retried)
    return e


class GitHubClient(GitProvider, RepositoryProvider, ConversationProvider):
    """Client for interacting with GitHub API.

    Implements GitProvider, RepositoryProvider, and ConversationProvider
    interfaces for GitHub-specific operations.

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

    @with_retry
    def get_merge_request(self, repo_name: str, mr_id: int) -> MergeRequest:
        """Fetch a pull request from GitHub and convert to MergeRequest model.

        Args:
            repo_name: Repository name in 'owner/repo' format.
            mr_id: Pull request number.

        Returns:
            MergeRequest model populated with PR data.

        Raises:
            AuthenticationError: If token is invalid.
            NotFoundError: If PR or repo doesn't exist.
            RateLimitError: If rate limit exceeded (will retry).
            ServerError: If GitHub server error (will retry).
        """
        try:
            repo = self.github.get_repo(repo_name)
            pr = repo.get_pull(mr_id)
        except RateLimitExceededException as e:
            logger.warning("GitHub rate limit exceeded for PR %s in %s", mr_id, repo_name)
            msg = f"GitHub rate limit exceeded: {e}"
            raise RateLimitError(msg) from e
        except GithubException as e:
            logger.warning("GitHub API error for PR %s in %s: %s", mr_id, repo_name, e)
            raise _convert_github_exception(e) from e

        # Fetch comments (both issue comments and review comments)
        comments: list[Comment] = []

        # 1. Issue comments (general discussion — no threading)
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
                    comment_id=str(issue_comment.id),
                )
            )

        # 2. Review comments (code specific — with threading)
        for review_comment in pr.get_review_comments():
            # Extract line number (may be None for outdated comments)
            raw_line = getattr(review_comment, "line", None)
            line_number: int | None = int(raw_line) if raw_line is not None else None

            # Threading: in_reply_to_id points to the root comment of the thread
            comment_id_str = str(review_comment.id)
            raw_in_reply_to = getattr(review_comment, "in_reply_to_id", None)
            parent_id: str | None = str(raw_in_reply_to) if raw_in_reply_to is not None else None
            thread_id = str(raw_in_reply_to) if raw_in_reply_to is not None else comment_id_str

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
                    file_path=getattr(review_comment, "path", None),
                    line_number=line_number,
                    comment_id=comment_id_str,
                    parent_comment_id=parent_id,
                    thread_id=thread_id,
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

    @staticmethod
    def _issue_to_linked_task(issue: object) -> LinkedTask:
        """Convert a PyGithub Issue to LinkedTask.

        Args:
            issue: PyGithub Issue object.

        Returns:
            LinkedTask model.
        """
        return LinkedTask(
            identifier=str(issue.number),  # type: ignore[attr-defined]
            title=issue.title,  # type: ignore[attr-defined]
            description=issue.body or "",  # type: ignore[attr-defined]
            url=issue.html_url,  # type: ignore[attr-defined]
        )

    def get_linked_tasks(  # noqa: PLR0912
        self,
        repo_name: str,
        mr_id: int,
        source_branch: str,
    ) -> tuple[LinkedTask, ...]:
        """Find linked tasks via regex, timeline events, and branch name.

        Combines three strategies (each fail-open):
        1. Regex matching of closing keywords in the PR description.
        2. GitHub timeline events (cross-referenced, connected).
        3. Branch name convention (e.g. ``86-task-description``).

        Note: This method does NOT use ``@with_retry`` as linked tasks
        are optional. Failure should not block the review.

        Args:
            repo_name: Repository name in 'owner/repo' format.
            mr_id: Pull request number.
            source_branch: Source branch name.

        Returns:
            Tuple of LinkedTask objects (deduplicated by issue number).
        """
        tasks: list[LinkedTask] = []
        seen_ids: set[int] = set()

        try:
            repo = self.github.get_repo(repo_name)
            pr = repo.get_pull(mr_id)

            # Strategy 1: Regex in description
            if pr.body:
                for match in ISSUE_CLOSING_RE.finditer(pr.body):
                    issue_number = int(match.group(1))
                    if issue_number in seen_ids:
                        continue
                    seen_ids.add(issue_number)
                    try:
                        issue = repo.get_issue(issue_number)
                        tasks.append(self._issue_to_linked_task(issue))
                    except (GithubException, RateLimitExceededException):
                        logger.warning("Failed to fetch issue #%s", issue_number)

            # Strategy 2: Timeline events
            try:
                for event in pr.as_issue().get_timeline():
                    if getattr(event, "event", None) not in (
                        "cross-referenced",
                        "connected",
                    ):
                        continue
                    source = getattr(event, "source", None)
                    if not source:
                        continue
                    issue_data = source.get("issue") if isinstance(source, dict) else None
                    if not issue_data:
                        continue
                    issue_number = issue_data.get("number")
                    if issue_number and issue_number not in seen_ids:
                        seen_ids.add(issue_number)
                        tasks.append(
                            LinkedTask(
                                identifier=str(issue_number),
                                title=issue_data.get("title", ""),
                                description=issue_data.get("body") or "",
                                url=issue_data.get("html_url", ""),
                            )
                        )
            except (GithubException, RateLimitExceededException):
                logger.debug("Timeline API unavailable for PR #%s", mr_id)

            # Strategy 3: Branch name convention
            branch_issue = _parse_branch_issue_number(source_branch)
            if branch_issue and branch_issue not in seen_ids:
                try:
                    issue = repo.get_issue(branch_issue)
                    seen_ids.add(branch_issue)
                    tasks.append(self._issue_to_linked_task(issue))
                except (GithubException, RateLimitExceededException):
                    logger.debug("Branch issue #%s not found", branch_issue)

        except (GithubException, RateLimitExceededException) as e:
            logger.warning("Failed task search for PR #%s: %s", mr_id, e)

        return tuple(tasks)

    @with_retry
    def post_comment(self, repo_name: str, mr_id: int, body: str) -> None:
        """Post a general comment to the pull request.

        This creates an Issue Comment visible in the PR conversation.
        Use this for summary comments, error notifications, etc.

        Args:
            repo_name: Repository name in 'owner/repo' format.
            mr_id: Pull request number.
            body: The comment text to post.

        Raises:
            AuthenticationError: If token is invalid.
            ForbiddenError: If insufficient permissions.
            RateLimitError: If rate limit exceeded (will retry).
            ServerError: If GitHub server error (will retry).
        """
        try:
            repo = self.github.get_repo(repo_name)
            pr = repo.get_pull(mr_id)
            pr.create_issue_comment(body)
            logger.info("Posted comment to PR #%s in %s", mr_id, repo_name)
        except RateLimitExceededException as e:
            logger.warning("GitHub rate limit exceeded posting comment to PR #%s", mr_id)
            msg = f"GitHub rate limit exceeded: {e}"
            raise RateLimitError(msg) from e
        except GithubException as e:
            logger.warning("Failed to post comment to PR #%s in %s: %s", mr_id, repo_name, e)
            raise _convert_github_exception(e) from e

    @with_retry
    def submit_review(
        self,
        repo_name: str,
        mr_id: int,
        submission: ReviewSubmission,
    ) -> None:
        """Submit a code review with inline comments.

        Uses GitHub's Pull Request Review API to create a review with
        inline comments attached to specific lines. This enables the
        "Apply suggestion" button for suggestions.

        Args:
            repo_name: Repository name in 'owner/repo' format.
            mr_id: Pull request number.
            submission: Review data including summary and line comments.

        Raises:
            AuthenticationError: If token is invalid.
            ForbiddenError: If insufficient permissions.
            RateLimitError: If rate limit exceeded (will retry).
            ServerError: If GitHub server error (will retry).
        """
        try:
            repo = self.github.get_repo(repo_name)
            pr = repo.get_pull(mr_id)

            # Get the latest commit SHA (required for creating review comments)
            commit_sha = pr.head.sha

            # Build review comments for the API
            # PyGithub's create_review expects a list of dicts
            review_comments = []
            for line_comment in submission.line_comments:
                comment_dict = {
                    "path": line_comment.path,
                    "line": line_comment.line,
                    "body": line_comment.format_body_with_suggestion(),
                    "side": line_comment.side,
                }
                review_comments.append(comment_dict)

            # Create the review
            # event can be: APPROVE, REQUEST_CHANGES, COMMENT
            # Note: PyGithub accepts dicts at runtime but type stubs expect ReviewComment
            pr.create_review(
                commit=repo.get_commit(commit_sha),
                body=submission.summary,
                event=submission.event,
                comments=review_comments if review_comments else None,  # type: ignore[arg-type]
            )

            logger.info(
                "Submitted review to PR #%s in %s with %d inline comments",
                mr_id,
                repo_name,
                len(review_comments),
            )

        except RateLimitExceededException as e:
            logger.warning("GitHub rate limit exceeded submitting review to PR #%s", mr_id)
            msg = f"GitHub rate limit exceeded: {e}"
            raise RateLimitError(msg) from e
        except GithubException as e:
            logger.warning("Failed to submit review to PR #%s in %s: %s", mr_id, repo_name, e)
            raise _convert_github_exception(e) from e

    # ── RepositoryProvider implementation ──────────────────────────────

    @with_retry
    def get_languages(self, repo_name: str) -> dict[str, float]:
        """Get repository languages as percentages.

        GitHub returns bytes per language; this method converts to percentages.

        Args:
            repo_name: Repository name in ``owner/repo`` format.

        Returns:
            Mapping of language name to percentage (0-100).
        """
        try:
            repo = self.github.get_repo(repo_name)
            langs = repo.get_languages()  # {name: bytes}
            total = sum(langs.values())
            if total == 0:
                return {}
            return {name: round(bytes_ / total * 100, 1) for name, bytes_ in langs.items()}
        except RateLimitExceededException as e:
            msg = f"GitHub: {e}"
            raise RateLimitError(msg) from e
        except GithubException as e:
            raise _convert_github_exception(e) from e

    @with_retry
    def get_metadata(self, repo_name: str) -> RepositoryMetadata:
        """Get basic repository metadata from GitHub.

        Args:
            repo_name: Repository name in ``owner/repo`` format.

        Returns:
            RepositoryMetadata populated from the GitHub API.
        """
        try:
            repo = self.github.get_repo(repo_name)
            return RepositoryMetadata(
                name=repo.full_name,
                description=repo.description,
                default_branch=repo.default_branch,
                topics=tuple(repo.get_topics()),
                license=repo.license.spdx_id if repo.license else None,
                visibility="public" if not repo.private else "private",
            )
        except RateLimitExceededException as e:
            msg = f"GitHub: {e}"
            raise RateLimitError(msg) from e
        except GithubException as e:
            raise _convert_github_exception(e) from e

    @with_retry
    def get_file_tree(
        self,
        repo_name: str,
        *,
        ref: str | None = None,
    ) -> tuple[str, ...]:
        """Get file paths in the repository (blobs only).

        Uses GitHub's Git Trees API with ``recursive=True``.
        Limited to ~10 000 entries by the API.

        Args:
            repo_name: Repository name in ``owner/repo`` format.
            ref: Git ref. Defaults to the default branch.

        Returns:
            Tuple of file paths relative to the repository root.
        """
        try:
            repo = self.github.get_repo(repo_name)
            branch = ref or repo.default_branch
            tree = repo.get_git_tree(branch, recursive=True)
            if getattr(tree, "truncated", False):
                logger.warning(
                    "Git tree for %s is truncated (exceeds 10,000 entries)",
                    repo_name,
                )
            return tuple(item.path for item in tree.tree if item.type == "blob")
        except RateLimitExceededException as e:
            msg = f"GitHub: {e}"
            raise RateLimitError(msg) from e
        except GithubException as e:
            raise _convert_github_exception(e) from e

    @with_retry
    def get_file_content(
        self,
        repo_name: str,
        path: str,
        *,
        ref: str | None = None,
    ) -> str | None:
        """Get file content as text.

        Args:
            repo_name: Repository name in ``owner/repo`` format.
            path: File path relative to the repository root.
            ref: Git ref. Defaults to the default branch.

        Returns:
            File content string, or ``None`` for binary files,
            directories, or if the file does not exist.
        """
        try:
            repo = self.github.get_repo(repo_name)
            kwargs: dict[str, str] = {"ref": ref} if ref else {}
            content_file = repo.get_contents(path, **kwargs)
            if isinstance(content_file, list) or content_file.type != "file":
                return None  # directory, submodule, or symlink
            try:
                return content_file.decoded_content.decode("utf-8")
            except UnicodeDecodeError:
                return None  # binary file
        except RateLimitExceededException as e:
            msg = f"GitHub: {e}"
            raise RateLimitError(msg) from e
        except GithubException as e:
            if getattr(e, "status", None) == HTTP_NOT_FOUND:
                return None
            raise _convert_github_exception(e) from e

    # ── ConversationProvider implementation ──────────────────────────

    @with_retry
    def post_question_comment(
        self,
        repo_name: str,
        mr_id: int,
        questions: Sequence[BotQuestion],
        *,
        intro: str = "",
    ) -> str:
        """Post a comment with structured bot questions.

        Creates an issue comment with the bot question marker so it can
        be found later by :meth:`get_bot_threads`.

        Note:
            GitHub issue comments have no native threading. Responses
            are identified by temporal ordering (comments posted after
            the question comment by non-bot users).

        Args:
            repo_name: Repository name in 'owner/repo' format.
            mr_id: Pull request number.
            questions: Questions to post.
            intro: Optional introductory text.

        Returns:
            The issue comment ID as a string.
        """
        try:
            body = format_questions_markdown(questions, intro)
            repo = self.github.get_repo(repo_name)
            pr = repo.get_pull(mr_id)
            comment = pr.create_issue_comment(body)
            logger.info("Posted question comment to PR #%s in %s", mr_id, repo_name)
            return str(comment.id)
        except RateLimitExceededException as e:
            msg = f"GitHub: {e}"
            raise RateLimitError(msg) from e
        except GithubException as e:
            raise _convert_github_exception(e) from e

    @with_retry
    def reply_in_thread(
        self,
        repo_name: str,
        mr_id: int,
        thread_id: str,
        body: str,
    ) -> str:
        """Reply in an existing conversation thread.

        Note:
            GitHub issue comments do not support native threading.
            This creates a new issue comment on the PR. For review
            comment threads, use the review API instead.

        Args:
            repo_name: Repository name in 'owner/repo' format.
            mr_id: Pull request number.
            thread_id: Comment ID to reply to (used for context only).
            body: Reply text (markdown supported).

        Returns:
            The new comment ID as a string.
        """
        try:
            repo = self.github.get_repo(repo_name)
            pr = repo.get_pull(mr_id)
            comment = pr.create_issue_comment(body)
            logger.info("Posted reply to PR #%s in %s (thread %s)", mr_id, repo_name, thread_id)
            return str(comment.id)
        except RateLimitExceededException as e:
            msg = f"GitHub: {e}"
            raise RateLimitError(msg) from e
        except GithubException as e:
            raise _convert_github_exception(e) from e

    @with_retry
    def get_bot_threads(
        self,
        repo_name: str,
        mr_id: int,
    ) -> tuple[BotThread, ...]:
        """Find all bot-initiated question threads on the PR.

        Scans issue comments in a single pass: identifies bot question
        comments (by marker), then collects subsequent non-bot comments
        as responses.

        Args:
            repo_name: Repository name in 'owner/repo' format.
            mr_id: Pull request number.

        Returns:
            Tuple of BotThread objects with questions and responses.
        """
        try:
            repo = self.github.get_repo(repo_name)
            pr = repo.get_pull(mr_id)

            # Single pass: collect all comments, then group
            all_comments = list(pr.get_issue_comments())

            threads: list[BotThread] = []
            for idx, issue_comment in enumerate(all_comments):
                if BOT_QUESTION_MARKER not in (issue_comment.body or ""):
                    continue

                questions = parse_questions_from_markdown(issue_comment.body)
                if not questions:
                    continue

                bot_login = issue_comment.user.login
                bot_time = issue_comment.created_at

                # Responses: comments after bot's, not from bot
                responses: list[Comment] = []
                for later_comment in all_comments[idx + 1 :]:
                    if later_comment.user.login == bot_login:
                        continue
                    if later_comment.created_at <= bot_time:
                        continue
                    responses.append(
                        Comment(
                            author=later_comment.user.login,
                            author_type=(
                                CommentAuthorType.BOT
                                if later_comment.user.type == "Bot"
                                else CommentAuthorType.USER
                            ),
                            body=later_comment.body,
                            type=CommentType.ISSUE,
                            created_at=later_comment.created_at,
                            comment_id=str(later_comment.id),
                        )
                    )

                comment_id = str(issue_comment.id)
                status = ThreadStatus.ANSWERED if responses else ThreadStatus.PENDING
                threads.append(
                    BotThread(
                        thread_id=comment_id,
                        platform_thread_id=comment_id,
                        mr_id=mr_id,
                        questions=tuple(questions),
                        responses=tuple(responses),
                        status=status,
                    )
                )

            return tuple(threads)
        except RateLimitExceededException as e:
            msg = f"GitHub: {e}"
            raise RateLimitError(msg) from e
        except GithubException as e:
            raise _convert_github_exception(e) from e

    # Backward compatibility alias
    def post_review_comment(self, repo_name: str, pr_number: int, comment: str) -> None:
        """Post a comment to the pull request (deprecated alias).

        This method is kept for backward compatibility.
        Use post_comment() instead.

        Args:
            repo_name: Repository name in 'owner/repo' format.
            pr_number: Pull request number.
            comment: The comment text to post.
        """
        return self.post_comment(repo_name, pr_number, comment)
