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

from ai_reviewer.core.formatter import format_review_comment
from ai_reviewer.core.models import CommentAuthorType, ReviewContext
from ai_reviewer.integrations.gemini import analyze_code_changes

if TYPE_CHECKING:
    from ai_reviewer.core.config import Settings
    from ai_reviewer.integrations.base import GitProvider

logger = logging.getLogger(__name__)


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

        # 5. Format comment (pass detected language for Russian disclaimer)
        comment_body = format_review_comment(result, language=result.detected_language)

        # 6. Check for duplicates
        # We check the last comment by a bot. If it matches our new comment, we skip.
        # Note: This assumes we are the only bot or we want to avoid repeating
        # any bot's identical comment.
        # Ideally, we should check if the author is US, but we don't know our own
        # username easily via API without an extra call.
        # Checking CommentAuthorType.BOT is a reasonable proxy for MVP.

        last_bot_comment = None
        for comment in reversed(mr.comments):
            if comment.author_type == CommentAuthorType.BOT:
                last_bot_comment = comment
                break

        if last_bot_comment and last_bot_comment.body.strip() == comment_body.strip():
            logger.info("Duplicate comment detected. Skipping publication.")
            return

        # 7. Post comment
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
