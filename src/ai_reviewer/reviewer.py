"""Main reviewer logic for AI Code Reviewer.

This module orchestrates the entire review process:
1. Fetching data from Git provider
2. Analyzing code with AI (Gemini)
3. Formatting and posting results

The reviewer is provider-agnostic and works with any GitProvider implementation.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ai_reviewer.core.formatter import (
    format_inline_comment,
    format_review_comment,
    format_review_summary,
)
from ai_reviewer.core.models import CommentAuthorType, ReviewContext
from ai_reviewer.integrations.base import LineComment, ReviewSubmission
from ai_reviewer.integrations.gemini import analyze_code_changes

if TYPE_CHECKING:
    from ai_reviewer.core.config import Settings
    from ai_reviewer.core.models import CodeIssue, ReviewResult
    from ai_reviewer.integrations.base import GitProvider

logger = logging.getLogger(__name__)


def _build_review_submission(
    result: ReviewResult,
    language: str | None,
) -> ReviewSubmission:
    """Build a ReviewSubmission by partitioning issues into inline and fallback.

    Issues with both file_path and line_number (>= 1) become inline comments.
    Remaining issues are included in the summary body as fallback.

    Args:
        result: The structured review result from AI analysis.
        language: ISO 639 language code for formatting.

    Returns:
        ReviewSubmission with summary and inline line comments.
    """
    inline_issues: list[CodeIssue] = []
    fallback_issues: list[CodeIssue] = []

    for issue in result.issues:
        if issue.file_path and issue.line_number and issue.line_number >= 1:
            inline_issues.append(issue)
        else:
            fallback_issues.append(issue)

    # Build inline line comments
    line_comments: list[LineComment] = []
    for issue in inline_issues:
        body = format_inline_comment(issue, language)
        line_comments.append(
            LineComment(
                path=issue.file_path,  # type: ignore[arg-type]  # guarded above
                line=issue.line_number,  # type: ignore[arg-type]  # guarded above
                body=body,
                suggestion=issue.proposed_code,
            )
        )

    summary = format_review_summary(result, tuple(fallback_issues), language)

    return ReviewSubmission(
        summary=summary,
        line_comments=tuple(line_comments),
    )


def review_pull_request(
    provider: GitProvider,
    repo_name: str,
    mr_id: int,
    settings: Settings,
) -> None:
    """Perform a full AI code review on a pull/merge request.

    This function orchestrates the entire review process using the provided
    Git provider. It is provider-agnostic and works with any GitProvider
    implementation (GitHub, GitLab, etc.).

    Args:
        provider: Git provider instance for API interactions.
        repo_name: Repository identifier (e.g., 'owner/repo' for GitHub).
        mr_id: Merge/Pull request number.
        settings: Application settings.
    """
    try:
        logger.info("Starting review for MR #%s in %s", mr_id, repo_name)

        # 1. Fetch MR data
        mr = provider.get_merge_request(repo_name, mr_id)
        if not mr:
            logger.error("Could not fetch MR data (likely rate limit exceeded). Aborting.")
            return

        logger.info("Fetched MR: %s", mr.title)

        # 2. Get linked task
        task = provider.get_linked_task(repo_name, mr)
        if task:
            logger.info("Found linked task: %s", task.identifier)
        else:
            logger.info("No linked task found")

        # 3. Build context
        context = ReviewContext(mr=mr, task=task, repository=repo_name)

        # 4. Analyze with AI
        result = analyze_code_changes(context, settings)

        # 5. Find last bot comment for duplicate detection
        last_bot_comment = None
        for comment in reversed(mr.comments):
            if comment.author_type == CommentAuthorType.BOT:
                last_bot_comment = comment
                break

        # 6. Post results
        if settings.review_post_inline_comments:
            submission = _build_review_submission(result, result.detected_language)

            # Duplicate detection: compare summary only
            if last_bot_comment and last_bot_comment.body.strip() == submission.summary.strip():
                logger.info("Duplicate summary detected. Skipping publication.")
                return

            provider.submit_review(repo_name, mr_id, submission)
            logger.info("Review completed successfully (inline comments)")
        else:
            # Legacy behavior: single summary comment via post_comment
            comment_body = format_review_comment(result, language=result.detected_language)

            if last_bot_comment and last_bot_comment.body.strip() == comment_body.strip():
                logger.info("Duplicate comment detected. Skipping publication.")
                return

            provider.post_comment(repo_name, mr_id, comment_body)
            logger.info("Review completed successfully")

    except Exception as e:
        logger.exception("AI Review failed")
        # Fail Open strategy: Try to post a failure comment, but don't crash the CI hard
        # unless it's a critical configuration error.
        _post_error_comment(provider, repo_name, mr_id, e)


def _post_error_comment(
    provider: GitProvider,
    repo_name: str,
    mr_id: int,
    error: Exception,
) -> None:
    """Attempt to post an error comment to the MR.

    Args:
        provider: Git provider instance.
        repo_name: Repository identifier.
        mr_id: Merge/Pull request number.
        error: The exception that caused the failure.
    """
    try:
        error_msg = (
            "## ❌ AI Review Failed\n\n"
            "The AI reviewer encountered an error while processing this PR.\n"
            f"**Error:** `{error!s}`\n\n"
            "_Please check the CI logs for more details._"
        )
        provider.post_comment(repo_name, mr_id, error_msg)
    except Exception:
        logger.exception("Failed to post error comment")
