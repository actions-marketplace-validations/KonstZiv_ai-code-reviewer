"""Unit tests for prompt engineering."""

from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from ai_reviewer.core.config import LanguageMode, Settings
from ai_reviewer.core.models import (
    Comment,
    CommentAuthorType,
    CommentType,
    FileChange,
    FileChangeType,
    LinkedTask,
    MergeRequest,
    ReviewContext,
)
from ai_reviewer.integrations.prompts import (
    _build_comments_section,
    _format_comment_for_prompt,
    _format_thread_for_prompt,
    _group_comments_into_threads,
    _truncate_comment_body,
    build_review_prompt,
)


class TestBuildReviewPrompt:
    """Tests for build_review_prompt function."""

    @pytest.fixture
    def mock_settings(self) -> Settings:
        """Create mock settings."""
        settings = Mock(spec=Settings)
        settings.review_max_files = 5
        settings.review_max_diff_lines = 10
        settings.language = "en"
        settings.language_mode = LanguageMode.FIXED
        settings.review_max_comment_chars = 3000
        settings.review_include_bot_comments = True
        settings.review_enable_dialogue = True
        return settings

    @pytest.fixture
    def sample_context(self) -> ReviewContext:
        """Create a sample review context."""
        mr = MergeRequest(
            number=1,
            title="Test PR",
            description="PR Description",
            author="dev",
            source_branch="feat",
            target_branch="main",
            changes=(
                FileChange(
                    filename="test.py",
                    change_type=FileChangeType.MODIFIED,
                    patch="line1\nline2\nline3",
                ),
            ),
        )
        task = LinkedTask(
            identifier="123",
            title="Task Title",
            description="Task Description",
        )
        return ReviewContext(mr=mr, task=task, repository="owner/repo")

    def test_full_context(self, sample_context: ReviewContext, mock_settings: Settings) -> None:
        """Test prompt generation with full context."""
        prompt = build_review_prompt(sample_context, mock_settings)

        # Language instruction should be first
        assert "## Language" in prompt
        assert "Respond in en language" in prompt
        assert "## Linked Task" in prompt
        assert "Title: Task Title" in prompt
        assert "Task Description" in prompt
        assert "## Merge Request" in prompt
        assert "Title: Test PR" in prompt
        assert "PR Description" in prompt
        assert "## Code Changes" in prompt
        assert "File: test.py" in prompt
        assert "line1" in prompt

    def test_no_task_context(self, sample_context: ReviewContext, mock_settings: Settings) -> None:
        """Test prompt generation without linked task."""
        # Create context without task using model_copy if possible, or new instance
        mr = sample_context.mr
        context = ReviewContext(mr=mr, task=None, repository="owner/repo")

        prompt = build_review_prompt(context, mock_settings)

        assert "## Linked Task" in prompt
        assert "No linked task provided" in prompt
        assert "Title: Task Title" not in prompt

    def test_diff_truncation(self, sample_context: ReviewContext, mock_settings: Settings) -> None:
        """Test that long diffs are truncated."""
        # Create a long patch
        long_patch = "\n".join([f"line{i}" for i in range(20)])
        change = FileChange(
            filename="long.py",
            change_type=FileChangeType.MODIFIED,
            patch=long_patch,
        )

        # Update context with long change
        # Since models are frozen, we create new ones
        mr = MergeRequest(
            number=1, title="T", author="a", source_branch="s", target_branch="t", changes=(change,)
        )
        context = ReviewContext(mr=mr, repository="o/r")

        # Set limit to 5 lines
        mock_settings.review_max_diff_lines = 5

        prompt = build_review_prompt(context, mock_settings)

        assert "line0" in prompt
        assert "line4" in prompt
        assert "line5" not in prompt
        assert "[Diff truncated" in prompt

    def test_file_limit(self, mock_settings: Settings) -> None:
        """Test that file count is limited."""
        # Create 10 changes
        changes = tuple(
            FileChange(
                filename=f"file{i}.py",
                change_type=FileChangeType.ADDED,
                patch="content",
            )
            for i in range(10)
        )

        mr = MergeRequest(
            number=1, title="T", author="a", source_branch="s", target_branch="t", changes=changes
        )
        context = ReviewContext(mr=mr, repository="o/r")

        # Set limit to 3 files
        mock_settings.review_max_files = 3

        prompt = build_review_prompt(context, mock_settings)

        assert "File: file0.py" in prompt
        assert "File: file2.py" in prompt
        assert "File: file3.py" not in prompt
        assert "[Skipped 7 more files" in prompt

    def test_binary_file_handling(self, mock_settings: Settings) -> None:
        """Test handling of files with no patch (binary)."""
        change = FileChange(
            filename="image.png",
            change_type=FileChangeType.ADDED,
            patch=None,
        )

        mr = MergeRequest(
            number=1, title="T", author="a", source_branch="s", target_branch="t", changes=(change,)
        )
        context = ReviewContext(mr=mr, repository="o/r")

        prompt = build_review_prompt(context, mock_settings)

        assert "File: image.png" in prompt
        assert "[Binary or large file - content skipped]" in prompt

    def test_prompt_includes_comments_section(self, mock_settings: Settings) -> None:
        """Test that comments are included in the prompt."""
        now = datetime.now(tz=UTC)
        comments = (
            Comment(
                author="user1",
                body="Looks good overall",
                type=CommentType.ISSUE,
                created_at=now,
            ),
        )
        mr = MergeRequest(
            number=1,
            title="T",
            author="a",
            source_branch="s",
            target_branch="t",
            comments=comments,
        )
        context = ReviewContext(mr=mr, repository="o/r")

        prompt = build_review_prompt(context, mock_settings)

        assert "## Existing Discussion" in prompt
        assert "DO NOT repeat" in prompt
        assert "@user1" in prompt
        assert "Looks good overall" in prompt

    def test_prompt_no_comments_section_when_no_comments(self, mock_settings: Settings) -> None:
        """Test that no comments section appears when MR has no comments."""
        mr = MergeRequest(
            number=1,
            title="T",
            author="a",
            source_branch="s",
            target_branch="t",
        )
        context = ReviewContext(mr=mr, repository="o/r")

        prompt = build_review_prompt(context, mock_settings)

        assert "## Existing Discussion" not in prompt

    def test_prompt_no_comments_section_when_disabled(self, mock_settings: Settings) -> None:
        """Test that comments are omitted when max_comment_chars is 0."""
        comments = (Comment(author="user1", body="Hello", type=CommentType.ISSUE),)
        mr = MergeRequest(
            number=1,
            title="T",
            author="a",
            source_branch="s",
            target_branch="t",
            comments=comments,
        )
        context = ReviewContext(mr=mr, repository="o/r")
        mock_settings.review_max_comment_chars = 0

        prompt = build_review_prompt(context, mock_settings)

        assert "## Existing Discussion" not in prompt

    def test_prompt_comments_between_mr_and_code(self, mock_settings: Settings) -> None:
        """Test that comments section appears between MR and Code Changes."""
        now = datetime.now(tz=UTC)
        comments = (
            Comment(author="user1", body="Comment", type=CommentType.ISSUE, created_at=now),
        )
        changes = (
            FileChange(filename="test.py", change_type=FileChangeType.MODIFIED, patch="diff"),
        )
        mr = MergeRequest(
            number=1,
            title="T",
            author="a",
            source_branch="s",
            target_branch="t",
            comments=comments,
            changes=changes,
        )
        context = ReviewContext(mr=mr, repository="o/r")

        prompt = build_review_prompt(context, mock_settings)

        mr_pos = prompt.index("## Merge Request")
        discussion_pos = prompt.index("## Existing Discussion")
        code_pos = prompt.index("## Code Changes")
        assert mr_pos < discussion_pos < code_pos


class TestTruncateCommentBody:
    """Tests for _truncate_comment_body helper."""

    def test_short_body_unchanged(self) -> None:
        """Test that short body is returned as-is."""
        assert _truncate_comment_body("Hello world") == "Hello world"

    def test_long_body_truncated(self) -> None:
        """Test that long body is truncated with ellipsis."""
        body = "word " * 200  # ~1000 chars
        result = _truncate_comment_body(body, max_chars=50)
        assert len(result) <= 50
        assert result.endswith("...")

    def test_whitespace_normalized(self) -> None:
        """Test that extra whitespace is normalized."""
        body = "line1\n\n  line2\t\tline3"
        result = _truncate_comment_body(body)
        assert result == "line1 line2 line3"

    def test_exact_length_not_truncated(self) -> None:
        """Test body at exactly max_chars is not truncated."""
        body = "x" * 500
        result = _truncate_comment_body(body, max_chars=500)
        assert result == body
        assert "..." not in result


class TestFormatCommentForPrompt:
    """Tests for _format_comment_for_prompt helper."""

    def test_user_comment_basic(self) -> None:
        """Test formatting a basic user comment."""
        comment = Comment(author="user1", body="LGTM", type=CommentType.ISSUE)
        result = _format_comment_for_prompt(comment)
        assert result.startswith("- @user1")
        assert "LGTM" in result
        assert "[BOT]" not in result

    def test_bot_comment_has_prefix(self) -> None:
        """Test that bot comments get [BOT] prefix."""
        comment = Comment(
            author="ai-bot",
            author_type=CommentAuthorType.BOT,
            body="Auto review",
            type=CommentType.REVIEW,
        )
        result = _format_comment_for_prompt(comment)
        assert "[BOT]" in result
        assert "@ai-bot" in result

    def test_timestamp_included(self) -> None:
        """Test that timestamp is included when available."""
        dt = datetime(2024, 1, 15, 10, 30, tzinfo=UTC)
        comment = Comment(
            author="user1",
            body="Test",
            type=CommentType.ISSUE,
            created_at=dt,
        )
        result = _format_comment_for_prompt(comment)
        assert "[2024-01-15 10:30]" in result

    def test_file_and_line_included(self) -> None:
        """Test that file_path and line_number are included."""
        comment = Comment(
            author="user1",
            body="Fix this",
            type=CommentType.REVIEW,
            file_path="src/main.py",
            line_number=42,
        )
        result = _format_comment_for_prompt(comment)
        assert "(at src/main.py:42)" in result

    def test_file_without_line(self) -> None:
        """Test that file_path without line_number shows file only."""
        comment = Comment(
            author="user1",
            body="Check this file",
            type=CommentType.REVIEW,
            file_path="src/main.py",
        )
        result = _format_comment_for_prompt(comment)
        assert "(at src/main.py)" in result
        assert ":" not in result.split("(at ")[1].split(")")[0]


class TestBuildCommentsSection:
    """Tests for _build_comments_section helper."""

    def test_empty_comments_returns_none(self) -> None:
        """Test that empty comments returns None."""
        assert _build_comments_section((), 3000, True) is None

    def test_zero_max_chars_returns_none(self) -> None:
        """Test that max_total_chars=0 disables comments."""
        comments = (Comment(author="user1", body="Hello", type=CommentType.ISSUE),)
        assert _build_comments_section(comments, 0, True) is None

    def test_general_comments_section(self) -> None:
        """Test general discussion section."""
        dt = datetime(2024, 1, 15, 10, 0, tzinfo=UTC)
        comments = (
            Comment(author="user1", body="LGTM", type=CommentType.ISSUE, created_at=dt),
            Comment(author="user2", body="Needs work", type=CommentType.ISSUE, created_at=dt),
        )
        result = _build_comments_section(comments, 3000, True)
        assert result is not None
        assert "### General Discussion" in result
        assert "@user1" in result
        assert "@user2" in result

    def test_inline_comments_grouped_by_file(self) -> None:
        """Test inline comments are grouped by file."""
        dt = datetime(2024, 1, 15, 10, 0, tzinfo=UTC)
        comments = (
            Comment(
                author="user1",
                body="Fix A",
                type=CommentType.REVIEW,
                file_path="src/a.py",
                line_number=10,
                created_at=dt,
            ),
            Comment(
                author="user2",
                body="Fix B",
                type=CommentType.REVIEW,
                file_path="src/b.py",
                line_number=20,
                created_at=dt,
            ),
            Comment(
                author="user1",
                body="Also fix A",
                type=CommentType.REVIEW,
                file_path="src/a.py",
                line_number=15,
                created_at=dt,
            ),
        )
        result = _build_comments_section(comments, 3000, True)
        assert result is not None
        assert "### Inline Code Discussion" in result
        assert "**src/a.py:**" in result
        assert "**src/b.py:**" in result

    def test_bot_comments_filtered_when_disabled(self) -> None:
        """Test that bot comments are filtered out when include_bot=False."""
        comments = (
            Comment(
                author="bot",
                author_type=CommentAuthorType.BOT,
                body="Auto review",
                type=CommentType.ISSUE,
            ),
        )
        result = _build_comments_section(comments, 3000, include_bot=False)
        assert result is None

    def test_bot_comments_included_when_enabled(self) -> None:
        """Test that bot comments are included when include_bot=True."""
        comments = (
            Comment(
                author="bot",
                author_type=CommentAuthorType.BOT,
                body="Auto review",
                type=CommentType.ISSUE,
            ),
        )
        result = _build_comments_section(comments, 3000, include_bot=True)
        assert result is not None
        assert "[BOT]" in result

    def test_truncation_drops_comments(self) -> None:
        """Test that comments exceeding budget are omitted."""
        dt = datetime(2024, 1, 15, 10, 0, tzinfo=UTC)
        comments = tuple(
            Comment(
                author=f"user{i}",
                body=f"Comment {'x' * 100}",
                type=CommentType.ISSUE,
                created_at=dt,
            )
            for i in range(20)
        )
        result = _build_comments_section(comments, max_total_chars=300, include_bot=True)
        assert result is not None
        assert "older comments omitted" in result

    def test_header_present(self) -> None:
        """Test that the section has proper header."""
        comments = (Comment(author="user1", body="Hello", type=CommentType.ISSUE),)
        result = _build_comments_section(comments, 3000, True)
        assert result is not None
        assert "## Existing Discussion" in result
        assert "DO NOT repeat" in result

    def test_mixed_general_and_inline(self) -> None:
        """Test section with both general and inline comments."""
        dt = datetime(2024, 1, 15, 10, 0, tzinfo=UTC)
        comments = (
            Comment(author="user1", body="General", type=CommentType.ISSUE, created_at=dt),
            Comment(
                author="user2",
                body="Inline",
                type=CommentType.REVIEW,
                file_path="src/main.py",
                line_number=5,
                created_at=dt,
            ),
        )
        result = _build_comments_section(comments, 3000, True)
        assert result is not None
        assert "### General Discussion" in result
        assert "### Inline Code Discussion" in result


class TestGroupCommentsIntoThreads:
    """Tests for _group_comments_into_threads."""

    def test_empty_list(self) -> None:
        """Test grouping empty list returns empty list."""
        result = _group_comments_into_threads([])
        assert result == []

    def test_no_thread_ids_each_standalone(self) -> None:
        """Test comments without thread_id become standalone threads."""
        c1 = Comment(author="u1", body="A", type=CommentType.ISSUE)
        c2 = Comment(author="u2", body="B", type=CommentType.ISSUE)
        result = _group_comments_into_threads([c1, c2])
        assert len(result) == 2
        assert all(len(t) == 1 for t in result)

    def test_comments_grouped_by_thread_id(self) -> None:
        """Test comments with same thread_id are grouped and sorted."""
        dt1 = datetime(2024, 1, 15, 10, 0, tzinfo=UTC)
        dt2 = datetime(2024, 1, 15, 11, 0, tzinfo=UTC)
        c1 = Comment(
            author="u1",
            body="Root",
            type=CommentType.REVIEW,
            comment_id="1",
            thread_id="1",
            created_at=dt1,
        )
        c2 = Comment(
            author="u2",
            body="Reply",
            type=CommentType.REVIEW,
            comment_id="2",
            parent_comment_id="1",
            thread_id="1",
            created_at=dt2,
        )
        # Intentionally reversed
        result = _group_comments_into_threads([c2, c1])
        assert len(result) == 1
        assert result[0][0].body == "Root"
        assert result[0][1].body == "Reply"

    def test_multiple_threads_sorted_by_root_time(self) -> None:
        """Test threads are sorted by root comment time."""
        dt1 = datetime(2024, 1, 15, 10, 0, tzinfo=UTC)
        dt2 = datetime(2024, 1, 15, 9, 0, tzinfo=UTC)
        c1 = Comment(
            author="u1",
            body="Thread A",
            type=CommentType.ISSUE,
            thread_id="A",
            created_at=dt1,
        )
        c2 = Comment(
            author="u2",
            body="Thread B",
            type=CommentType.ISSUE,
            thread_id="B",
            created_at=dt2,
        )
        result = _group_comments_into_threads([c1, c2])
        assert result[0][0].thread_id == "B"  # earlier thread first


class TestFormatThreadForPrompt:
    """Tests for _format_thread_for_prompt."""

    def test_single_comment_thread(self) -> None:
        """Test formatting a single-comment thread."""
        c = Comment(
            author="u1",
            body="Hello",
            type=CommentType.ISSUE,
            thread_id="1",
        )
        lines, omitted, _used = _format_thread_for_prompt([c], 0, 3000)
        assert len(lines) == 1
        assert lines[0].startswith("- @u1")
        assert omitted == 0

    def test_replies_indented(self) -> None:
        """Test that replies are indented with '  > '."""
        root = Comment(
            author="u1",
            body="Root",
            type=CommentType.ISSUE,
            comment_id="1",
            thread_id="1",
        )
        reply = Comment(
            author="u2",
            body="Reply",
            type=CommentType.ISSUE,
            comment_id="2",
            parent_comment_id="1",
            thread_id="1",
        )
        lines, _omitted, _used = _format_thread_for_prompt([root, reply], 0, 3000)
        assert len(lines) == 2
        assert lines[0].startswith("- @u1")
        assert lines[1].startswith("  > @u2")

    def test_budget_overflow_omits_replies(self) -> None:
        """Test that budget overflow omits comments."""
        root = Comment(
            author="u1",
            body="x" * 100,
            type=CommentType.ISSUE,
            thread_id="1",
        )
        reply = Comment(
            author="u2",
            body="y" * 100,
            type=CommentType.ISSUE,
            thread_id="1",
        )
        _lines, omitted, _used = _format_thread_for_prompt([root, reply], 0, 150)
        assert omitted >= 1


class TestBuildCommentsSectionThreaded:
    """Tests for _build_comments_section with dialogue enabled/disabled."""

    def test_threaded_rendering_groups_replies(self) -> None:
        """Test threaded rendering shows indented replies."""
        dt1 = datetime(2024, 1, 15, 10, 0, tzinfo=UTC)
        dt2 = datetime(2024, 1, 15, 11, 0, tzinfo=UTC)
        comments = (
            Comment(
                author="u1",
                body="Root",
                type=CommentType.ISSUE,
                comment_id="1",
                thread_id="1",
                created_at=dt1,
            ),
            Comment(
                author="u2",
                body="Reply",
                type=CommentType.ISSUE,
                comment_id="2",
                parent_comment_id="1",
                thread_id="1",
                created_at=dt2,
            ),
        )
        result = _build_comments_section(
            comments,
            3000,
            True,
            enable_dialogue=True,
        )
        assert result is not None
        assert "  > @u2" in result

    def test_flat_rendering_when_dialogue_disabled(self) -> None:
        """Test flat rendering when dialogue is disabled."""
        dt1 = datetime(2024, 1, 15, 10, 0, tzinfo=UTC)
        comments = (
            Comment(
                author="u1",
                body="Root",
                type=CommentType.ISSUE,
                comment_id="1",
                thread_id="1",
                created_at=dt1,
            ),
        )
        result = _build_comments_section(
            comments,
            3000,
            True,
            enable_dialogue=False,
        )
        assert result is not None
        assert "  >" not in result

    def test_inline_threaded_grouped_by_file(self) -> None:
        """Test inline threaded comments are grouped by file."""
        dt = datetime(2024, 1, 15, 10, 0, tzinfo=UTC)
        dt2 = datetime(2024, 1, 15, 11, 0, tzinfo=UTC)
        comments = (
            Comment(
                author="u1",
                body="Fix",
                type=CommentType.REVIEW,
                file_path="a.py",
                line_number=10,
                comment_id="1",
                thread_id="t1",
                created_at=dt,
            ),
            Comment(
                author="u2",
                body="Done",
                type=CommentType.REVIEW,
                file_path="a.py",
                line_number=10,
                comment_id="2",
                parent_comment_id="1",
                thread_id="t1",
                created_at=dt2,
            ),
        )
        result = _build_comments_section(
            comments,
            3000,
            True,
            enable_dialogue=True,
        )
        assert result is not None
        assert "**a.py:**" in result
        assert "  > @u2" in result
