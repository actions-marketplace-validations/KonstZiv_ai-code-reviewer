"""Unit tests for core data models."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from ai_reviewer.core.models import (
    CodeIssue,
    Comment,
    CommentAuthorType,
    CommentType,
    FileChange,
    FileChangeType,
    GoodPractice,
    IssueCategory,
    IssueSeverity,
    LinkedTask,
    MergeRequest,
    ReviewContext,
    ReviewMetrics,
    ReviewResult,
    TaskAlignmentStatus,
)


class TestComment:
    """Tests for Comment model."""

    def test_create_minimal_comment(self) -> None:
        """Test creating a comment with minimal required fields."""
        comment = Comment(author="user1", body="LGTM", type=CommentType.ISSUE)
        assert comment.author == "user1"
        assert comment.body == "LGTM"
        assert comment.author_type == CommentAuthorType.USER
        assert comment.type == CommentType.ISSUE
        assert comment.created_at is None

    def test_create_full_comment(self) -> None:
        """Test creating a comment with all fields."""
        now = datetime.now(tz=UTC)
        comment = Comment(
            author="bot",
            author_type=CommentAuthorType.BOT,
            body="Automated review",
            type=CommentType.REVIEW,
            created_at=now,
        )
        assert comment.author == "bot"
        assert comment.author_type == CommentAuthorType.BOT
        assert comment.body == "Automated review"
        assert comment.type == CommentType.REVIEW
        assert comment.created_at == now

    def test_comment_author_required(self) -> None:
        """Test that author field is required."""
        with pytest.raises(ValidationError) as exc_info:
            Comment(body="test", type=CommentType.ISSUE)  # type: ignore[call-arg]
        assert "author" in str(exc_info.value)

    def test_comment_type_required(self) -> None:
        """Test that type field is required."""
        with pytest.raises(ValidationError) as exc_info:
            Comment(author="user", body="test")  # type: ignore[call-arg]
        assert "type" in str(exc_info.value)

    def test_comment_author_not_empty(self) -> None:
        """Test that author cannot be empty."""
        with pytest.raises(ValidationError) as exc_info:
            Comment(author="", body="test", type=CommentType.ISSUE)
        assert "author" in str(exc_info.value)

    def test_comment_is_frozen(self) -> None:
        """Test that comment model is immutable."""
        comment = Comment(author="user", body="test", type=CommentType.ISSUE)
        with pytest.raises(ValidationError):
            comment.body = "modified"  # type: ignore[misc]

    def test_comment_created_at_must_be_timezone_aware(self) -> None:
        """Test that created_at rejects naive datetime."""
        naive_dt = datetime(2026, 1, 20, 12, 0, 0)
        with pytest.raises(ValidationError) as exc_info:
            Comment(author="user", body="test", type=CommentType.ISSUE, created_at=naive_dt)
        assert "timezone-aware" in str(exc_info.value)


class TestFileChange:
    """Tests for FileChange model."""

    def test_create_minimal_file_change(self) -> None:
        """Test creating a file change with minimal fields."""
        change = FileChange(filename="src/main.py", change_type=FileChangeType.MODIFIED)
        assert change.filename == "src/main.py"
        assert change.change_type == FileChangeType.MODIFIED
        assert change.additions == 0
        assert change.deletions == 0
        assert change.patch is None

    def test_create_full_file_change(self) -> None:
        """Test creating a file change with all fields."""
        change = FileChange(
            filename="src/new.py",
            change_type=FileChangeType.ADDED,
            additions=50,
            deletions=0,
            patch="@@ -0,0 +1,50 @@\n+# New file",
        )
        assert change.additions == 50
        assert change.patch is not None

    def test_renamed_file_change(self) -> None:
        """Test file change for renamed file."""
        change = FileChange(
            filename="src/new_name.py",
            change_type=FileChangeType.RENAMED,
            previous_filename="src/old_name.py",
        )
        assert change.change_type == FileChangeType.RENAMED
        assert change.previous_filename == "src/old_name.py"

    def test_filename_required(self) -> None:
        """Test that filename is required."""
        with pytest.raises(ValidationError):
            FileChange(change_type=FileChangeType.ADDED)  # type: ignore[call-arg]

    def test_filename_not_empty(self) -> None:
        """Test that filename cannot be empty."""
        with pytest.raises(ValidationError):
            FileChange(filename="", change_type=FileChangeType.ADDED)

    def test_additions_non_negative(self) -> None:
        """Test that additions must be non-negative."""
        with pytest.raises(ValidationError):
            FileChange(filename="test.py", change_type=FileChangeType.MODIFIED, additions=-1)

    def test_deletions_non_negative(self) -> None:
        """Test that deletions must be non-negative."""
        with pytest.raises(ValidationError):
            FileChange(filename="test.py", change_type=FileChangeType.MODIFIED, deletions=-5)

    def test_previous_filename_empty_string_becomes_none(self) -> None:
        """Test that empty previous_filename is converted to None."""
        change = FileChange(
            filename="test.py",
            change_type=FileChangeType.RENAMED,
            previous_filename="  ",
        )
        assert change.previous_filename is None


class TestMergeRequest:
    """Tests for MergeRequest model."""

    @pytest.fixture
    def minimal_mr(self) -> MergeRequest:
        """Create a minimal merge request for testing."""
        return MergeRequest(
            number=1,
            title="Add new feature",
            author="developer",
            source_branch="feature/new",
            target_branch="main",
        )

    @pytest.fixture
    def full_mr(self) -> MergeRequest:
        """Create a full merge request with all fields."""
        return MergeRequest(
            number=42,
            title="Fix critical bug",
            description="This PR fixes the login issue",
            author="developer",
            source_branch="fix/login",
            target_branch="main",
            comments=(
                Comment(author="reviewer", body="Needs tests", type=CommentType.REVIEW),
                Comment(author="developer", body="Added tests", type=CommentType.ISSUE),
            ),
            changes=(
                FileChange(
                    filename="src/auth.py",
                    change_type=FileChangeType.MODIFIED,
                    additions=20,
                    deletions=5,
                ),
                FileChange(
                    filename="tests/test_auth.py",
                    change_type=FileChangeType.ADDED,
                    additions=50,
                    deletions=0,
                ),
            ),
            url="https://github.com/owner/repo/pull/42",
            created_at=datetime(2026, 1, 15, tzinfo=UTC),
            updated_at=datetime(2026, 1, 20, tzinfo=UTC),
        )

    def test_create_minimal_mr(self, minimal_mr: MergeRequest) -> None:
        """Test creating MR with minimal fields."""
        assert minimal_mr.number == 1
        assert minimal_mr.title == "Add new feature"
        assert minimal_mr.description == ""
        assert minimal_mr.comments == ()
        assert minimal_mr.changes == ()

    def test_create_full_mr(self, full_mr: MergeRequest) -> None:
        """Test creating MR with all fields."""
        assert full_mr.number == 42
        assert len(full_mr.comments) == 2
        assert len(full_mr.changes) == 2
        assert full_mr.comments[0].type == CommentType.REVIEW
        assert full_mr.comments[1].type == CommentType.ISSUE

    def test_total_additions(self, full_mr: MergeRequest) -> None:
        """Test total_additions property."""
        assert full_mr.total_additions == 70  # 20 + 50

    def test_total_deletions(self, full_mr: MergeRequest) -> None:
        """Test total_deletions property."""
        assert full_mr.total_deletions == 5

    def test_files_changed(self, full_mr: MergeRequest) -> None:
        """Test files_changed property."""
        assert full_mr.files_changed == 2

    def test_mr_number_positive(self) -> None:
        """Test that MR number must be positive."""
        with pytest.raises(ValidationError):
            MergeRequest(
                number=0,
                title="Test",
                author="dev",
                source_branch="feature",
                target_branch="main",
            )

    def test_mr_title_required(self) -> None:
        """Test that title is required."""
        with pytest.raises(ValidationError):
            MergeRequest(
                number=1,
                author="dev",
                source_branch="feature",
                target_branch="main",
            )  # type: ignore[call-arg]

    def test_mr_title_not_empty(self) -> None:
        """Test that title cannot be empty."""
        with pytest.raises(ValidationError):
            MergeRequest(
                number=1,
                title="",
                author="dev",
                source_branch="feature",
                target_branch="main",
            )

    def test_mr_is_frozen(self, minimal_mr: MergeRequest) -> None:
        """Test that MR model is immutable."""
        with pytest.raises(ValidationError):
            minimal_mr.title = "Modified"  # type: ignore[misc]

    def test_mr_datetime_must_be_timezone_aware(self) -> None:
        """Test that created_at and updated_at reject naive datetime."""
        naive_dt = datetime(2026, 1, 20, 12, 0, 0)

        with pytest.raises(ValidationError) as exc_info:
            MergeRequest(
                number=1,
                title="Test",
                author="dev",
                source_branch="feature",
                target_branch="main",
                created_at=naive_dt,
            )
        assert "timezone-aware" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            MergeRequest(
                number=1,
                title="Test",
                author="dev",
                source_branch="feature",
                target_branch="main",
                updated_at=naive_dt,
            )
        assert "timezone-aware" in str(exc_info.value)


class TestLinkedTask:
    """Tests for LinkedTask model."""

    def test_create_minimal_task(self) -> None:
        """Test creating a task with minimal fields."""
        task = LinkedTask(identifier="123", title="Implement feature X")
        assert task.identifier == "123"
        assert task.title == "Implement feature X"
        assert task.description == ""
        assert task.url is None

    def test_create_full_task(self) -> None:
        """Test creating a task with all fields."""
        task = LinkedTask(
            identifier="PROJ-456",
            title="Add authentication",
            description="Implement OAuth2 authentication flow",
            url="https://jira.example.com/PROJ-456",
        )
        assert task.identifier == "PROJ-456"
        assert task.url == "https://jira.example.com/PROJ-456"

    def test_task_identifier_required(self) -> None:
        """Test that identifier is required."""
        with pytest.raises(ValidationError):
            LinkedTask(title="Test")  # type: ignore[call-arg]

    def test_task_identifier_not_empty(self) -> None:
        """Test that identifier cannot be empty."""
        with pytest.raises(ValidationError):
            LinkedTask(identifier="", title="Test")


class TestReviewContext:
    """Tests for ReviewContext model."""

    @pytest.fixture
    def sample_mr(self) -> MergeRequest:
        """Create a sample MR for testing."""
        return MergeRequest(
            number=1,
            title="Test PR",
            author="dev",
            source_branch="feature",
            target_branch="main",
        )

    @pytest.fixture
    def sample_task(self) -> LinkedTask:
        """Create a sample task for testing."""
        return LinkedTask(identifier="123", title="Test task")

    def test_create_context_without_task(self, sample_mr: MergeRequest) -> None:
        """Test creating context without linked task."""
        context = ReviewContext(mr=sample_mr, repository="owner/repo")
        assert context.mr == sample_mr
        assert context.task is None
        assert context.repository == "owner/repo"
        assert context.has_linked_task is False

    def test_create_context_with_task(
        self, sample_mr: MergeRequest, sample_task: LinkedTask
    ) -> None:
        """Test creating context with linked task."""
        context = ReviewContext(mr=sample_mr, task=sample_task, repository="owner/repo")
        assert context.task == sample_task
        assert context.has_linked_task is True

    def test_repository_format_valid(self, sample_mr: MergeRequest) -> None:
        """Test that valid repository formats are accepted."""
        context = ReviewContext(mr=sample_mr, repository="owner/repo")
        assert context.repository == "owner/repo"

        context2 = ReviewContext(mr=sample_mr, repository="org-name/repo-name")
        assert context2.repository == "org-name/repo-name"

    def test_repository_format_invalid_no_slash(self, sample_mr: MergeRequest) -> None:
        """Test that repository without slash is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ReviewContext(mr=sample_mr, repository="invalid")
        assert "owner/repo" in str(exc_info.value)

    def test_repository_format_invalid_empty_parts(self, sample_mr: MergeRequest) -> None:
        """Test that repository with empty parts is rejected."""
        with pytest.raises(ValidationError):
            ReviewContext(mr=sample_mr, repository="/repo")

        with pytest.raises(ValidationError):
            ReviewContext(mr=sample_mr, repository="owner/")

    def test_repository_format_invalid_multiple_slashes(self, sample_mr: MergeRequest) -> None:
        """Test that repository with multiple slashes is rejected."""
        with pytest.raises(ValidationError):
            ReviewContext(mr=sample_mr, repository="owner/repo/extra")


class TestCodeIssue:
    """Tests for CodeIssue model."""

    def test_create_minimal_issue(self) -> None:
        """Test creating an issue with minimal fields."""
        issue = CodeIssue(
            category=IssueCategory.SECURITY,
            severity=IssueSeverity.CRITICAL,
            title="SQL Injection",
            description="User input not sanitized",
        )
        assert issue.title == "SQL Injection"
        assert issue.severity == IssueSeverity.CRITICAL
        assert issue.category == IssueCategory.SECURITY
        assert issue.file_path is None
        assert issue.line_number is None
        assert issue.has_suggestion is False
        assert issue.is_critical is True
        assert issue.is_security is True

    def test_create_full_issue(self) -> None:
        """Test creating an issue with all fields."""
        issue = CodeIssue(
            category=IssueCategory.CODE_QUALITY,
            severity=IssueSeverity.WARNING,
            title="Unused variable",
            description="Variable 'x' is declared but never used",
            file_path="src/utils.py",
            line_number=42,
            existing_code="x = 5",
            proposed_code="# removed unused variable",
            why_matters="Unused variables clutter the code and can indicate bugs",
            learn_more_url="https://pylint.pycqa.org/en/latest/user_guide/messages/warning/unused-variable.html",
        )
        assert issue.file_path == "src/utils.py"
        assert issue.line_number == 42
        assert issue.has_suggestion is True
        assert issue.is_critical is False
        assert issue.is_security is False

    def test_issue_line_must_be_positive(self) -> None:
        """Test that line number must be positive."""
        with pytest.raises(ValidationError):
            CodeIssue(
                category=IssueCategory.SECURITY,
                severity=IssueSeverity.CRITICAL,
                title="Test",
                description="Test",
                line_number=0,
            )

    def test_all_severity_levels(self) -> None:
        """Test all issue severity levels."""
        for severity in IssueSeverity:
            issue = CodeIssue(
                category=IssueCategory.CODE_QUALITY,
                severity=severity,
                title="Test",
                description="Test",
            )
            assert issue.severity == severity

    def test_all_categories(self) -> None:
        """Test all issue categories."""
        for category in IssueCategory:
            issue = CodeIssue(
                category=category,
                severity=IssueSeverity.INFO,
                title="Test",
                description="Test",
            )
            assert issue.category == category


class TestGoodPractice:
    """Tests for GoodPractice model."""

    def test_create_minimal_good_practice(self) -> None:
        """Test creating a good practice with minimal fields."""
        practice = GoodPractice(description="Good use of type hints")
        assert practice.description == "Good use of type hints"
        assert practice.file_path is None
        assert practice.line_number is None

    def test_create_full_good_practice(self) -> None:
        """Test creating a good practice with all fields."""
        practice = GoodPractice(
            description="Excellent error handling",
            file_path="src/api.py",
            line_number=100,
        )
        assert practice.file_path == "src/api.py"
        assert practice.line_number == 100

    def test_good_practice_description_required(self) -> None:
        """Test that description is required."""
        with pytest.raises(ValidationError):
            GoodPractice()  # type: ignore[call-arg]

    def test_good_practice_description_not_empty(self) -> None:
        """Test that description cannot be empty."""
        with pytest.raises(ValidationError):
            GoodPractice(description="")


class TestReviewResult:
    """Tests for ReviewResult model."""

    @pytest.fixture
    def critical_issue(self) -> CodeIssue:
        """Create a critical issue."""
        return CodeIssue(
            category=IssueCategory.SECURITY,
            severity=IssueSeverity.CRITICAL,
            title="Critical issue",
            description="Critical description",
        )

    @pytest.fixture
    def warning_issue(self) -> CodeIssue:
        """Create a warning issue."""
        return CodeIssue(
            category=IssueCategory.CODE_QUALITY,
            severity=IssueSeverity.WARNING,
            title="Warning issue",
            description="Warning description",
        )

    @pytest.fixture
    def info_issue(self) -> CodeIssue:
        """Create an info issue."""
        return CodeIssue(
            category=IssueCategory.PERFORMANCE,
            severity=IssueSeverity.INFO,
            title="Info issue",
            description="Info description",
        )

    @pytest.fixture
    def good_practice(self) -> GoodPractice:
        """Create a good practice."""
        return GoodPractice(description="Good type hints")

    def test_create_empty_result(self) -> None:
        """Test creating an empty review result."""
        result = ReviewResult()
        assert result.issues == ()
        assert result.good_practices == ()
        assert result.task_alignment == TaskAlignmentStatus.INSUFFICIENT_DATA
        assert result.summary == ""
        assert result.has_critical_issues is False
        assert result.has_security_issues is False
        assert result.issue_count == 0
        assert result.good_practice_count == 0
        assert result.matches_task is None

    def test_create_full_result(
        self, critical_issue: CodeIssue, good_practice: GoodPractice
    ) -> None:
        """Test creating a full review result."""
        now = datetime.now(tz=UTC)
        result = ReviewResult(
            issues=(critical_issue,),
            good_practices=(good_practice,),
            task_alignment=TaskAlignmentStatus.ALIGNED,
            task_alignment_reasoning="Changes match task requirements",
            summary="Found 1 critical issue",
            reviewed_at=now,
        )
        assert len(result.issues) == 1
        assert len(result.good_practices) == 1
        assert result.task_alignment == TaskAlignmentStatus.ALIGNED
        assert result.reviewed_at == now

    def test_has_critical_issues(self, critical_issue: CodeIssue, info_issue: CodeIssue) -> None:
        """Test has_critical_issues property."""
        result_with_critical = ReviewResult(issues=(critical_issue,))
        assert result_with_critical.has_critical_issues is True

        result_without_critical = ReviewResult(issues=(info_issue,))
        assert result_without_critical.has_critical_issues is False

    def test_has_security_issues(self, critical_issue: CodeIssue, warning_issue: CodeIssue) -> None:
        """Test has_security_issues property."""
        # critical_issue has SECURITY category
        result_with_security = ReviewResult(issues=(critical_issue,))
        assert result_with_security.has_security_issues is True

        # warning_issue has CODE_QUALITY category
        result_without_security = ReviewResult(issues=(warning_issue,))
        assert result_without_security.has_security_issues is False

    def test_issue_counts(
        self,
        critical_issue: CodeIssue,
        warning_issue: CodeIssue,
        info_issue: CodeIssue,
    ) -> None:
        """Test issue count properties."""
        result = ReviewResult(issues=(critical_issue, warning_issue, info_issue))
        assert result.critical_count == 1
        assert result.warning_count == 1
        assert result.info_count == 1
        assert result.issue_count == 3

    def test_good_practice_count(self, good_practice: GoodPractice) -> None:
        """Test good_practice_count property."""
        result = ReviewResult(good_practices=(good_practice, good_practice))
        assert result.good_practice_count == 2

    def test_matches_task_aligned(self) -> None:
        """Test matches_task property when aligned."""
        result = ReviewResult(task_alignment=TaskAlignmentStatus.ALIGNED)
        assert result.matches_task is True

    def test_matches_task_misaligned(self) -> None:
        """Test matches_task property when misaligned."""
        result = ReviewResult(task_alignment=TaskAlignmentStatus.MISALIGNED)
        assert result.matches_task is False

    def test_matches_task_insufficient_data(self) -> None:
        """Test matches_task property when insufficient data."""
        result = ReviewResult(task_alignment=TaskAlignmentStatus.INSUFFICIENT_DATA)
        assert result.matches_task is None

    def test_result_is_frozen(self) -> None:
        """Test that result model is immutable."""
        result = ReviewResult()
        with pytest.raises(ValidationError):
            result.summary = "Modified"  # type: ignore[misc]

    def test_result_reviewed_at_must_be_timezone_aware(self) -> None:
        """Test that reviewed_at rejects naive datetime."""
        naive_dt = datetime(2026, 1, 20, 12, 0, 0)
        with pytest.raises(ValidationError) as exc_info:
            ReviewResult(reviewed_at=naive_dt)
        assert "timezone-aware" in str(exc_info.value)


class TestEnums:
    """Tests for enum classes."""

    def test_comment_author_type_values(self) -> None:
        """Test CommentAuthorType enum values."""
        assert CommentAuthorType.USER.value == "user"
        assert CommentAuthorType.BOT.value == "bot"

    def test_comment_type_values(self) -> None:
        """Test CommentType enum values."""
        assert CommentType.ISSUE.value == "issue"
        assert CommentType.REVIEW.value == "review"

    def test_file_change_type_values(self) -> None:
        """Test FileChangeType enum values."""
        assert FileChangeType.ADDED.value == "added"
        assert FileChangeType.MODIFIED.value == "modified"
        assert FileChangeType.DELETED.value == "deleted"
        assert FileChangeType.RENAMED.value == "renamed"

    def test_issue_severity_values(self) -> None:
        """Test IssueSeverity enum values."""
        assert IssueSeverity.CRITICAL.value == "critical"
        assert IssueSeverity.WARNING.value == "warning"
        assert IssueSeverity.INFO.value == "info"

    def test_issue_category_values(self) -> None:
        """Test IssueCategory enum values."""
        assert IssueCategory.SECURITY.value == "security"
        assert IssueCategory.CODE_QUALITY.value == "code_quality"
        assert IssueCategory.ARCHITECTURE.value == "architecture"
        assert IssueCategory.PERFORMANCE.value == "performance"
        assert IssueCategory.TESTING.value == "testing"

    def test_task_alignment_status_values(self) -> None:
        """Test TaskAlignmentStatus enum values."""
        assert TaskAlignmentStatus.ALIGNED.value == "aligned"
        assert TaskAlignmentStatus.MISALIGNED.value == "misaligned"
        assert TaskAlignmentStatus.INSUFFICIENT_DATA.value == "insufficient_data"


class TestReviewMetrics:
    """Tests for ReviewMetrics model."""

    def test_create_minimal_metrics(self) -> None:
        """Test creating metrics with minimal fields."""
        metrics = ReviewMetrics(model_name="gemini-2.5-flash")
        assert metrics.model_name == "gemini-2.5-flash"
        assert metrics.prompt_tokens == 0
        assert metrics.completion_tokens == 0
        assert metrics.total_tokens == 0
        assert metrics.api_latency_ms == 0
        assert metrics.estimated_cost_usd == 0.0

    def test_create_full_metrics(self) -> None:
        """Test creating metrics with all fields."""
        metrics = ReviewMetrics(
            model_name="gemini-1.5-pro",
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500,
            api_latency_ms=2500,
            estimated_cost_usd=0.0037,
        )
        assert metrics.model_name == "gemini-1.5-pro"
        assert metrics.prompt_tokens == 1000
        assert metrics.completion_tokens == 500
        assert metrics.total_tokens == 1500
        assert metrics.api_latency_ms == 2500
        assert metrics.estimated_cost_usd == 0.0037

    def test_cost_formatted_small_cost(self) -> None:
        """Test cost_formatted for small costs (< $0.01)."""
        metrics = ReviewMetrics(
            model_name="gemini-2.5-flash",
            estimated_cost_usd=0.0003,
        )
        assert metrics.cost_formatted == "$0.0003"

    def test_cost_formatted_larger_cost(self) -> None:
        """Test cost_formatted for larger costs (>= $0.01)."""
        metrics = ReviewMetrics(
            model_name="gemini-1.5-pro",
            estimated_cost_usd=0.05,
        )
        assert metrics.cost_formatted == "$0.05"

    def test_latency_formatted_milliseconds(self) -> None:
        """Test latency_formatted for sub-second latency."""
        metrics = ReviewMetrics(
            model_name="gemini-2.5-flash",
            api_latency_ms=750,
        )
        assert metrics.latency_formatted == "750ms"

    def test_latency_formatted_seconds(self) -> None:
        """Test latency_formatted for multi-second latency."""
        metrics = ReviewMetrics(
            model_name="gemini-2.5-flash",
            api_latency_ms=2500,
        )
        assert metrics.latency_formatted == "2.5s"

    def test_metrics_is_frozen(self) -> None:
        """Test that metrics model is immutable."""
        metrics = ReviewMetrics(model_name="gemini-2.5-flash")
        with pytest.raises(ValidationError):
            metrics.model_name = "other-model"  # type: ignore[misc]

    def test_tokens_must_be_non_negative(self) -> None:
        """Test that token counts must be non-negative."""
        with pytest.raises(ValidationError):
            ReviewMetrics(model_name="gemini-2.5-flash", prompt_tokens=-1)

        with pytest.raises(ValidationError):
            ReviewMetrics(model_name="gemini-2.5-flash", completion_tokens=-1)

        with pytest.raises(ValidationError):
            ReviewMetrics(model_name="gemini-2.5-flash", total_tokens=-1)

    def test_latency_must_be_non_negative(self) -> None:
        """Test that latency must be non-negative."""
        with pytest.raises(ValidationError):
            ReviewMetrics(model_name="gemini-2.5-flash", api_latency_ms=-1)

    def test_cost_must_be_non_negative(self) -> None:
        """Test that cost must be non-negative."""
        with pytest.raises(ValidationError):
            ReviewMetrics(model_name="gemini-2.5-flash", estimated_cost_usd=-0.01)

    def test_model_name_required(self) -> None:
        """Test that model_name is required."""
        with pytest.raises(ValidationError):
            ReviewMetrics()  # type: ignore[call-arg]

    def test_model_name_not_empty(self) -> None:
        """Test that model_name cannot be empty."""
        with pytest.raises(ValidationError):
            ReviewMetrics(model_name="")


class TestReviewResultWithMetrics:
    """Tests for ReviewResult with metrics."""

    def test_result_with_metrics(self) -> None:
        """Test creating result with metrics."""
        metrics = ReviewMetrics(
            model_name="gemini-2.5-flash",
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500,
            api_latency_ms=1500,
            estimated_cost_usd=0.0002,
        )
        result = ReviewResult(
            summary="LGTM",
            metrics=metrics,
        )
        assert result.metrics is not None
        assert result.metrics.model_name == "gemini-2.5-flash"
        assert result.metrics.total_tokens == 1500

    def test_result_without_metrics(self) -> None:
        """Test that metrics is optional."""
        result = ReviewResult(summary="LGTM")
        assert result.metrics is None
