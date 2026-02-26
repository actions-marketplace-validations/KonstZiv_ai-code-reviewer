"""Abstract base class for bot conversation capabilities.

This module defines the ``ConversationProvider`` interface for two-way
communication on merge requests: posting structured questions, reading
responses, and replying in threads.

Used by the Discovery engine to ask clarifying questions and by the
orchestrator to track bot-initiated conversations.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from datetime import datetime  # noqa: TC003 — needed at runtime by Pydantic
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from ai_reviewer.core.models import Comment  # noqa: TC001 — needed at runtime by Pydantic

if TYPE_CHECKING:
    from collections.abc import Sequence


class QuestionContext(str, Enum):
    """Context in which a bot question is asked.

    Attributes:
        DISCOVERY: Question asked during project discovery phase.
        REVIEW: Question asked during code review.
        FOLLOW_UP: Follow-up to a previous conversation.
    """

    DISCOVERY = "discovery"
    REVIEW = "review"
    FOLLOW_UP = "follow_up"


class ThreadStatus(str, Enum):
    """Status of a bot conversation thread.

    Attributes:
        PENDING: Questions posted, no responses yet.
        ANSWERED: At least one human response received.
        EXPIRED: Thread is stale (no response within time window).
        RESOLVED: Thread explicitly resolved (GitLab) or considered done.
    """

    PENDING = "pending"
    ANSWERED = "answered"
    EXPIRED = "expired"
    RESOLVED = "resolved"


class BotQuestion(BaseModel):
    """A structured question posted by the bot.

    Each question has a tracking ID (e.g. ``Q1``, ``Q2``) and a default
    assumption that the bot will use if no response is received.

    Attributes:
        question_id: Tracking identifier (e.g. ``Q1``).
        text: The question text.
        default_assumption: What the bot assumes if no answer is given.
        context: Why this question is being asked.
        asked_at: When the question was posted.
    """

    model_config = ConfigDict(frozen=True)

    question_id: str = Field(..., min_length=1, description="Tracking ID (e.g. Q1)")
    text: str = Field(..., min_length=1, description="Question text")
    default_assumption: str = Field(..., min_length=1, description="Default if no response")
    context: QuestionContext = Field(default=QuestionContext.DISCOVERY)
    asked_at: datetime | None = Field(default=None)


class BotThread(BaseModel):
    """A conversation thread initiated by the bot.

    Groups the original questions with any human responses and tracks
    the overall thread status.

    Attributes:
        thread_id: Internal thread identifier.
        platform_thread_id: Platform-specific thread/discussion ID.
        mr_id: Merge request number.
        questions: Questions posted in this thread.
        responses: Human responses collected from this thread.
        status: Current thread status.
    """

    model_config = ConfigDict(frozen=True)

    thread_id: str = Field(..., min_length=1)
    platform_thread_id: str = Field(..., min_length=1)
    mr_id: int = Field(..., ge=1)
    questions: tuple[BotQuestion, ...] = Field(default=())
    responses: tuple[Comment, ...] = Field(default=())
    status: ThreadStatus = Field(default=ThreadStatus.PENDING)


# ── Markdown format for bot questions ──────────────────────────────

BOT_QUESTION_MARKER = "<!-- ai-reviewbot-questions -->"
QUESTION_PATTERN_RE = r"\*\*Q(\d+):\*\*\s*(.+?)\s*\n>\s*\*Default:\s*(.+?)\*"


def format_questions_markdown(
    questions: Sequence[BotQuestion],
    intro: str = "",
) -> str:
    """Format bot questions as a markdown comment.

    Produces a comment body with an HTML marker (for machine detection)
    followed by numbered questions with default assumptions.

    Example output::

        <!-- ai-reviewbot-questions -->
        I have a few questions about this project:

        **Q1:** How do you run tests?
        > *Default: pytest*

    Args:
        questions: Sequence of BotQuestion objects to format.
        intro: Optional introductory text before the questions.

    Returns:
        Formatted markdown string ready for posting.
    """
    parts = [BOT_QUESTION_MARKER]
    if intro:
        parts.append(intro)
        parts.append("")
    for q in questions:
        parts.append(f"**{q.question_id}:** {q.text}")
        parts.append(f"> *Default: {q.default_assumption}*")
        parts.append("")
    return "\n".join(parts)


def parse_questions_from_markdown(body: str) -> list[BotQuestion]:
    """Parse bot questions from a markdown comment body.

    Extracts questions that match the format produced by
    :func:`format_questions_markdown`.

    Args:
        body: The markdown comment body to parse.

    Returns:
        List of BotQuestion objects extracted from the body.
    """
    questions: list[BotQuestion] = []
    for match in re.finditer(QUESTION_PATTERN_RE, body):
        questions.append(
            BotQuestion(
                question_id=f"Q{match.group(1)}",
                text=match.group(2).strip(),
                default_assumption=match.group(3).strip(),
            )
        )
    return questions


class ConversationProvider(ABC):
    """Abstract interface for bot conversation on merge requests.

    Provides two-way communication: posting structured questions,
    reading responses, and replying in threads.
    """

    @abstractmethod
    def post_question_comment(
        self,
        repo_name: str,
        mr_id: int,
        questions: Sequence[BotQuestion],
        *,
        intro: str = "",
    ) -> str:
        """Post a comment with structured bot questions.

        Formats questions using :func:`format_questions_markdown` and
        posts to the merge request.

        Args:
            repo_name: Repository identifier.
            mr_id: Merge/pull request number.
            questions: Questions to post.
            intro: Optional introductory text.

        Returns:
            The comment or discussion ID (platform-specific).
        """

    @abstractmethod
    def reply_in_thread(
        self,
        repo_name: str,
        mr_id: int,
        thread_id: str,
        body: str,
    ) -> str:
        """Reply in an existing conversation thread.

        Args:
            repo_name: Repository identifier.
            mr_id: Merge/pull request number.
            thread_id: Platform-specific thread/discussion ID.
            body: Reply text (markdown supported).

        Returns:
            The new comment ID.
        """

    @abstractmethod
    def get_bot_threads(
        self,
        repo_name: str,
        mr_id: int,
    ) -> tuple[BotThread, ...]:
        """Find all bot-initiated conversation threads.

        Scans merge request comments for the bot question marker,
        collects human responses, and determines thread status.

        Args:
            repo_name: Repository identifier.
            mr_id: Merge/pull request number.

        Returns:
            Tuple of BotThread objects with questions and responses.
        """


__all__ = [
    "BOT_QUESTION_MARKER",
    "BotQuestion",
    "BotThread",
    "ConversationProvider",
    "QuestionContext",
    "ThreadStatus",
    "format_questions_markdown",
    "parse_questions_from_markdown",
]
