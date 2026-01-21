"""Main reviewer logic for AI Code Reviewer.

This module orchestrates the entire review process:
1. Fetching data from GitHub
2. Analyzing code with Gemini
3. Formatting and posting results
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ai_reviewer.core.formatter import format_review_comment
from ai_reviewer.core.models import CommentAuthorType, ReviewContext
from ai_reviewer.integrations.gemini import analyze_code_changes
from ai_reviewer.integrations.github import GitHubClient

if TYPE_CHECKING:
    from ai_reviewer.core.config import Settings

logger = logging.getLogger(__name__)


def review_pull_request(repo_name: str, pr_number: int, settings: Settings) -> None:
    """Perform a full AI code review on a pull request.

    Args:
        repo_name: Repository name in 'owner/repo' format.
        pr_number: Pull request number.
        settings: Application settings.
    """
    try:
        logger.info("Starting review for PR #%s in %s", pr_number, repo_name)

        # 1. Initialize GitHub client
        github_client = GitHubClient(token=settings.github_token.get_secret_value())

        # 2. Fetch PR data
        mr = github_client.get_pull_request(repo_name, pr_number)
        if not mr:
            logger.error("Could not fetch PR data (likely rate limit exceeded). Aborting.")
            return

        logger.info("Fetched PR: %s", mr.title)

        # 3. Get linked task
        task = github_client.get_linked_task(repo_name, mr)
        if task:
            logger.info("Found linked task: %s", task.identifier)
        else:
            logger.info("No linked task found")

        # 4. Build context
        context = ReviewContext(mr=mr, task=task, repository=repo_name)

        # 5. Analyze with Gemini
        result = analyze_code_changes(context, settings)

        # 6. Format comment
        comment_body = format_review_comment(result)

        # 7. Check for duplicates
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

        # 8. Post comment
        github_client.post_review_comment(repo_name, pr_number, comment_body)
        logger.info("Review completed successfully")

    except Exception as e:
        logger.exception("AI Review failed")
        # Fail Open strategy: Try to post a failure comment, but don't crash the CI hard
        # unless it's a critical configuration error.
        try:
            # Re-initialize client just in case (though reuse is fine)
            # We use a simple client here to avoid circular deps or complex logic
            gh = GitHubClient(token=settings.github_token.get_secret_value())
            error_msg = (
                "## ❌ AI Review Failed\n\n"
                "The AI reviewer encountered an error while processing this PR.\n"
                f"**Error:** `{e!s}`\n\n"
                "_Please check the CI logs for more details._"
            )
            gh.post_review_comment(repo_name, pr_number, error_msg)
        except Exception:
            logger.exception("Failed to post error comment to GitHub")
