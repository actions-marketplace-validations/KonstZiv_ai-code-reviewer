"""Unit tests for prompt engineering."""

from unittest.mock import Mock

import pytest

from ai_reviewer.core.config import LanguageMode, Settings
from ai_reviewer.core.models import (
    FileChange,
    FileChangeType,
    LinkedTask,
    MergeRequest,
    ReviewContext,
)
from ai_reviewer.integrations.prompts import build_review_prompt


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
