# Task 1.3: ConversationProvider — Implementation Guide

## Поточний стан

Існуючий код вже частково підтримує:
- `post_comment()` — постить довільний текст
- `submit_review()` — постить inline коментарі
- Comments читаються з threading (thread_id, parent_comment_id)
- `get_linked_task()` — regex "Fixes #123" (один issue)

Але нема: structured questions, response tracking, thread participation, deep task search.

---

## Що створити

### 1. `src/ai_reviewer/integrations/conversation.py`

```python
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict

from ai_reviewer.core.models import Comment, LinkedTask


class QuestionContext(str, Enum):
    DISCOVERY = "discovery"
    REVIEW = "review"
    FOLLOW_UP = "follow_up"


class ThreadStatus(str, Enum):
    PENDING = "pending"
    ANSWERED = "answered"
    EXPIRED = "expired"
    RESOLVED = "resolved"


class BotQuestion(BaseModel):
    """Питання бота з tracking ID і default assumption."""
    model_config = ConfigDict(frozen=True)

    question_id: str                        # "Q1", "Q2"
    text: str
    default_assumption: str
    context: QuestionContext = QuestionContext.DISCOVERY
    asked_at: datetime | None = None


class BotThread(BaseModel):
    """Thread де бот бере участь."""
    model_config = ConfigDict(frozen=True)

    thread_id: str                          # internal
    platform_thread_id: str                 # GitHub/GitLab thread ID
    mr_id: int
    questions: tuple[BotQuestion, ...] = ()
    responses: tuple[Comment, ...] = ()
    status: ThreadStatus = ThreadStatus.PENDING


# --- Формат питань у markdown ---

BOT_QUESTION_MARKER = "<!-- ai-reviewbot-questions -->"
QUESTION_PATTERN_RE = r"\*\*Q(\d+):\*\*\s+(.+?)\n>\s+\*Default:\s*(.+?)\*"


def format_questions_markdown(
    questions: Sequence[BotQuestion],
    intro: str = "",
) -> str:
    """Форматує питання в markdown для MR-коментаря.

    Формат:
        <!-- ai-reviewbot-questions -->
        {intro}

        **Q1:** {text}
        > *Default: {default_assumption}*

        **Q2:** {text}
        > *Default: {default_assumption}*
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
    """Парсить питання з markdown-коментаря бота."""
    import re
    questions = []
    for match in re.finditer(QUESTION_PATTERN_RE, body):
        questions.append(BotQuestion(
            question_id=f"Q{match.group(1)}",
            text=match.group(2).strip(),
            default_assumption=match.group(3).strip(),
        ))
    return questions


class ConversationProvider(ABC):
    """Двостороння комунікація бота на платформі."""

    @abstractmethod
    def post_question_comment(
        self,
        repo_name: str,
        mr_id: int,
        questions: Sequence[BotQuestion],
        *,
        intro: str = "",
    ) -> str:
        """Постити коментар з питаннями. Повертає comment/thread ID."""

    @abstractmethod
    def reply_in_thread(
        self,
        repo_name: str,
        mr_id: int,
        thread_id: str,
        body: str,
    ) -> str:
        """Відповісти в існуючий thread. Повертає comment ID."""

    @abstractmethod
    def get_bot_threads(
        self,
        repo_name: str,
        mr_id: int,
    ) -> tuple[BotThread, ...]:
        """Знайти threads з питаннями бота + відповіді."""

    @abstractmethod
    def get_linked_tasks_deep(
        self,
        repo_name: str,
        mr_id: int,
    ) -> tuple[LinkedTask, ...]:
        """Глибокий пошук linked tasks."""
```

### 2. GitHub реалізація

```python
# Додати до GitHubClient

class GitHubClient(GitProvider, RepositoryProvider, ConversationProvider):

    def post_question_comment(self, repo_name, mr_id, questions, *, intro=""):
        body = format_questions_markdown(questions, intro)
        repo = self._github.get_repo(repo_name)
        pr = repo.get_pull(mr_id)
        comment = pr.create_issue_comment(body)
        return str(comment.id)

    def reply_in_thread(self, repo_name, mr_id, thread_id, body):
        # GitHub issue comments don't have native threading
        # Use @mention or quote for context
        repo = self._github.get_repo(repo_name)
        pr = repo.get_pull(mr_id)
        comment = pr.create_issue_comment(body)
        return str(comment.id)

    def get_bot_threads(self, repo_name, mr_id):
        repo = self._github.get_repo(repo_name)
        pr = repo.get_pull(mr_id)
        threads = []
        bot_comments = []

        # Scan all issue comments for bot question markers
        for comment in pr.get_issue_comments():
            if BOT_QUESTION_MARKER in comment.body:
                questions = parse_questions_from_markdown(comment.body)
                bot_comments.append((comment, questions))

        for comment, questions in bot_comments:
            # Collect replies: comments after bot's, not from bot
            responses = []
            for c in pr.get_issue_comments():
                if c.created_at > comment.created_at and c.user.login != comment.user.login:
                    responses.append(self._comment_to_model(c))

            status = ThreadStatus.ANSWERED if responses else ThreadStatus.PENDING
            threads.append(BotThread(
                thread_id=str(comment.id),
                platform_thread_id=str(comment.id),
                mr_id=mr_id,
                questions=tuple(questions),
                responses=tuple(responses),
                status=status,
            ))
        return tuple(threads)

    def get_linked_tasks_deep(self, repo_name, mr_id):
        """GitHub: regex + timeline events."""
        repo = self._github.get_repo(repo_name)
        pr = repo.get_pull(mr_id)
        tasks = []
        seen_ids = set()

        # 1. Regex in description
        # (reuse existing logic from get_linked_task)
        # ...

        # 2. Timeline events (cross-referenced, connected)
        try:
            for event in pr.get_timeline():
                if event.event in ("cross-referenced", "connected"):
                    issue = getattr(event, "source", {}).get("issue")
                    if issue and issue.get("number") not in seen_ids:
                        seen_ids.add(issue["number"])
                        tasks.append(LinkedTask(
                            identifier=str(issue["number"]),
                            title=issue.get("title", ""),
                            description=issue.get("body", ""),
                            url=issue.get("html_url", ""),
                        ))
        except Exception:
            pass  # Timeline API might not be available

        return tuple(tasks)
```

### 3. GitLab реалізація

```python
# Додати до GitLabClient

class GitLabClient(GitProvider, RepositoryProvider, ConversationProvider):

    def post_question_comment(self, repo_name, mr_id, questions, *, intro=""):
        body = format_questions_markdown(questions, intro)
        project = self.gitlab.projects.get(repo_name)
        mr = project.mergerequests.get(mr_id)
        # GitLab: створити discussion (threading з коробки)
        discussion = mr.discussions.create({"body": body})
        return str(discussion.id)

    def reply_in_thread(self, repo_name, mr_id, thread_id, body):
        project = self.gitlab.projects.get(repo_name)
        mr = project.mergerequests.get(mr_id)
        discussion = mr.discussions.get(thread_id)
        note = discussion.notes.create({"body": body})
        return str(note.id)

    def get_bot_threads(self, repo_name, mr_id):
        project = self.gitlab.projects.get(repo_name)
        mr = project.mergerequests.get(mr_id)
        threads = []

        for discussion in mr.discussions.list(iterator=True):
            notes = discussion.attributes.get("notes", [])
            if not notes:
                continue
            first_note = notes[0]
            body = first_note.get("body", "")
            if BOT_QUESTION_MARKER not in body:
                continue

            questions = parse_questions_from_markdown(body)
            responses = []
            for note in notes[1:]:
                if not note.get("system", False):
                    responses.append(self._note_to_comment(note, discussion.id))

            is_resolved = discussion.attributes.get("resolved", False)
            if is_resolved:
                status = ThreadStatus.RESOLVED
            elif responses:
                status = ThreadStatus.ANSWERED
            else:
                status = ThreadStatus.PENDING

            threads.append(BotThread(
                thread_id=str(discussion.id),
                platform_thread_id=str(discussion.id),
                mr_id=mr_id,
                questions=tuple(questions),
                responses=tuple(responses),
                status=status,
            ))
        return tuple(threads)

    def get_linked_tasks_deep(self, repo_name, mr_id):
        project = self.gitlab.projects.get(repo_name)
        mr = project.mergerequests.get(mr_id)
        tasks = []

        # 1. GitLab closes_issues API
        try:
            for issue in mr.closes_issues():
                tasks.append(LinkedTask(
                    identifier=str(issue.iid),
                    title=issue.title,
                    description=issue.description or "",
                    url=issue.web_url,
                ))
        except Exception:
            pass

        # 2. Regex fallback (reuse existing)
        # ...

        return tuple(tasks)
```

---

## Тести

### `tests/unit/test_conversation_provider.py`

- `format_questions_markdown()` — output formatting
- `parse_questions_from_markdown()` — roundtrip parse
- `get_bot_threads()` — scan, match, collect responses
- `post_question_comment()` — creates comment with marker
- `reply_in_thread()` — GitHub and GitLab specific
- `get_linked_tasks_deep()` — GitHub timeline + regex, GitLab closes_issues

---

## Чеклист

- [ ] `integrations/conversation.py` — ABC + models + format/parse helpers
- [ ] `GitHubClient` extends `ConversationProvider` — 4 methods
- [ ] `GitLabClient` extends `ConversationProvider` — 4 methods
- [ ] Question format: human-readable + machine-parseable
- [ ] Unit-тести
- [ ] `make check` проходить
