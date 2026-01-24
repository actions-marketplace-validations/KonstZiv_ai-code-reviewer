"""Unit tests for language detection utilities."""

# ruff: noqa: RUF001
import os
from unittest.mock import patch

import pytest

from ai_reviewer.core.config import Settings
from ai_reviewer.core.models import (
    Comment,
    CommentType,
    LinkedTask,
    MergeRequest,
    ReviewContext,
)
from ai_reviewer.utils.language import (
    MIN_WORDS_FOR_DETECTION,
    build_language_instruction,
    collect_text_samples,
    get_language_for_review,
)


@pytest.fixture
def minimal_env() -> dict[str, str]:
    """Return minimal required environment variables."""
    return {
        "GITHUB_TOKEN": "ghp_test_token_12345",
        "GOOGLE_API_KEY": "AIza_test_key_12345",
    }


@pytest.fixture
def settings_adaptive(minimal_env: dict[str, str]) -> Settings:
    """Create settings with ADAPTIVE language mode."""
    with patch.dict(os.environ, {**minimal_env, "LANGUAGE_MODE": "adaptive", "LANGUAGE": "en"}):
        from ai_reviewer.core.config import clear_settings_cache

        clear_settings_cache()
        return Settings()


@pytest.fixture
def settings_fixed_uk(minimal_env: dict[str, str]) -> Settings:
    """Create settings with FIXED language mode and Ukrainian."""
    with patch.dict(os.environ, {**minimal_env, "LANGUAGE_MODE": "fixed", "LANGUAGE": "uk"}):
        from ai_reviewer.core.config import clear_settings_cache

        clear_settings_cache()
        return Settings()


@pytest.fixture
def simple_mr() -> MergeRequest:
    """Create a simple MR with short description."""
    return MergeRequest(
        number=1,
        title="Fix bug",
        description="Short desc",
        author="dev",
        source_branch="fix",
        target_branch="main",
    )


@pytest.fixture
def mr_with_long_description() -> MergeRequest:
    """Create an MR with long Ukrainian description."""
    long_desc = (
        "Цей PR виправляє критичну помилку в модулі аутентифікації. "
        "Проблема полягала в тому, що токени не валідувались правильно. "
        "Тепер всі токени перевіряються на термін дії та підпис. "
        "Додано також логування для відстеження помилок автентифікації."
    )
    return MergeRequest(
        number=1,
        title="Fix auth",
        description=long_desc,
        author="dev",
        source_branch="fix",
        target_branch="main",
    )


@pytest.fixture
def mr_with_comments() -> MergeRequest:
    """Create an MR with comments in different languages."""
    short_comment = Comment(
        author="user1",
        body="LGTM",
        type=CommentType.ISSUE,
    )
    long_uk_comment = Comment(
        author="user2",
        body=(
            "Дякую за PR! Я переглянув код і маю кілька зауважень. "
            "По-перше, варто додати обробку помилок у функції authenticate. "
            "По-друге, потрібно оновити документацію для нових методів."
        ),
        type=CommentType.ISSUE,
    )
    long_en_comment = Comment(
        author="user3",
        body=(
            "This looks good overall. I have reviewed the changes and they seem solid. "
            "However, I would suggest adding some unit tests for the new functionality. "
            "Also, please update the README with the new configuration options."
        ),
        type=CommentType.ISSUE,
    )
    return MergeRequest(
        number=1,
        title="Feature",
        description="Short",
        author="dev",
        source_branch="feature",
        target_branch="main",
        comments=(short_comment, long_uk_comment, long_en_comment),
    )


class TestCollectTextSamples:
    """Tests for collect_text_samples function."""

    def test_empty_context_returns_empty(self, simple_mr: MergeRequest) -> None:
        """Test that context with short texts returns empty samples."""
        context = ReviewContext(mr=simple_mr, repository="owner/repo")
        samples = collect_text_samples(context)
        assert samples == ()

    def test_collects_long_mr_description(self, mr_with_long_description: MergeRequest) -> None:
        """Test that long MR description is collected."""
        context = ReviewContext(mr=mr_with_long_description, repository="owner/repo")
        samples = collect_text_samples(context)
        assert len(samples) == 1
        assert "критичну помилку" in samples[0]

    def test_collects_comments_most_recent_first(self, mr_with_comments: MergeRequest) -> None:
        """Test that comments are collected with most recent first."""
        context = ReviewContext(mr=mr_with_comments, repository="owner/repo")
        samples = collect_text_samples(context)
        # Should have 2 long comments (short "LGTM" is filtered out)
        assert len(samples) == 2
        # Most recent (English) should be first
        assert "This looks good overall" in samples[0]
        # Ukrainian should be second
        assert "Дякую за PR" in samples[1]

    def test_collects_task_description(self, simple_mr: MergeRequest) -> None:
        """Test that linked task description is collected."""
        long_task_desc = (
            "Implement user authentication with JWT tokens. "
            "The system should validate tokens on each request. "
            "Include proper error handling and logging for security events."
        )
        task = LinkedTask(
            identifier="123",
            title="Auth feature",
            description=long_task_desc,
        )
        context = ReviewContext(mr=simple_mr, task=task, repository="owner/repo")
        samples = collect_text_samples(context)
        assert len(samples) == 1
        assert "JWT tokens" in samples[0]

    def test_order_comments_mr_task(self, mr_with_long_description: MergeRequest) -> None:
        """Test the order: comments first, then MR, then task."""
        long_task_desc = (
            "This is the task description with enough words to be substantial. "
            "It describes what needs to be done in detail for the implementation."
        )
        task = LinkedTask(identifier="1", title="Task", description=long_task_desc)

        # Add a long comment (needs 8+ words)
        comment = Comment(
            author="reviewer",
            body=(
                "Great implementation! The code is clean and well-structured. "
                "I especially like the error handling approach you've taken here. "
                "This is exactly what we needed for this feature to work properly."
            ),
            type=CommentType.ISSUE,
        )
        mr = MergeRequest(
            number=1,
            title="Feature",
            description=mr_with_long_description.description,
            author="dev",
            source_branch="feature",
            target_branch="main",
            comments=(comment,),
        )

        context = ReviewContext(mr=mr, task=task, repository="owner/repo")
        samples = collect_text_samples(context)

        assert len(samples) == 3
        # Comment first (most recent)
        assert "Great implementation" in samples[0]
        # MR description second
        assert "критичну помилку" in samples[1]
        # Task description last
        assert "task description" in samples[2]


class TestGetLanguageForReview:
    """Tests for get_language_for_review function."""

    def test_fixed_mode_returns_configured_language(
        self, settings_fixed_uk: Settings, simple_mr: MergeRequest
    ) -> None:
        """Test that FIXED mode always returns configured language."""
        context = ReviewContext(mr=simple_mr, repository="owner/repo")
        lang = get_language_for_review(context, settings_fixed_uk)
        assert lang == "uk"

    def test_adaptive_mode_no_samples_returns_fallback(
        self, settings_adaptive: Settings, simple_mr: MergeRequest
    ) -> None:
        """Test that ADAPTIVE mode with no samples returns fallback."""
        context = ReviewContext(mr=simple_mr, repository="owner/repo")
        lang = get_language_for_review(context, settings_adaptive)
        assert lang == "en"

    def test_adaptive_mode_with_samples_returns_fallback(
        self, settings_adaptive: Settings, mr_with_long_description: MergeRequest
    ) -> None:
        """Test that ADAPTIVE mode with samples still returns fallback hint."""
        context = ReviewContext(mr=mr_with_long_description, repository="owner/repo")
        lang = get_language_for_review(context, settings_adaptive)
        # Returns configured language as fallback hint
        # Actual detection happens in LLM
        assert lang == "en"


class TestBuildLanguageInstruction:
    """Tests for build_language_instruction function."""

    def test_fixed_mode_instruction(
        self, settings_fixed_uk: Settings, simple_mr: MergeRequest
    ) -> None:
        """Test instruction for FIXED mode."""
        context = ReviewContext(mr=simple_mr, repository="owner/repo")
        instruction = build_language_instruction(context, settings_fixed_uk)
        assert "Respond in uk language" in instruction
        assert "must be written in uk" in instruction

    def test_adaptive_mode_no_context(
        self, settings_adaptive: Settings, simple_mr: MergeRequest
    ) -> None:
        """Test instruction for ADAPTIVE mode without substantial context."""
        context = ReviewContext(mr=simple_mr, repository="owner/repo")
        instruction = build_language_instruction(context, settings_adaptive)
        # Falls back to configured language
        assert "Respond in en language" in instruction

    def test_adaptive_mode_with_context(
        self, settings_adaptive: Settings, mr_with_long_description: MergeRequest
    ) -> None:
        """Test instruction for ADAPTIVE mode with substantial context."""
        context = ReviewContext(mr=mr_with_long_description, repository="owner/repo")
        instruction = build_language_instruction(context, settings_adaptive)
        assert "Detect the language" in instruction
        assert "Context sample" in instruction
        # Should include part of the Ukrainian description
        assert "критичну помилку" in instruction or "en" in instruction

    def test_adaptive_mode_truncates_long_sample(self, settings_adaptive: Settings) -> None:
        """Test that long samples are truncated in instruction."""
        # Create MR with very long description
        long_desc = "Word " * 200  # 200 words
        mr = MergeRequest(
            number=1,
            title="Test",
            description=long_desc,
            author="dev",
            source_branch="test",
            target_branch="main",
        )
        context = ReviewContext(mr=mr, repository="owner/repo")
        instruction = build_language_instruction(context, settings_adaptive)
        # Should be truncated with "..."
        assert "..." in instruction


class TestMinWordsConstant:
    """Tests for MIN_WORDS_FOR_DETECTION constant."""

    def test_min_words_value(self) -> None:
        """Test that MIN_WORDS_FOR_DETECTION is set to expected value."""
        assert MIN_WORDS_FOR_DETECTION == 8

    def test_text_below_min_not_collected(self, simple_mr: MergeRequest) -> None:
        """Test that text with fewer than MIN_WORDS is not collected."""
        # simple_mr has "Short desc" which is 2 words
        context = ReviewContext(mr=simple_mr, repository="owner/repo")
        samples = collect_text_samples(context)
        assert len(samples) == 0

    def test_text_at_min_is_collected(self) -> None:
        """Test that text with exactly MIN_WORDS is collected."""
        # Create description with exactly MIN_WORDS_FOR_DETECTION words
        desc = " ".join(["word"] * MIN_WORDS_FOR_DETECTION)
        mr = MergeRequest(
            number=1,
            title="Test",
            description=desc,
            author="dev",
            source_branch="test",
            target_branch="main",
        )
        context = ReviewContext(mr=mr, repository="owner/repo")
        samples = collect_text_samples(context)
        assert len(samples) == 1
